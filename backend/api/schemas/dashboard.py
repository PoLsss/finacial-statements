from pydantic import BaseModel
from typing import Optional


class DashboardData(BaseModel):
    """Dashboard summary data."""
    total_documents: int = 0
    total_chunks: int = 0
    total_embeddings: int = 0
    total_cost: float = 0.0
    total_tokens: int = 0


class DashboardResponse(BaseModel):
    """Response for dashboard endpoint."""
    success: bool
    data: Optional[DashboardData] = None
    error: Optional[str] = None
