"""
Verification Tool for Agent-based RAG

Provides fact-checking and verification capabilities:
- Cross-reference claims across multiple documents
- Verify consistency of numerical data
- Check for contradictions
- Assess claim confidence based on supporting evidence
"""

import os
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from langfuse.openai import OpenAI
from langfuse import observe

# Initialize OpenAI client
openai = OpenAI()
MODEL = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")


@dataclass
class VerificationResult:
    """Result from a verification operation."""
    
    claim: str
    is_verified: bool
    confidence: float = 0.0
    supporting_evidence: List[str] = field(default_factory=list)
    contradicting_evidence: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    explanation: str = ""
    verification_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "claim": self.claim,
            "is_verified": self.is_verified,
            "confidence": self.confidence,
            "supporting_evidence": self.supporting_evidence,
            "contradicting_evidence": self.contradicting_evidence,
            "sources": self.sources,
            "explanation": self.explanation,
            "verification_metadata": self.verification_metadata,
        }


class VerifyTool:
    """Fact verification and cross-reference tool."""
    
    def __init__(self, model: str = None):
        """Initialize verification tool.
        
        Args:
            model: OpenAI model to use for verification
        """
        self.model = model or MODEL
        self.openai = openai
    
    @observe(name="agent_verify", as_type="tool")
    def verify(
        self,
        claim: str,
        context_chunks: List[Dict[str, Any]],
        strict_mode: bool = False,
    ) -> VerificationResult:
        """Verify a claim against provided context.
        
        Args:
            claim: The claim or statement to verify
            context_chunks: Relevant document chunks for verification
            strict_mode: If True, requires strong evidence to verify
            
        Returns:
            VerificationResult with verification status and evidence
        """
        if not context_chunks:
            return VerificationResult(
                claim=claim,
                is_verified=False,
                confidence=0.0,
                explanation="No context provided for verification.",
                verification_metadata={"error": "No context chunks"}
            )
        
        try:
            # Build context from chunks
            context_text = self._build_context(context_chunks)
            
            # Build verification prompt
            system_prompt = self._get_system_prompt(strict_mode)
            user_prompt = self._build_user_prompt(claim, context_text)
            
            # Call LLM for verification
            response = self.openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            
            verification_text = response.choices[0].message.content
            
            # Parse verification result
            is_verified, confidence, supporting, contradicting, explanation = \
                self._parse_verification(verification_text, strict_mode)
            
            # Track sources
            sources = list(set(
                chunk.get("metadata", {}).get("source", "unknown")
                for chunk in context_chunks
            ))
            
            return VerificationResult(
                claim=claim,
                is_verified=is_verified,
                confidence=confidence,
                supporting_evidence=supporting,
                contradicting_evidence=contradicting,
                sources=sources,
                explanation=explanation,
                verification_metadata={
                    "strict_mode": strict_mode,
                    "num_chunks_checked": len(context_chunks),
                    "model": self.model,
                }
            )
            
        except Exception as e:
            print(f"Error in verification: {e}")
            import traceback
            traceback.print_exc()
            
            return VerificationResult(
                claim=claim,
                is_verified=False,
                confidence=0.0,
                explanation=f"Error during verification: {str(e)}",
                verification_metadata={"error": str(e)}
            )
    
    def verify_multiple(
        self,
        claims: List[str],
        context_chunks: List[Dict[str, Any]],
        strict_mode: bool = False,
    ) -> List[VerificationResult]:
        """Verify multiple claims against context.
        
        Args:
            claims: List of claims to verify
            context_chunks: Relevant document chunks for verification
            strict_mode: If True, requires strong evidence to verify
            
        Returns:
            List of VerificationResult for each claim
        """
        results = []
        for claim in claims:
            result = self.verify(claim, context_chunks, strict_mode)
            results.append(result)
        return results
    
    def _build_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Build context string from chunks."""
        context_parts = []
        
        for i, chunk in enumerate(chunks[:10], 1):  # Limit to top 10 chunks
            content = chunk.get("page_content", "")
            metadata = chunk.get("metadata", {})
            source = metadata.get("source", "unknown")
            page = metadata.get("page_index", "unknown")
            
            context_parts.append(
                f"[Evidence {i} - Source: {source}, Page: {page}]\n{content}\n"
            )
        
        return "\n".join(context_parts)
    
    def _get_system_prompt(self, strict_mode: bool) -> str:
        """Get system prompt based on verification mode."""
        base_prompt = """You are an expert fact-checker specializing in financial data verification.
Your role is to carefully verify claims against provided evidence."""
        
        if strict_mode:
            mode_specific = """
**STRICT VERIFICATION MODE**

