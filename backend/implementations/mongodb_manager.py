"""
MongoDB Manager Module

Replaces ChromaDB with MongoDB for storing chunks, embeddings, and financial data.
Uses MongoDB Atlas with vector search capabilities.
"""

import os
import certifi
from typing import List, Dict, Optional, Any
from pymongo import MongoClient
from pymongo.collection import Collection
from dotenv import load_dotenv

load_dotenv()


class MongoDBManager:
    """Manages MongoDB connections and operations for the financial reports pipeline."""

    def __init__(
        self,
        mongo_url: Optional[str] = None,
        database_name: Optional[str] = None,
    ):
        self.mongo_url = mongo_url or os.getenv("MONGO_URL")
        self.database_name = database_name or os.getenv("MONGO_DATABASE", "financialReport")

        if not self.mongo_url:
            raise ValueError(
                "MongoDB URL not provided. Set MONGO_URL environment variable "
                "or pass mongo_url parameter."
            )

        self.client = MongoClient(self.mongo_url, tlsCAFile=certifi.where())
        self.db = self.client[self.database_name]

        # Verify connection
        self.client.admin.command("ping")
        print(f"Connected to MongoDB Atlas - Database: {self.database_name}")

        # Collection names from env
        self.chunks_collection_name = os.getenv("MONGODB_COLLECTION_CHUNKS", "chunks")
        self.embeddings_collection_name = os.getenv("MONGODB_COLLECTION_EMBEDDINGS", "embeddings")
        self.variables_collection_name = os.getenv("MONGODB_COLLECTION_STATISTICS", "variables")

    @property
    def chunks_collection(self) -> Collection:
        return self.db[self.chunks_collection_name]

    @property
    def embeddings_collection(self) -> Collection:
        return self.db[self.embeddings_collection_name]

    @property
    def variables_collection(self) -> Collection:
        return self.db[self.variables_collection_name]

    # --- Chunks operations ---

    def store_chunks(self, chunks: List[Dict], source_name: str, reset: bool = False) -> int:
        """
        Store document chunks in MongoDB.

        Args:
            chunks: List of chunk dicts with 'text' and 'metadata'
            source_name: Name of the source document
            reset: If True, delete existing chunks for this source first

        Returns:
            Number of chunks stored
        """
        if reset:
            result = self.chunks_collection.delete_many({"metadata.source": source_name})
            print(f"Deleted {result.deleted_count} existing chunks for {source_name}")

        documents = []
        for chunk in chunks:
            doc = {
                "chunk_id": chunk["metadata"].get("chunk_id", ""),
                "source": source_name,
                "page_number": chunk["metadata"].get("page_number", 0),
                "text": chunk["text"],
                "metadata": chunk["metadata"],
            }
            documents.append(doc)

        if documents:
            self.chunks_collection.insert_many(documents)
            print(f"Stored {len(documents)} chunks for {source_name}")

        return len(documents)

    def get_chunks_by_source(self, source_name: str) -> List[Dict]:
        """Get all chunks for a given source document."""
        return list(self.chunks_collection.find(
            {"source": source_name},
            {"_id": 0}
        ))

    def get_all_chunks_count(self) -> int:
        """Get total number of chunks."""
        return self.chunks_collection.count_documents({})

    # --- Embeddings operations ---

    def store_embeddings(
        self,
        embeddings_data: List[Dict],
        source_name: str,
        reset: bool = False
    ) -> int:
        """
        Store embeddings in MongoDB.

        Args:
            embeddings_data: List of dicts with 'chunk_id', 'page_number', 'embedding', 'text', 'metadata'
            source_name: Name of the source document
            reset: If True, delete existing embeddings for this source first

        Returns:
            Number of embeddings stored
        """
        if reset:
            result = self.embeddings_collection.delete_many({"metadata.source": source_name})
            print(f"Deleted {result.deleted_count} existing embeddings for {source_name}")

        documents = []
        for item in embeddings_data:
            doc = {
                "chunk_id": item["chunk_id"],
                "page_number": item["page_number"],
                "embedding": item["embedding"],
                "text": item["text"],
                "source": source_name,
                "metadata": item.get("metadata", {}),
            }
            documents.append(doc)

        if documents:
            self.embeddings_collection.insert_many(documents)
            print(f"Stored {len(documents)} embeddings for {source_name}")

        return len(documents)

    def get_all_embeddings(self, source_name: Optional[str] = None) -> List[Dict]:
        """Get all embeddings, optionally filtered by source."""
        query = {}
        if source_name:
            query["source"] = source_name
        return list(self.embeddings_collection.find(query, {"_id": 0}))

    def get_all_embeddings_count(self) -> int:
        """Get total number of embeddings."""
        return self.embeddings_collection.count_documents({})

    def query_by_embedding(
        self,
        query_embedding: List[float],
        n_results: int = 10,
        source_filter: Optional[str] = None,
    ) -> List[Dict]:
        """
        Find the most similar embeddings using cosine similarity computed in Python.

        Args:
            query_embedding: The query embedding vector
            n_results: Number of results to return
            source_filter: Optional source name filter

        Returns:
            List of matching documents sorted by similarity (descending)
        """
        import numpy as np

        query = {}
        if source_filter:
            query["source"] = source_filter

        all_docs = list(self.embeddings_collection.find(query))

        if not all_docs:
            return []

        query_vec = np.array(query_embedding)
        query_norm = np.linalg.norm(query_vec)

        results = []
        for doc in all_docs:
            doc_vec = np.array(doc["embedding"])
            doc_norm = np.linalg.norm(doc_vec)

            if query_norm == 0 or doc_norm == 0:
                similarity = 0.0
            else:
                similarity = float(np.dot(query_vec, doc_vec) / (query_norm * doc_norm))

            results.append({
                "chunk_id": doc.get("chunk_id", ""),
                "page_number": doc.get("page_number", 0),
                "text": doc.get("text", ""),
                "metadata": doc.get("metadata", {}),
                "source": doc.get("source", ""),
                "similarity": similarity,
            })

        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:n_results]

    # --- Variables / Financial data operations ---

    def store_financial_data(
        self,
        source_name: str,
        company: str,
        period: str,
        currency: str,
        extracted_fields: Dict,
        calculated_ratios: Dict,
        extraction_method: Optional[str] = None,
        z_score: Optional[Dict] = None,
        reset: bool = False
    ) -> str:
        """
        Store extracted financial fields and computed ratios.

        Args:
            source_name: Name of the source document
            company: Company name
            period: Reporting period
            currency: Currency unit
            extracted_fields: Per-field dict with value + grounding metadata
                              {field_name: {value, page, location, chunk_type}}
                              or {value, error} when grounding is unavailable
            calculated_ratios: Computed ratios each containing formula, result,
                               and per-field grounding via the 'fields' sub-dict
            extraction_method: "landingai" or "openai"

        Returns:
            Inserted document ID as string
        """
        from datetime import datetime, timezone

        if reset:
            self.variables_collection.delete_many({"source": source_name})

        doc = {
            "source": source_name,
            "company": company,
            "period": period,
            "currency": currency,
            "extraction_method": extraction_method,
            "extracted_fields": extracted_fields,
            "calculated_ratios": calculated_ratios,
            "z_score": z_score,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        result = self.variables_collection.insert_one(doc)
        print(f"Stored financial data for {company} ({period})")
        return str(result.inserted_id)

    def get_financial_data(self, source_name: Optional[str] = None) -> List[Dict]:
        """Get financial data, optionally filtered by source."""
        query = {}
        if source_name:
            query["source"] = source_name
        return list(self.variables_collection.find(query, {"_id": 0}))

    # --- Utility ---

    def delete_source_data(self, source_name: str):
        """Delete all data for a given source document."""
        r1 = self.chunks_collection.delete_many({"source": source_name})
        r2 = self.embeddings_collection.delete_many({"source": source_name})
        r3 = self.variables_collection.delete_many({"source": source_name})
        print(
            f"Deleted data for {source_name}: "
            f"{r1.deleted_count} chunks, {r2.deleted_count} embeddings, "
            f"{r3.deleted_count} variables"
        )

    def get_status(self) -> Dict:
        """Get database status info."""
        return {
            "database": self.database_name,
            "chunks_count": self.chunks_collection.count_documents({}),
            "embeddings_count": self.embeddings_collection.count_documents({}),
            "variables_count": self.variables_collection.count_documents({}),
        }

    def close(self):
        """Close MongoDB connection."""
        self.client.close()


# Singleton instance
_mongodb_manager: Optional[MongoDBManager] = None


def get_mongodb_manager() -> MongoDBManager:
    """Get or create singleton MongoDB manager."""
    global _mongodb_manager
    if _mongodb_manager is None:
        _mongodb_manager = MongoDBManager()
    return _mongodb_manager
