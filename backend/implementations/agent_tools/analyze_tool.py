"""
Analysis Tool for Agent-based RAG

Provides LLM-powered financial analysis capabilities:
- Multi-metric financial analysis (growth, margins, ratios)
- Trend identification and pattern recognition
- Comparative analysis across periods
- Impact analysis and causal reasoning
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
class AnalysisResult:
    """Result from an analysis operation."""
    
    query: str
    analysis: str
    metrics: Dict[str, Any] = field(default_factory=dict)
    insights: List[str] = field(default_factory=list)
    confidence: float = 0.0
    sources_used: List[str] = field(default_factory=list)
    analysis_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "query": self.query,
            "analysis": self.analysis,
            "metrics": self.metrics,
            "insights": self.insights,
            "confidence": self.confidence,
            "sources_used": self.sources_used,
            "analysis_metadata": self.analysis_metadata,
        }


class AnalyzeTool:
    """LLM-based financial analysis tool."""
    
    def __init__(self, model: str = None):
        """Initialize analysis tool.
        
        Args:
            model: OpenAI model to use for analysis
        """
        self.model = model or MODEL
        self.openai = openai
    
    @observe(name="agent_analyze", as_type="tool")
    def analyze(
        self,
        question: str,
        context_chunks: List[Dict[str, Any]],
        analysis_type: str = "general",
    ) -> AnalysisResult:
        """Analyze financial data using LLM.
        
        Args:
            question: Analysis question or task
            context_chunks: Relevant document chunks for analysis
            analysis_type: Type of analysis ("general", "trend", "comparative", "impact")
            
        Returns:
            AnalysisResult with analysis, metrics, and insights
        """
        if not context_chunks:
            return AnalysisResult(
                query=question,
                analysis="No context provided for analysis.",
                confidence=0.0,
                analysis_metadata={"error": "No context chunks"}
            )
        
        try:
            # Build context from chunks
            context_text = self._build_context(context_chunks)
            
            # Build analysis prompt based on type
            system_prompt = self._get_system_prompt(analysis_type)
            user_prompt = self._build_user_prompt(question, context_text, analysis_type)
            
            # Call LLM for analysis
            response = self.openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            
            analysis_text = response.choices[0].message.content
            
            # Extract metrics and insights from analysis
            metrics, insights = self._extract_metrics_and_insights(analysis_text, context_chunks)
            
            # Calculate confidence based on context quality
            confidence = self._calculate_confidence(context_chunks)
            
            # Track sources
            sources = list(set(
                chunk.get("metadata", {}).get("source", "unknown")
                for chunk in context_chunks
            ))
            
            return AnalysisResult(
                query=question,
                analysis=analysis_text,
                metrics=metrics,
                insights=insights,
                confidence=confidence,
                sources_used=sources,
                analysis_metadata={
                    "analysis_type": analysis_type,
                    "num_chunks_used": len(context_chunks),
                    "model": self.model,
                }
            )
            
        except Exception as e:
            print(f"Error in analysis: {e}")
            import traceback
            traceback.print_exc()
            
            return AnalysisResult(
                query=question,
                analysis=f"Error during analysis: {str(e)}",
                confidence=0.0,
                analysis_metadata={"error": str(e)}
            )
    
    def _build_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Build context string from chunks."""
        context_parts = []
        
        for i, chunk in enumerate(chunks[:10], 1):  # Limit to top 10 chunks
            content = chunk.get("page_content", "")
            metadata = chunk.get("metadata", {})
            source = metadata.get("source", "unknown")
            page = metadata.get("page_index", "unknown")
            
            context_parts.append(
                f"[Chunk {i} - Source: {source}, Page: {page}]\n{content}\n"
            )
        
        return "\n".join(context_parts)
    
    def _get_system_prompt(self, analysis_type: str) -> str:
        """Get system prompt based on analysis type."""
        base_prompt = """You are an expert financial analyst specializing in analyzing financial reports and data.
Your role is to provide thorough, accurate financial analysis based on the provided context."""
        
        type_specific = {
            "general": """
Provide a comprehensive analysis that covers:
1. Key findings and observations
2. Important metrics and their significance
3. Notable trends or patterns
4. Potential implications
""",
            "trend": """
Focus on identifying and analyzing trends:
1. Direction of key metrics (increasing, decreasing, stable)
2. Rate of change and acceleration
3. Patterns across time periods
4. Potential causes of trends
5. Future trajectory implications
""",
            "comparative": """
Focus on comparative analysis:
1. Compare metrics across different periods
2. Calculate percentage changes and growth rates
3. Identify significant differences
4. Explain reasons for variations
5. Benchmark against expectations
""",
            "impact": """
Focus on impact and causal analysis:
1. Identify causal relationships
2. Quantify impact where possible
3. Distinguish correlation from causation
4. Assess materiality of impacts
5. Consider multiple contributing factors
"""
        }
        
        return base_prompt + type_specific.get(analysis_type, type_specific["general"])
    
    def _build_user_prompt(self, question: str, context: str, analysis_type: str) -> str:
        """Build user prompt for analysis."""
        return f"""Based on the following financial data, please analyze:

**Question:** {question}

**Context:**
{context}

**Analysis Type:** {analysis_type}

Please provide:
1. A clear, structured analysis
2. Specific metrics and figures from the context
3. Key insights and findings
4. Support all claims with evidence from the context
5. If calculating changes, always show the calculation

Be thorough but concise. Use bullet points for clarity where appropriate.
"""
    
    def _extract_metrics_and_insights(
        self,
        analysis_text: str,
        context_chunks: List[Dict[str, Any]]
    ) -> tuple[Dict[str, Any], List[str]]:
        """Extract structured metrics and insights from analysis text."""
        metrics = {}
        insights = []
        
        # Simple extraction - look for common patterns
        lines = analysis_text.split("\n")
        
        for line in lines:
            # Extract insights (lines starting with bullet points or numbers)
            if line.strip().startswith(("•", "-", "*", "1.", "2.", "3.")):
                insight = line.strip().lstrip("•-*123456789. ")
                if len(insight) > 20:  # Meaningful insights
                    insights.append(insight)
        
        # Extract metrics from chunks (e.g., revenue, profit, etc.)
        for chunk in context_chunks[:5]:
            content = chunk.get("page_content", "")
            # Simple metric extraction - could be enhanced
            if "revenue" in content.lower() and "$" in content:
                metrics["revenue_mentioned"] = True
            if "profit" in content.lower():
                metrics["profit_mentioned"] = True
        
        return metrics, insights[:5]  # Limit to top 5 insights
    
    def _calculate_confidence(self, chunks: List[Dict[str, Any]]) -> float:
        """Calculate confidence based on context quality."""
        if not chunks:
            return 0.0
        
        # Base confidence on number and quality of chunks
        num_chunks = len(chunks)
        avg_confidence = sum(
            chunk.get("confidence", 0.5) for chunk in chunks
        ) / num_chunks
        
        # Confidence increases with more chunks up to a point
        quantity_factor = min(1.0, num_chunks / 8.0)
        
        # Combine factors
        confidence = (avg_confidence * 0.7) + (quantity_factor * 0.3)
        
        return round(confidence, 2)


# Global instance
_analyze_tool = None


def get_analyze_tool() -> AnalyzeTool:
    """Get singleton analysis tool instance."""
    global _analyze_tool
    if _analyze_tool is None:
        _analyze_tool = AnalyzeTool()
    return _analyze_tool


@observe(name="agent_analyze_function", as_type="tool")
def analyze(
    question: str,
    context_chunks: List[Dict[str, Any]],
    analysis_type: str = "general",
) -> AnalysisResult:
    """Convenience function for financial analysis.
    
    Args:
        question: Analysis question or task
        context_chunks: Relevant document chunks for analysis
        analysis_type: Type of analysis ("general", "trend", "comparative", "impact")
        
    Returns:
        AnalysisResult with analysis, metrics, and insights
        
    Example:
        >>> from agent_tools import search, analyze
        >>> search_result = search("revenue trends")
        >>> analysis_result = analyze(
        ...     "Analyze revenue trends",
        ...     search_result.chunks,
        ...     analysis_type="trend"
        ... )
        >>> print(analysis_result.analysis)
    """
    tool = get_analyze_tool()
    return tool.analyze(question, context_chunks, analysis_type)
