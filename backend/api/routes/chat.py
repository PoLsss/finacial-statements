"""Chat route for RAG Q&A."""
from fastapi import APIRouter, HTTPException
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.api.schemas.chat import (
    ChatRequest, 
    ChatResponse, 
    ChatData, 
    Chunk, 
    RoutingMetadata
)

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process chat question with hybrid RAG.
    
    - **question**: The question to ask
    - **history**: Optional conversation history
    - **use_agent**: Force agent mode (True/False) or auto-detect (None)
    """
    
    try:
        # Import here to avoid startup issues
        from backend.implementations.answers import answer_question_hybrid
        # Convert history to expected format
        history = [
            {"role": msg.role, "content": msg.content}
            for msg in (request.history or [])
        ]
        
        # Call hybrid RAG
        answer, chunks, routing_metadata = answer_question_hybrid(
            question=request.question,
            history=history,
            use_agent=request.use_agent
        )
        
        # Format chunks
        formatted_chunks = []
        for chunk in chunks:
            if hasattr(chunk, 'page_content'):
                # LangChain Document object
                formatted_chunks.append(Chunk(
                    page_content=chunk.page_content,
                    metadata=chunk.metadata if hasattr(chunk, 'metadata') else {}
                ))
            elif isinstance(chunk, dict):
                formatted_chunks.append(Chunk(
                    page_content=chunk.get("page_content", chunk.get("text", "")),
                    metadata=chunk.get("metadata", {})
                ))
            else:
                formatted_chunks.append(Chunk(
                    page_content=str(chunk),
                    metadata={}
                ))
        
        # Build routing metadata
        routing_meta = RoutingMetadata(
            complexity_level=routing_metadata.get("complexity_level", "simple"),
            complexity_score=routing_metadata.get("complexity_score", 0.0),
            routing_decision=routing_metadata.get("routing_decision", "simple"),
            reasoning=routing_metadata.get("reasoning"),
            agent_mode=routing_metadata.get("agent_mode"),
            analysis_type=routing_metadata.get("analysis_type"),
            agent_steps=routing_metadata.get("agent_steps"),
            insights_count=routing_metadata.get("insights_count"),
            sources=routing_metadata.get("sources")
        )
        
        return ChatResponse(
            success=True,
            data=ChatData(
                answer=answer,
                chunks=formatted_chunks,
                routing_metadata=routing_meta
            )
        )
        
    except Exception as e:
        return ChatResponse(
            success=False,
            error=str(e)
        )
