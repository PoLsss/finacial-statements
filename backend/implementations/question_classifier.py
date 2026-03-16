"""
Phase 1: Hybrid RAG - Question Classifier (LLM-Based)

This module implements LLM-based question classification
that categorizes financial questions into complexity levels for intelligent routing.

The classifier helps route questions to the appropriate RAG strategy:
- Simple questions (complexity < 0.4): Direct retrieval + simple LLM answer
- Complex questions (complexity >= 0.4): Multi-retrieval + reranking + analysis

Uses Claude/GPT with proper prompting for accurate complexity assessment.

Author: Financial Reports RAG System
Version: 1.0.0
"""

import os
import json
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Optional
import logging
from dotenv import load_dotenv

load_dotenv(override=True)

from langfuse import observe

try:
    from langfuse.openai import OpenAI
except ImportError:
    from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ComplexityLevel(str, Enum):
    """Enum for question complexity levels."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


@dataclass
class ClassificationResult:
    """Result of question classification."""
    question: str
    complexity_level: ComplexityLevel
    complexity_score: float  # 0.0 to 1.0
    reasoning: str
    features: Dict[str, any]
    should_use_reranking: bool
    recommended_k: int
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "complexity_level": self.complexity_level.value,
            "complexity_score": round(self.complexity_score, 3),
            "reasoning": self.reasoning,
            "features": self.features,
            "should_use_reranking": self.should_use_reranking,
            "recommended_k": self.recommended_k,
        }


class QuestionClassifier:
    """
    LLM-based question classifier using Claude/GPT for intelligent analysis.
    
    This classifier uses an LLM to analyze questions with proper prompting,
    providing accurate complexity assessment. Includes caching to minimize API calls.
    
    Attributes:
        client: OpenAI/Claude client (with optional Langfuse integration)
        model: LLM model to use (default: gpt-4o-mini)
        cache: Classification cache to avoid redundant API calls
    """
    
    def __init__(
        self,
        model: str = "gpt-4o-mini",
        min_score_for_complex: float = 0.4,
        enable_cache: bool = True,
    ):
        """
        Initialize the LLM classifier.
        
        Args:
            model: LLM model name to use
            min_score_for_complex: Score threshold for complex classification
            enable_cache: Whether to cache results
        """
        self.model = model
        self.min_score_for_complex = min_score_for_complex
        self.enable_cache = enable_cache
        self.cache: Dict[str, ClassificationResult] = {}
        
        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        # Use Langfuse-wrapped OpenAI if available
        try:
            self.client = OpenAI(api_key=api_key)
        except:
            from openai import OpenAI as StandardOpenAI
            self.client = StandardOpenAI(api_key=api_key)
        
        logger.info(f"QuestionClassifier (LLM) initialized with model: {model}")
    
    @observe(name="classify_question", as_type="span")
    def classify(self, question: str, context: Optional[str] = None) -> ClassificationResult:
        """
        Classify a question using LLM analysis.
        
        Args:
            question: The question to classify
            context: Optional conversation context for better classification
            
        Returns:
            ClassificationResult with LLM-based analysis
            
        Raises:
            ValueError: If question is empty
        """
        # Validate input
        if not question or not isinstance(question, str):
            raise ValueError("Question must be a non-empty string")
        
        question = question.strip()
        if len(question) == 0:
            raise ValueError("Question cannot be empty")
        
        # Check cache
        cache_key = f"{question}:{context or ''}"
        if self.enable_cache and cache_key in self.cache:
            logger.debug(f"Cache hit for question: {question[:50]}...")
            return self.cache[cache_key]
        
        # Call LLM for classification
        result = self._classify_with_llm(question, context)
        
        # Cache result
        if self.enable_cache:
            self.cache[cache_key] = result
        
        logger.debug(f"Question classified: {result.complexity_level} (score={result.complexity_score:.3f})")
        return result
    
    def _classify_with_llm(self, question: str, context: Optional[str] = None) -> ClassificationResult:
        """
        Call LLM to classify the question.
        
        Args:
            question: Question to classify
            context: Optional conversation context
            
        Returns:
            ClassificationResult
        """
        # Build prompt
        system_prompt = """You are a financial question classifier. Your task is to analyze questions about financial reports and classify their complexity.

            For each question, you must:
            1. Analyze the question to determine its complexity level (simple, moderate, or complex)
            2. Calculate a complexity score from 0.0 to 1.0
            3. Identify if it requires reranking for better relevance
            4. Suggest optimal retrieval K value
            5. Provide clear reasoning

            Consider these factors:
            - Simple questions: Direct factual retrieval (What is X?, How much is Y?, List Z)
            - Moderate questions: Require some analysis (Analyze X trend, Show comparison)
            - Complex questions: Multi-step analysis, correlations, forecasting, explanations (Why did X change?, Explain the relationship between X and Y, What would happen if...)

            Note: Query rewriting is automatically applied when conversation history exists.

            Output MUST be valid JSON with this exact structure:
            {
                "complexity_level": "simple|moderate|complex",
                "complexity_score": 0.0-1.0,
                "should_use_reranking": true/false,
                "recommended_k": 3-8,
                "reasoning": "brief explanation"
            }"""

        user_message = f"""Classify this financial question:\n\nQUESTION: {question}"""

        if context:
            user_message += f"\n\nCONVERSATION CONTEXT: {context}"
        
        user_message += "\n\nRespond ONLY with valid JSON, no other text."
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
            )
            
            # Parse LLM response
            response_text = response.choices[0].message.content.strip()
            
            # Try to extract JSON if wrapped in markdown
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            classification_data = json.loads(response_text)
            
            # Validate response
            required_fields = {
                "complexity_level", "complexity_score", 
                "should_use_reranking",
                "recommended_k", "reasoning"
            }
            
            if not all(field in classification_data for field in required_fields):
                logger.warning(f"LLM response missing fields: {classification_data}")
                raise ValueError("Incomplete LLM response")
            
            # Build result
            complexity_level = ComplexityLevel(classification_data["complexity_level"])
            complexity_score = float(classification_data["complexity_score"])
            
            # Ensure score is in valid range
            complexity_score = max(0.0, min(complexity_score, 1.0))
            
            result = ClassificationResult(
                question=question,
                complexity_level=complexity_level,
                complexity_score=complexity_score,
                reasoning=classification_data["reasoning"],
                features={
                    "llm_based": True,
                    "model": self.model,
                    "context_provided": context is not None,
                },
                should_use_reranking=bool(classification_data["should_use_reranking"]),
                recommended_k=int(classification_data["recommended_k"]),
            )
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            raise ValueError(f"LLM did not return valid JSON: {e}")
        except Exception as e:
            logger.error(f"LLM classification failed: {e}")
            raise


# Global classifier instance (lazy initialization)
_classifier: Optional[QuestionClassifier] = None


def get_classifier(model: str = "gpt-4o-mini") -> QuestionClassifier:
    """
    Get or create the global classifier instance.
    
    Args:
        model: LLM model to use
        
    Returns:
        QuestionClassifier instance
    """
    global _classifier
    if _classifier is None:
        _classifier = QuestionClassifier(model=model)
    return _classifier


def classify_question(
    question: str,
    context: Optional[str] = None,
    classifier: Optional[QuestionClassifier] = None,
) -> ClassificationResult:
    """
    Classify a question's complexity.
    
    Args:
        question: The question to classify
        context: Optional conversation context
        classifier: Optional pre-initialized classifier
        
    Returns:
        ClassificationResult
    """
    if classifier is None:
        classifier = get_classifier()
    
    return classifier.classify(question, context)


def should_use_advanced_rag(
    question: str,
    classifier: Optional[QuestionClassifier] = None,
    context: Optional[str] = None,
) -> bool:
    """
    Determine if advanced RAG features should be used for a question.
    
    Args:
        question: The question to evaluate
        classifier: Optional pre-initialized classifier
        context: Optional conversation context
        
    Returns:
        True if advanced RAG (reranking, query rewriting) should be used
    """
    if classifier is None:
        classifier = get_classifier()
    
    result = classifier.classify(question, context)
    return result.should_use_reranking


def get_rag_strategy(
    question: str,
    classifier: Optional[QuestionClassifier] = None,
    context: Optional[str] = None,
) -> Dict:
    """
    Get the recommended RAG strategy for a question.
    
    Args:
        question: The question to evaluate
        classifier: Optional pre-initialized classifier
        context: Optional conversation context
        
    Returns:
        Dictionary with strategy parameters
    """
    if classifier is None:
        classifier = get_classifier()
    
    result = classifier.classify(question, context)
    
    return {
        "complexity_level": result.complexity_level.value,
        "complexity_score": result.complexity_score,
        "use_reranking": result.should_use_reranking,
        "retrieval_k": result.recommended_k,
        "strategy": "advanced" if result.should_use_reranking else "simple",
        "reasoning": result.reasoning,
    }
