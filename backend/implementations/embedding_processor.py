import os
from typing import List, Dict, Optional
# from openai import OpenAI
import time
from langfuse.openai import OpenAI

class EmbeddingProcessor:
    def __init__(self, api_key: Optional[str] = None, model: str = "text-embedding-3-large"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided. Set OPENAI_API_KEY env variable or pass api_key parameter.")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        print(f"Initialized EmbeddingProcessor with model: {self.model}")
    
    def create_embedding(self, text: str) -> List[float]:
        try:
            response = self.client.embeddings.create(
                input=text,
                model=self.model
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error creating embedding: {e}")
            raise
    
    def create_embeddings_batch(self, texts: List[str], batch_size: int = 100, delay: float = 0.1) -> List[List[float]]:
        
        embeddings = []
        total_texts = len(texts)
        
        print(f"\nCreating embeddings for {total_texts} texts")
        
        for i in range(0, total_texts, batch_size):
            batch = texts[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total_texts + batch_size - 1) // batch_size
            
            print(f"Batch {batch_num}/{total_batches} ({len(batch)} texts)...", end=" ")
            
            try:
                response = self.client.embeddings.create(
                    input=batch,
                    model=self.model
                )
                
                # Extract embeddings from response
                batch_embeddings = [item.embedding for item in response.data]
                embeddings.extend(batch_embeddings)
                
                # Add delay to avoid rate limiting
                if i + batch_size < total_texts:
                    time.sleep(delay)
                    
            except Exception as e:
                print(f"Error: {e}")
                raise
        
        print(f"Successfully created {len(embeddings)} embeddings")
        return embeddings
    
    def process_chunks(self, chunks: List[Dict], batch_size: int = 100, delay: float = 0.1) -> List[Dict]:
        """Process chunks to create embeddings and add to metadata. """
        print(f"\nProcessing {len(chunks)} chunks for embedding...")
        
        # Extract texts
        texts = [chunk['text'] for chunk in chunks]
        
        # Create embeddings
        embeddings = self.create_embeddings_batch(texts, batch_size, delay)
        
        # Add embeddings to chunks
        enriched_chunks = []
        for chunk, embedding in zip(chunks, embeddings):
            enriched_chunk = {
                'text': chunk['text'],
                'metadata': chunk['metadata'],
                'embedding': embedding
            }
            enriched_chunks.append(enriched_chunk)
        
        print(f"Added embeddings to {len(enriched_chunks)} chunks")
        print(f"Embedding dimension: {len(embeddings[0])}")
        
        return enriched_chunks
    
    def get_embedding_dimension(self) -> int:
        if "3-large" in self.model:
            return 3072
        elif "3-small" in self.model:
            return 1536
        else:
            test_embedding = self.create_embedding("test")
            return len(test_embedding)