Only verify a claim as TRUE if:
1. Direct, explicit evidence supports it
2. Numbers and figures match exactly
3. No contradicting evidence exists
4. The evidence is clear and unambiguous

If there is ANY doubt or the evidence is indirect, mark as UNVERIFIED.
"""
        else:
            mode_specific = """
**STANDARD VERIFICATION MODE**

Verify a claim as TRUE if:
1. Evidence supports the claim (direct or reasonably inferred)
2. Numbers are consistent (allowing for rounding)
3. No significant contradictions exist
4. The preponderance of evidence supports the claim

Mark as UNVERIFIED if evidence is insufficient or contradictory.
"""
        
        return base_prompt + mode_specific
    
    def _build_user_prompt(self, claim: str, context: str) -> str:
        """Build user prompt for verification."""
        return f"""Please verify the following claim against the provided evidence:

**CLAIM TO VERIFY:**
{claim}

**EVIDENCE:**
{context}

**INSTRUCTIONS:**
1. Carefully review all evidence
2. Identify supporting evidence (quote relevant excerpts)
3. Identify any contradicting evidence (quote relevant excerpts)
4. Determine if the claim is VERIFIED or UNVERIFIED
5. Provide your confidence level (0.0 to 1.0)
6. Explain your reasoning

**FORMAT YOUR RESPONSE AS:**
VERIFICATION: [VERIFIED or UNVERIFIED]
CONFIDENCE: [0.0-1.0]
SUPPORTING EVIDENCE:
- [Quote or paraphrase evidence that supports the claim]
- [Additional supporting evidence]

CONTRADICTING EVIDENCE:
- [Quote or paraphrase evidence that contradicts the claim]
- [Additional contradicting evidence, if any]

EXPLANATION:
[Your detailed reasoning for the verification decision]
"""
    
    def _parse_verification(
        self,
        verification_text: str,
        strict_mode: bool
    ) -> tuple[bool, float, List[str], List[str], str]:
        """Parse LLM verification response."""
        is_verified = False
        confidence = 0.5
        supporting = []
        contradicting = []
        explanation = ""
        
        lines = verification_text.split("\n")
        current_section = None
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Parse verification status
            if line_lower.startswith("verification:"):
                is_verified = "verified" in line_lower and "unverified" not in line_lower
            
            # Parse confidence
            elif line_lower.startswith("confidence:"):
                try:
                    conf_str = line.split(":", 1)[1].strip()
                    confidence = float(conf_str)
                except:
                    confidence = 0.7 if is_verified else 0.3
            
            # Track sections
            elif line_lower.startswith("supporting evidence:"):
                current_section = "supporting"
            elif line_lower.startswith("contradicting evidence:"):
                current_section = "contradicting"
            elif line_lower.startswith("explanation:"):
                current_section = "explanation"
            
            # Parse evidence
            elif line.strip().startswith(("-", "•", "*")):
                evidence = line.strip().lstrip("-•* ")
                if current_section == "supporting" and evidence:
                    supporting.append(evidence)
                elif current_section == "contradicting" and evidence:
                    contradicting.append(evidence)
            
            # Parse explanation
            elif current_section == "explanation" and line.strip():
                explanation += line + "\n"
        
        # Adjust confidence in strict mode
        if strict_mode and is_verified:
            confidence = min(confidence, 0.9)  # Cap at 0.9 in strict mode
        
        # If contradicting evidence exists, reduce confidence
        if contradicting:
            confidence = max(0.3, confidence - 0.2)
        
        return is_verified, confidence, supporting, contradicting, explanation.strip()


# Global instance
_verify_tool = None


def get_verify_tool() -> VerifyTool:
    """Get singleton verification tool instance."""
    global _verify_tool
    if _verify_tool is None:
        _verify_tool = VerifyTool()
    return _verify_tool


@observe(name="agent_verify_function", as_type="tool")
def verify(
    claim: str,
    context_chunks: List[Dict[str, Any]],
    strict_mode: bool = False,
) -> VerificationResult:
    """Convenience function for claim verification.
    
    Args:
        claim: The claim or statement to verify
        context_chunks: Relevant document chunks for verification
        strict_mode: If True, requires strong evidence to verify
        
    Returns:
        VerificationResult with verification status and evidence
        
    Example:
        from agent_tools import search, verify
        search_result = search("revenue 2024")
        verification_result = verify(
            "Revenue increased by 10% in 2024",
            search_result.chunks
        )
        print(f"Verified: {verification_result.is_verified}")
        print(f"Confidence: {verification_result.confidence:.2f}")
    """
    tool = get_verify_tool()
    return tool.verify(claim, context_chunks, strict_mode)
