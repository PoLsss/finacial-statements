from pydantic import BaseModel
from typing import Optional


class UploadData(BaseModel):
    """Data returned after successful upload processing."""
    source_name: str
    total_chunks: int
    total_embeddings: int
    financial_extraction: bool
    extraction_method: Optional[str] = None
    ratios_computed: bool
    processing_time_seconds: float


class UploadResponse(BaseModel):
    """Response for upload endpoint."""
    success: bool
    message: str
    data: Optional[UploadData] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
