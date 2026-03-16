from pydantic import BaseModel
from typing import Optional


class ServicesStatus(BaseModel):
    """Status of external services."""
    openai: bool = False
    landing_ai: bool = False
    mongodb: bool = False


class StatusData(BaseModel):
    """Data returned from status endpoint."""
    database_initialized: bool
    total_chunks: int
    total_embeddings: int
    total_variables: int
    embedding_model: str
    llm_model: str
    services: ServicesStatus


class StatusResponse(BaseModel):
    """Response for status endpoint."""
    success: bool
    data: Optional[StatusData] = None
    error: Optional[str] = None
