import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
from pathlib import Path
import json
from backend.implementations.chroma_singleton import get_chroma_client


class DatabaseManager:
    def __init__(
        self, 
        persist_directory: Optional[str] = None,
        collection_name: str = "financial_reports"
    ):
        # Use consistent database path: backend/chroma_db
        if persist_directory is None:
            persist_directory = str(Path(__file__).parent.parent / "chroma_db")
        
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # Create persist directory if it doesn't exist
        Path(persist_directory).mkdir(parents=True, exist_ok=True)
        
        # Use singleton ChromaDB client to prevent "different settings" error
        self.client = get_chroma_client()
        
        print(f"✓ Using shared ChromaDB client at: {persist_directory}")
        
        self.collection = None
    
    def create_collection(
        self, 
        embedding_dimension: Optional[int] = None,
        reset: bool = False
    ):
        """
        Args:
            embedding_dimension: Dimension of embedding vectors (optional)
            reset: If True, delete existing collection and create new one
        """
        if reset:
            try:
                self.client.delete_collection(name=self.collection_name)
                print(f"Deleted existing collection: {self.collection_name}")
            except Exception:
                pass
        
        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "Financial reports embeddings"}
        )
        
        print(f"Collection ready: {self.collection_name}")
        print(f"Current items: {self.collection.count()}")
    
    def add_chunks(
        self, 
        chunks: List[Dict],
        batch_size: int = 100
    ):
        """
        Add chunks with embeddings to collection.
        
        Args:
            chunks: List of chunks with 'text', 'metadata', and 'embedding'
            batch_size: Batch size for adding to database
        """
        if self.collection is None:
            raise ValueError("Collection not initialized. Call create_collection() first.")
        
        total_chunks = len(chunks)
        print(f"\nAdding {total_chunks} chunks to database...")
        
        for i in range(0, total_chunks, batch_size):
            batch = chunks[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total_chunks + batch_size - 1) // batch_size
            
            print(f"Batch {batch_num}/{total_batches} ({len(batch)} chunks)...", end=" ")
            
            # Prepare data for ChromaDB
            ids = []
            embeddings = []
            documents = []
            metadatas = []
            
            for idx, chunk in enumerate(batch):
                # Generate unique ID using source and chunk index to prevent overwrites
                source = chunk['metadata'].get('source', 'unknown')
                chunk_idx = chunk['metadata'].get('chunk_index', i + idx)
                chunk_id = f"{source}_{chunk_idx}"
                ids.append(chunk_id)
                
                # Add embedding
                embeddings.append(chunk['embedding'])
                
                # Add document text
                documents.append(chunk['text'])
                
                # Add metadata (convert to JSON-serializable format)
                metadata = chunk['metadata'].copy()
                # Ensure all values are JSON-serializable
                for key, value in metadata.items():
                    if not isinstance(value, (str, int, float, bool, type(None))):
                        metadata[key] = str(value)
                metadatas.append(metadata)
            
            # Add to collection
            try:
                self.collection.add(
                    ids=ids,
                    embeddings=embeddings,
                    documents=documents,
                    metadatas=metadatas
                )
            except Exception as e:
                print(f"Error: {e}")
                raise
        
        print(f"Successfully added {total_chunks} chunks to database")
        print(f"Total items in collection: {self.collection.count()}")
    
    def query(
        self, 
        query_embedding: List[float],
        n_results: int = 5,
        where: Optional[Dict] = None,
        where_document: Optional[Dict] = None
    ) -> Dict:
        """
        Query database với embedding vector.
        
        Args:
            query_embedding: Embedding vector của query
            n_results: Number of results to return
            where: Filter on metadata
            where_document: Filter on document content
            
        Returns:
            Query results
        """
        if self.collection is None:
            raise ValueError("Collection not initialized. Call create_collection() first.")
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            where_document=where_document
        )
        
        return results
    
    def query_text(
        self,
        query_text: str,
        embedding_processor,
        n_results: int = 5,
        where: Optional[Dict] = None
    ) -> Dict:
        """
        Query database với text (tự động tạo embedding).
        
        Args:
            query_text: Text query
            embedding_processor: EmbeddingProcessor instance to create embedding
            n_results: Number of results to return
            where: Filter on metadata
            
        Returns:
            Query results
        """
        # Create embedding for query text
        query_embedding = embedding_processor.create_embedding(query_text)
        
        # Query database
        return self.query(
            query_embedding=query_embedding,
            n_results=n_results,
            where=where
        )
    
    def get_collection_info(self) -> Dict:
        """
        get collection's info.
        
        Returns:
            Dictionary  with collection information
        """
        if self.collection is None:
            return {"error": "Collection not initialized"}
        
        return {
            "name": self.collection.name,
            "count": self.collection.count(),
            "metadata": self.collection.metadata
        }
    
    def delete_collection(self):
        """Delete collection."""
        if self.collection_name:
            try:
                self.client.delete_collection(name=self.collection_name)
                print(f"Deleted collection: {self.collection_name}")
                self.collection = None
            except Exception as e:
                print(f"Error deleting collection: {e}")
    
    def reset_database(self):
        """Reset entire database."""
        try:
            self.client.reset()
            print("Database reset successfully")
            self.collection = None
        except Exception as e:
            print(f"Error resetting database: {e}")
    
    def export_collection(self, output_path: str):
        if self.collection is None:
            raise ValueError("Collection not initialized")
        
        # Get all items
        results = self.collection.get()
        
        # Save to JSON
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"Exported collection to: {output_path}")
        print(f"Total items: {len(results['ids'])}")