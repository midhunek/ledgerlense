from __future__ import annotations
"""
Pydantic schemas for invoice extraction.

Design principle: every extracted field carries its own confidence float so
the confidence-threshold router can flag individual fields rather than entire
documents.

These schemas are passed directly as `response_format` to the OpenAI client
(via client.beta.chat.completions.parse), which enforces JSON shape at the
API level — no fragile json.loads() needed.
"""
from typing import Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Typed wrappers — each scalar field carries its own confidence score
# ---------------------------------------------------------------------------

class StringField(BaseModel):
    """A string value with an associated model confidence score."""
    value: Optional[str] = Field(default=None, description="Extracted string value")
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Model confidence in this field (0=uncertain, 1=certain)"
    )


class FloatField(BaseModel):
    """A numeric value with an associated model confidence score."""
    value: Optional[float] = Field(default=None, description="Extracted numeric value")
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Model confidence in this field (0=uncertain, 1=certain)"
    )


# ---------------------------------------------------------------------------
# Line item — each row on an invoice
# ---------------------------------------------------------------------------

class LineItem(BaseModel):
    """A single line item from an invoice with its own confidence score."""
    description: str = Field(description="Item or service description")
    quantity: float = Field(default=1.0, description="Quantity")
    unit_price: float = Field(default=0.0, description="Price per unit")
    amount: float = Field(default=0.0, description="Line total (qty × unit_price)")
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Model confidence in this line item"
    )


# ---------------------------------------------------------------------------
# Root extraction schema — passed as response_format to OpenAI
# ---------------------------------------------------------------------------

class InvoiceExtraction(BaseModel):
    """
    Structured invoice extraction result.
    Every scalar field is a typed wrapper carrying its own confidence score.
    Pass this class directly as response_format to enforce schema at the API level.
    """
    vendor: StringField = Field(
        default_factory=StringField,
        description="Vendor / supplier name"
    )
    invoice_number: StringField = Field(
        default_factory=StringField,
        description="Invoice or receipt number"
    )
    date: StringField = Field(
        default_factory=StringField,
        description="Invoice date in ISO 8601 (YYYY-MM-DD)"
    )
    currency: StringField = Field(
        default_factory=StringField,
        description="Three-letter currency code, e.g. INR, USD"
    )
    subtotal: FloatField = Field(
        default_factory=FloatField,
        description="Subtotal before tax"
    )
    tax: FloatField = Field(
        default_factory=FloatField,
        description="Tax amount"
    )
    total: FloatField = Field(
        default_factory=FloatField,
        description="Grand total including tax"
    )
    line_items: list[LineItem] = Field(
        default_factory=list,
        description="Individual line items from the invoice"
    )
    overall_confidence: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Overall model confidence in the entire extraction"
    )
