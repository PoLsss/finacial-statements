from pydantic import BaseModel
from typing import List, Optional, Any


class ChatMessage(BaseModel):
    """Single chat message."""
    role: str
    content: str


class ChatRequest(BaseModel):
    """Request body for chat endpoint."""
    question: str
    history: Optional[List[ChatMessage]] = []
    use_agent: Optional[bool] = None


class ChunkMetadata(BaseModel):
    """Metadata for a retrieved chunk."""
    source: str = ""
    page_index: int = 0
    chunk_id: int = 0
    tokens: int = 0
    has_table: bool = False


class Chunk(BaseModel):
    """Retrieved chunk with content and metadata."""
    page_content: str
    metadata: dict = {}


class RoutingMetadata(BaseModel):
    """Metadata about RAG routing decision."""
    complexity_level: str = "simple"
    complexity_score: float = 0.0
    routing_decision: str = "simple"
    reasoning: Optional[str] = None
    agent_mode: Optional[bool] = None
    analysis_type: Optional[str] = None
    agent_steps: Optional[List[str]] = None
    insights_count: Optional[int] = None
    sources: Optional[List[str]] = None


class ChatData(BaseModel):
    """Data returned from chat endpoint."""
    answer: str
    chunks: List[Chunk]
    routing_metadata: RoutingMetadata


class ChatResponse(BaseModel):
    """Response for chat endpoint."""
    success: bool
    data: Optional[ChatData] = None
    error: Optional[str] = None
