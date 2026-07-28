from __future__ import annotations
"""
SQLAlchemy CRUD operations for the documents table.
All JSON serialization/deserialization goes through here.
"""
import json
from math import ceil
from typing import Optional

from sqlalchemy import func, desc, asc
from sqlalchemy.orm import Session

from models.document import Document
from schemas.invoice import InvoiceExtraction
from schemas.api import FlaggedField


# ---------------------------------------------------------------------------
# Write operations
# ---------------------------------------------------------------------------

def create_document(
    db: Session,
    filename: str,
    image_path: str,
    extraction: InvoiceExtraction,
    flagged_fields: list[FlaggedField],
    status: str,
    processed_image_path: str,
) -> Document:
    """Insert a new document record after extraction."""
    doc = Document(
        filename=filename,
        image_path=image_path,
        processed_image_path=processed_image_path,
        status=status,
        # Flat columns for easy querying
        vendor=extraction.vendor.value,
        invoice_number=extraction.invoice_number.value,
        invoice_date=extraction.date.value,
        currency=extraction.currency.value,
        subtotal=extraction.subtotal.value,
        tax=extraction.tax.value,
        total=extraction.total.value,
        overall_confidence=extraction.overall_confidence,
        # Full JSON blobs
        extracted_json=extraction.model_dump_json(),
        flagged_fields_json=json.dumps([f.model_dump() for f in flagged_fields]),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def update_document_approval(
    db: Session,
    doc_id: int,
    reviewed_data: dict,
) -> Optional[Document]:
    """Apply reviewer corrections and mark document as approved."""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        return None

    for field, value in reviewed_data.items():
        if hasattr(doc, field) and value is not None:
            setattr(doc, field, value)

    doc.reviewed_json = json.dumps(reviewed_data)
    doc.status = reviewed_data.get("status", "approved")
    db.commit()
    db.refresh(doc)
    return doc


# ---------------------------------------------------------------------------
# Read operations
# ---------------------------------------------------------------------------

def get_document(db: Session, doc_id: int) -> Optional[Document]:
    return db.query(Document).filter(Document.id == doc_id).first()


def get_pending_documents(db: Session) -> list[Document]:
    """Return all documents that are awaiting human review."""
    return (
        db.query(Document)
        .filter(Document.status == "pending_review")
        .order_by(desc(Document.created_at))
        .all()
    )


def get_documents_paginated(
    db: Session,
    vendor: str = "",
    filename: str = "",
    status: str = "",
    page: int = 1,
    page_size: int = 10,
    sort_by: str = "id",
    order: str = "desc",
) -> dict:
    """Paginated, filtered document list."""
    query = db.query(Document)

    if vendor:
        query = query.filter(Document.vendor.ilike(f"%{vendor}%"))
    if filename:
        query = query.filter(Document.filename.ilike(f"%{filename}%"))
    if status:
        query = query.filter(Document.status == status)

    total = query.count()

    sort_col = getattr(Document, sort_by, Document.id)
    sort_fn = desc if order == "desc" else asc
    query = query.order_by(sort_fn(sort_col))

    offset = (page - 1) * page_size
    docs = query.offset(offset).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": ceil(total / page_size) if total > 0 else 1,
        "data": docs,
    }


def get_dashboard_stats(db: Session) -> dict:
    """Aggregate counts and averages for the dashboard."""
    from datetime import date

    total = db.query(func.count(Document.id)).scalar() or 0
    uploaded = db.query(func.count(Document.id)).filter(Document.status == "uploaded").scalar() or 0
    processed = db.query(func.count(Document.id)).filter(Document.status == "processed").scalar() or 0
    pending = db.query(func.count(Document.id)).filter(Document.status == "pending_review").scalar() or 0
    auto_approved = db.query(func.count(Document.id)).filter(Document.status == "auto_approved").scalar() or 0
    approved = db.query(func.count(Document.id)).filter(Document.status == "approved").scalar() or 0

    today = date.today()
    today_uploads = (
        db.query(func.count(Document.id))
        .filter(func.date(Document.created_at) == today)
        .scalar() or 0
    )

    avg_confidence = db.query(func.avg(Document.overall_confidence)).scalar() or 0.0
    total_amount = db.query(func.sum(Document.total)).scalar() or 0.0

    return {
        "total_documents": total,
        "uploaded": uploaded,
        "processed": processed,
        "pending_review": pending,
        "auto_approved": auto_approved,
        "approved": approved,
        "today_uploads": today_uploads,
        "average_confidence": round(float(avg_confidence), 4),
        "total_invoice_amount": round(float(total_amount), 2),
    }


def get_status_distribution(db: Session) -> list[dict]:
    rows = (
        db.query(Document.status, func.count(Document.id))
        .group_by(Document.status)
        .all()
    )
    return [{"status": r[0], "count": r[1]} for r in rows]


def get_daily_uploads(db: Session) -> list[dict]:
    rows = (
        db.query(func.date(Document.created_at), func.count(Document.id))
        .group_by(func.date(Document.created_at))
        .order_by(func.date(Document.created_at))
        .all()
    )
    return [{"date": str(r[0]), "count": r[1]} for r in rows]
