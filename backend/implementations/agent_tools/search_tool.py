"""
Search Tool for Agent-based RAG

Uses MongoDB for semantic search across financial documents.
"""

import os
import sys
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
from langfuse import observe
from langfuse.openai import OpenAI
from dotenv import load_dotenv

load_dotenv(override=True)

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.implementations.mongodb_manager import get_mongodb_manager

# Configuration
embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")


@dataclass
class SearchResult:
    """Result from a search operation."""

    query: str
    chunks: List[Dict[str, Any]] = field(default_factory=list)
    num_results: int = 0
    sources: List[str] = field(default_factory=list)
    confidence: float = 0.0
    search_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "chunks": self.chunks,
            "num_results": self.num_results,
            "sources": self.sources,
            "confidence": self.confidence,
            "search_metadata": self.search_metadata,
        }


class SearchTool:
    """Advanced search tool for financial documents using MongoDB."""

    def __init__(self):
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        self.openai = OpenAI()

        try:
            self.mongo = get_mongodb_manager()
        except Exception as e:
            print(f"Warning: Could not connect to MongoDB in SearchTool: {e}")
            self.mongo = None

    @observe(name="agent_search", as_type="tool")
    def search(
        self,
        query: str,
        n_results: int = 8,
        source_filter: Optional[str] = None,
        min_confidence: float = 0.0,
    ) -> SearchResult:
        """Search for relevant financial documents using MongoDB embeddings."""
        if not self.mongo:
            return SearchResult(
                query=query,
                chunks=[],
                num_results=0,
                sources=[],
                confidence=0.0,
                search_metadata={"error": "MongoDB not initialized"}
            )

        try:
            query_embedding = self.openai.embeddings.create(
                model=self.embedding_model,
                input=[query]
            ).data[0].embedding

            results = self.mongo.query_by_embedding(
                query_embedding=query_embedding,
                n_results=n_results,
                source_filter=source_filter,
            )

            chunks = []
            sources = set()

            for doc in results:
                similarity = doc.get("similarity", 0.0)

                if similarity < min_confidence:
                    continue

                chunk = {
                    "page_content": doc["text"],
                    "metadata": doc.get("metadata", {}),
                    "confidence": similarity,
                    "similarity": similarity,
                }
                chunks.append(chunk)

                source = doc.get("source", doc.get("metadata", {}).get("source", ""))
                if source:
                    sources.add(source)

            avg_confidence = (
                sum(c["confidence"] for c in chunks) / len(chunks)
                if chunks else 0.0
            )

            return SearchResult(
                query=query,
                chunks=chunks,
                num_results=len(chunks),
                sources=list(sources),
                confidence=avg_confidence,
                search_metadata={
                    "n_results_requested": n_results,
                    "source_filter": source_filter,
                    "min_confidence": min_confidence,
                }
            )

        except Exception as e:
            print(f"Error in search: {e}")
            import traceback
            traceback.print_exc()

            return SearchResult(
                query=query,
                chunks=[],
                num_results=0,
                sources=[],
                confidence=0.0,
                search_metadata={"error": str(e)}
            )

    def multi_query_search(
        self,
        queries: List[str],
        n_results_per_query: int = 5,
        merge_strategy: str = "deduplicate",
    ) -> SearchResult:
        """Search with multiple queries and merge results."""
        all_chunks = []
        all_sources = set()

        for query in queries:
            result = self.search(query, n_results=n_results_per_query)
            all_chunks.extend(result.chunks)
            all_sources.update(result.sources)

        if merge_strategy == "deduplicate":
            seen_content = set()
            unique_chunks = []
            for chunk in all_chunks:
                content = chunk["page_content"]
                if content not in seen_content:
                    seen_content.add(content)
                    unique_chunks.append(chunk)
            all_chunks = unique_chunks

        all_chunks.sort(key=lambda x: x.get("confidence", 0.0), reverse=True)

        avg_confidence = (
            sum(c["confidence"] for c in all_chunks) / len(all_chunks)
            if all_chunks else 0.0
        )

        return SearchResult(
            query=" | ".join(queries),
            chunks=all_chunks,
            num_results=len(all_chunks),
            sources=list(all_sources),
            confidence=avg_confidence,
            search_metadata={
                "queries": queries,
                "merge_strategy": merge_strategy,
                "n_results_per_query": n_results_per_query,
            }
        )


# Global instance
_search_tool = None


def get_search_tool() -> SearchTool:
    """Get singleton search tool instance."""
    global _search_tool
    if _search_tool is None:
        _search_tool = SearchTool()
    return _search_tool


@observe(name="agent_search_function", as_type="tool")
def search(
    query: str,
    n_results: int = 8,
    source_filter: Optional[str] = None,
    min_confidence: float = 0.0,
) -> SearchResult:
    """Convenience function for searching financial documents."""
    tool = get_search_tool()
    return tool.search(query, n_results, source_filter, min_confidence)
