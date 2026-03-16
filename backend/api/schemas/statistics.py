from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class CompanyInfo(BaseModel):
    """Basic company info for dropdown selection."""
    source: str
    company: str
    period: str
    currency: str


class CompaniesResponse(BaseModel):
    """Response for companies list endpoint."""
    success: bool
    data: Optional[List[CompanyInfo]] = None
    error: Optional[str] = None


class FinancialDataResponse(BaseModel):
    """Response for financial data of a specific company."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ExplainRequest(BaseModel):
    """Request for LLM explanation."""
    group_name: str
    group_label: str
    ratios: Dict[str, Any]
    thresholds: Dict[str, Any]


class ExplainResponse(BaseModel):
    """Response for LLM explanation."""
    success: bool
    explanation: Optional[str] = None
    recommendations: Optional[str] = None
    error: Optional[str] = None


class PageContentResponse(BaseModel):
    """Response for document page content."""
    success: bool
    page_text: Optional[str] = None
    page_number: Optional[int] = None
    error: Optional[str] = None
