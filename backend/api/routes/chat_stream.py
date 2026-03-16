"""Streaming chat route for RAG Q&A with Server-Sent Events."""
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pathlib import Path
import sys
import json
import asyncio

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.api.schemas.chat import ChatRequest

router = APIRouter()


async def generate_stream(request: ChatRequest):
    """Generator for SSE streaming response with thinking steps."""
    
    try:
        # Import here to avoid startup issues
        from backend.implementations.answers import answer_question_hybrid
        
        # Send thinking steps
        steps = [
            {"type": "thinking", "step": "analyzing", "message": "🔍 Analyzing your question..."},
            {"type": "thinking", "step": "classifying", "message": "🧠 Classifying question complexity..."},
            {"type": "thinking", "step": "routing", "message": "🔀 Determining RAG strategy..."},
        ]
        
        for step in steps:
            yield f"data: {json.dumps(step)}\n\n"
            await asyncio.sleep(0.3)
        
        # Convert history to expected format
        history = [
            {"role": msg.role, "content": msg.content}
            for msg in (request.history or [])
        ]
        
        # Send retrieving step
        yield f"data: {json.dumps({'type': 'thinking', 'step': 'retrieving', 'message': '📚 Retrieving relevant context...'})}\n\n"
        await asyncio.sleep(0.2)
        
        # Call hybrid RAG
        answer, chunks, routing_metadata = answer_question_hybrid(
            question=request.question,
            history=history,
            use_agent=request.use_agent
        )
        
        # Send routing decision
        routing_decision = routing_metadata.get("routing_decision", "simple")
        complexity_score = routing_metadata.get("complexity_score", 0.0)
        
        yield f"data: {json.dumps({'type': 'routing', 'decision': routing_decision, 'score': complexity_score, 'message': f'Using {routing_decision.upper()} RAG (score: {complexity_score:.2f})'})}\n\n"
        await asyncio.sleep(0.2)
        
        # Send generating step
        yield f"data: {json.dumps({'type': 'thinking', 'step': 'generating', 'message': '✨ Generating response...'})}\n\n"
        await asyncio.sleep(0.2)
        
        # Format chunks for response
        formatted_chunks = []
        for chunk in chunks:
            if hasattr(chunk, 'page_content'):
                formatted_chunks.append({
                    "page_content": chunk.page_content,
                    "metadata": chunk.metadata if hasattr(chunk, 'metadata') else {}
                })
            elif isinstance(chunk, dict):
                formatted_chunks.append({
                    "page_content": chunk.get("page_content", chunk.get("text", "")),
                    "metadata": chunk.get("metadata", {})
                })
            else:
                formatted_chunks.append({
                    "page_content": str(chunk),
                    "metadata": {}
                })
        
        # Send chunks
        yield f"data: {json.dumps({'type': 'chunks', 'chunks': formatted_chunks})}\n\n"
        
        # Stream the answer word by word for typing effect
        words = answer.split(' ')
        current_content = ""
        
        for i, word in enumerate(words):
            current_content += word + " "
            yield f"data: {json.dumps({'type': 'token', 'content': word + ' ', 'full_content': current_content.strip()})}\n\n"
            # Variable delay for more natural feel
            await asyncio.sleep(0.02 if len(word) < 5 else 0.04)
        
        # Send final metadata
        yield f"data: {json.dumps({'type': 'metadata', 'routing_metadata': routing_metadata})}\n\n"
        
        # Send done signal
        yield f"data: {json.dumps({'type': 'done', 'success': True})}\n\n"
        
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Process chat question with streaming response.
    
    Returns Server-Sent Events with:
    - thinking: Current processing step
    - routing: RAG routing decision
    - chunks: Retrieved context chunks
    - token: Streamed answer tokens
    - metadata: Final routing metadata
    - done: Completion signal
    """
    return StreamingResponse(
        generate_stream(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
