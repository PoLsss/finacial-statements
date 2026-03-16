"""
Singleton ChromaDB Client

Provides a single shared instance of ChromaDB client to prevent
"different settings" errors when multiple modules access the database.
"""
import chromadb
from chromadb.config import Settings
from pathlib import Path
import os
from typing import Optional

# Configuration
DB_NAME = str(Path(__file__).parent.parent / "chroma_db")
collection_name = os.getenv("COLLECTION_NAME", "financial_reports")

# Singleton instance
_chroma_client: Optional[chromadb.PersistentClient] = None
_collection = None


def get_chroma_client() -> chromadb.PersistentClient:
    """
    Get or create the singleton ChromaDB client.
    
    Returns:
        ChromaDB PersistentClient instance
    """
    global _chroma_client
    
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(
            path=DB_NAME,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        print(f"✓ Initialized shared ChromaDB client at: {DB_NAME}")
    
    return _chroma_client


def get_collection(name: Optional[str] = None):
    """
    Get or create the collection.
    
    Args:
        name: Collection name (default from env)
        
    Returns:
        ChromaDB Collection instance or None if not exists
    """
    global _collection
    
    collection_name_to_use = name or collection_name
    
    try:
        client = get_chroma_client()
        _collection = client.get_collection(collection_name_to_use)
        return _collection
    except Exception as e:
        print(f"Warning: Could not load collection '{collection_name_to_use}': {e}")
        return None


def reset_client():
    """Reset the singleton client (useful for testing)."""
    global _chroma_client, _collection
    _chroma_client = None
    _collection = None
