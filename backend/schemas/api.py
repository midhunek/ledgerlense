from __future__ import annotations
"""API request / response Pydantic schemas for all FastAPI endpoints."""
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# /ingest
# ---------------------------------------------------------------------------

class IngestResponse(BaseModel):
    success: bool
    document_id: int
    status: str                    # "auto_approved" | "pending_review"
    flagged_count: int             # number of fields below threshold
    message: str
    extraction_summary: dict       # flat dict of field → value for quick display


# ---------------------------------------------------------------------------
# /review
# ---------------------------------------------------------------------------

class FlaggedField(BaseModel):
    field: str
    value: Any
    confidence: float


class ReviewDocument(BaseModel):
    id: int
    filename: str
    status: str
    vendor: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    currency: Optional[str] = None
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    total: Optional[float] = None
    overall_confidence: Optional[float] = None
    flagged_fields: list[FlaggedField] = []
    extracted_json: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ReviewListResponse(BaseModel):
    total: int
    documents: list[ReviewDocument]


# ---------------------------------------------------------------------------
# /approve
# ---------------------------------------------------------------------------

class ApproveRequest(BaseModel):
    vendor: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    currency: Optional[str] = None
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    total: Optional[float] = None
    overall_confidence: Optional[float] = None
    status: str = "approved"


class ApproveResponse(BaseModel):
    success: bool
    document_id: int
    message: str


# ---------------------------------------------------------------------------
# /documents (list)
# ---------------------------------------------------------------------------

class DocumentSummary(BaseModel):
    id: int
    filename: str
    vendor: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    currency: Optional[str] = None
    total: Optional[float] = None
    overall_confidence: Optional[float] = None
    status: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    data: list[DocumentSummary]


# ---------------------------------------------------------------------------
# /dashboard
# ---------------------------------------------------------------------------

class DashboardResponse(BaseModel):
    total_documents: int
    uploaded: int
    processed: int
    pending_review: int
    auto_approved: int
    approved: int
    today_uploads: int
    average_confidence: float
    total_invoice_amount: float
