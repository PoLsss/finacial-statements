"""
Agent Tools for Complex Financial Question Answering

This package contains specialized tools for the agentic RAG system:
- search_tool: Advanced document search and retrieval
- analyze_tool: LLM-based multi-metric financial analysis
- verify_tool: Cross-reference and fact verification

These tools are designed to work together in a LangGraph-based agent
for handling complex financial queries that require multi-step reasoning.
"""

from .search_tool import search, SearchResult
from .analyze_tool import analyze, AnalysisResult
from .verify_tool import verify, VerificationResult

__all__ = [
    "search",
    "SearchResult",
    "analyze",
    "AnalysisResult",
    "verify",
    "VerificationResult",
]

__version__ = "2.0.0"
