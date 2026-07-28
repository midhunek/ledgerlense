from __future__ import annotations
"""
All FastAPI route handlers for LedgerLens.

Endpoints:
  POST /ingest             — Upload image → moderation → extract → store
  GET  /review             — Fetch pending-review documents
  POST /approve/{id}       — Submit reviewer corrections
  GET  /documents          — Paginated document list
  GET  /document/{id}      — Single document detail
  PUT  /document/{id}      — Update document fields
  GET  /processed/{id}     — Serve watermarked image
  GET  /dashboard          — Aggregate stats
  GET  /dashboard/status   — Status distribution
  GET  /dashboard/daily    — Daily upload counts
"""
import json
import os
import time
from datetime import datetime

from fastapi import APIRouter, Depends, File, UploadFile, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from config.settings import settings
from core.exceptions import (
    DocumentNotFoundError,
    ExtractionError,
    ModerationBlockedError,
)
from core.logger import logger
from database.database import get_db
from metrics import (
    auto_approvals_total,
    extraction_latency,
    moderation_latency,
    pending_review_total,
    throughput_docs,
    token_cost_usd,
)
from schemas.api import (
    ApproveRequest,
    ApproveResponse,
    DashboardResponse,
    DocumentListResponse,
    FlaggedField,
    IngestResponse,
    ReviewDocument,
    ReviewListResponse,
)
from services import extraction as extraction_svc
from services import moderation as moderation_svc
from services import storage as storage_svc
from services.watermark import add_watermark

router = APIRouter()

ALLOWED_TYPES = {"image/jpeg", "image/jpg", "image/png"}

# Rolling counter for docs/minute gauge
_ingest_timestamps: list[float] = []


def _update_throughput():
    """Update the docs/minute Prometheus gauge using a 60-second rolling window."""
    now = time.time()
    _ingest_timestamps.append(now)
    # Keep only the last 60 seconds
    cutoff = now - 60.0
    while _ingest_timestamps and _ingest_timestamps[0] < cutoff:
        _ingest_timestamps.pop(0)
    throughput_docs.set(len(_ingest_timestamps))


# ---------------------------------------------------------------------------
# POST /ingest
# ---------------------------------------------------------------------------

@router.post("/ingest", response_model=IngestResponse)
async def ingest(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Full pipeline:
    1. Validate MIME type
    2. Moderation gate (omni-moderation-latest)
    3. GPT-4o extraction with InvoiceSchema response_format
    4. Confidence routing → auto_approved | pending_review
    5. PIL watermark
    6. Persist to DB
    7. Emit Prometheus metrics
    """
    # --- MIME validation ---
    if file.content_type not in ALLOWED_TYPES:
        raise ExtractionError(f"Unsupported file type: {file.content_type}. Use JPG or PNG.")

    image_bytes = await file.read()
    logger.info("Received upload: %s (%d bytes)", file.filename, len(image_bytes))

    # --- Save original image ---
    os.makedirs(settings.UPLOADS_DIR, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    safe_filename = f"{ts}_{file.filename.replace(' ', '_')}"
    image_path = os.path.join(settings.UPLOADS_DIR, safe_filename)
    with open(image_path, "wb") as f:
        f.write(image_bytes)

    # --- 1. Moderation gate ---
    mod_start = time.perf_counter()
    mod_result = moderation_svc.moderate_image(image_bytes, file.content_type or "image/png")
    moderation_latency.observe(time.perf_counter() - mod_start)

    if not mod_result.allowed:
        raise ModerationBlockedError(mod_result.blocked_reason or "Content policy violation")

    # --- 2. GPT-4o extraction ---
    ext_start = time.perf_counter()
    try:
        ext_result = extraction_svc.extract_invoice(image_bytes)
    except Exception as exc:
        logger.exception("Extraction failed for %s", file.filename)
        raise ExtractionError(str(exc)) from exc
    extraction_latency.observe(time.perf_counter() - ext_start)

    # Emit cost metric
    token_cost_usd.inc(ext_result.estimated_cost_usd)

    extracted = ext_result.extraction

    # --- 3. Confidence routing ---
    threshold = settings.REVIEW_THRESHOLD
    flagged: list[FlaggedField] = []

    # Check every top-level scalar field
    scalar_fields = {
        "vendor": extracted.vendor,
        "invoice_number": extracted.invoice_number,
        "date": extracted.date,
        "currency": extracted.currency,
        "subtotal": extracted.subtotal,
        "tax": extracted.tax,
        "total": extracted.total,
    }
    for field_name, field_obj in scalar_fields.items():
        if field_obj.confidence < threshold:
            flagged.append(FlaggedField(
                field=field_name,
                value=field_obj.value,
                confidence=field_obj.confidence,
            ))

    # Check line items
    for i, item in enumerate(extracted.line_items):
        if item.confidence < threshold:
            flagged.append(FlaggedField(
                field=f"line_item_{i}",
                value=item.model_dump(),
                confidence=item.confidence,
            ))

    # Also flag if overall confidence is low
    if extracted.overall_confidence < threshold:
        flagged.append(FlaggedField(
            field="overall_confidence",
            value=extracted.overall_confidence,
            confidence=extracted.overall_confidence,
        ))

    status = "pending_review" if flagged else "auto_approved"

    # --- 4. PIL watermark ---
    # Use a temporary doc_id of -1 for naming; will be updated after DB insert
    processed_path = add_watermark(image_bytes, doc_id=0)

    # --- 5. Persist to DB ---
    doc = storage_svc.create_document(
        db=db,
        filename=file.filename,
        image_path=image_path,
        extraction=extracted,
        flagged_fields=flagged,
        status=status,
        processed_image_path=processed_path,
    )

    # Rename processed image to use real doc_id
    final_processed = os.path.join(settings.PROCESSED_DIR, f"{doc.id}_watermarked.png")
    if os.path.exists(processed_path) and processed_path != final_processed:
        os.rename(processed_path, final_processed)
        # Update DB with correct path
        doc.processed_image_path = final_processed
        db.commit()

    # --- 6. Prometheus metrics ---
    if status == "auto_approved":
        auto_approvals_total.inc()
    else:
        pending_review_total.inc()
    _update_throughput()

    logger.info(
        "Ingest complete: doc_id=%d status=%s flagged=%d",
        doc.id, status, len(flagged),
    )

    return IngestResponse(
        success=True,
        document_id=doc.id,
        status=status,
        flagged_count=len(flagged),
        message=f"Extraction complete. Status: {status}. {len(flagged)} field(s) flagged for review.",
        extraction_summary={
            "vendor": extracted.vendor.value,
            "invoice_number": extracted.invoice_number.value,
            "date": extracted.date.value,
            "currency": extracted.currency.value,
            "subtotal": extracted.subtotal.value,
            "tax": extracted.tax.value,
            "total": extracted.total.value,
            "overall_confidence": extracted.overall_confidence,
            "line_items_count": len(extracted.line_items),
        },
    )


# ---------------------------------------------------------------------------
# GET /review
# ---------------------------------------------------------------------------

@router.get("/review", response_model=ReviewListResponse)
def get_review_queue(db: Session = Depends(get_db)):
    """Return all documents awaiting human review with their flagged fields."""
    docs = storage_svc.get_pending_documents(db)
    results = []
    for doc in docs:
        flagged = []
        if doc.flagged_fields_json:
            try:
                raw = json.loads(doc.flagged_fields_json)
                flagged = [FlaggedField(**f) for f in raw]
            except Exception:
                pass
        results.append(ReviewDocument(
            id=doc.id,
            filename=doc.filename,
            status=doc.status,
            vendor=doc.vendor,
            invoice_number=doc.invoice_number,
            invoice_date=doc.invoice_date,
            currency=doc.currency,
            subtotal=doc.subtotal,
            tax=doc.tax,
            total=doc.total,
            overall_confidence=doc.overall_confidence,
            flagged_fields=flagged,
            extracted_json=doc.extracted_json,
            created_at=doc.created_at,
        ))
    return ReviewListResponse(total=len(results), documents=results)


# ---------------------------------------------------------------------------
# POST /approve/{id}
# ---------------------------------------------------------------------------

@router.post("/approve/{doc_id}", response_model=ApproveResponse)
def approve_document(
    doc_id: int,
    payload: ApproveRequest,
    db: Session = Depends(get_db),
):
    """Apply reviewer corrections and mark document as approved."""
    doc = storage_svc.update_document_approval(db, doc_id, payload.model_dump(exclude_none=True))
    if not doc:
        raise DocumentNotFoundError(doc_id)
    logger.info("Document %d approved by reviewer", doc_id)
    return ApproveResponse(
        success=True,
        document_id=doc_id,
        message="Document approved and corrections saved.",
    )


# ---------------------------------------------------------------------------
# GET /documents
# ---------------------------------------------------------------------------

@router.get("/documents", response_model=DocumentListResponse)
def list_documents(
    vendor: str = Query(default=""),
    filename: str = Query(default=""),
    status: str = Query(default=""),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    sort_by: str = Query(default="id"),
    order: str = Query(default="desc"),
    db: Session = Depends(get_db),
):
    result = storage_svc.get_documents_paginated(
        db, vendor=vendor, filename=filename, status=status,
        page=page, page_size=page_size, sort_by=sort_by, order=order,
    )
    return DocumentListResponse(**result)


# ---------------------------------------------------------------------------
# GET /document/{id}
# ---------------------------------------------------------------------------

@router.get("/document/{doc_id}")
def get_document(doc_id: int, db: Session = Depends(get_db)):
    doc = storage_svc.get_document(db, doc_id)
    if not doc:
        raise DocumentNotFoundError(doc_id)
    return doc


# ---------------------------------------------------------------------------
# PUT /document/{id}  — reviewer manual update
# ---------------------------------------------------------------------------

@router.put("/document/{doc_id}", response_model=ApproveResponse)
def update_document(
    doc_id: int,
    payload: ApproveRequest,
    db: Session = Depends(get_db),
):
    doc = storage_svc.update_document_approval(db, doc_id, payload.model_dump(exclude_none=True))
    if not doc:
        raise DocumentNotFoundError(doc_id)
    return ApproveResponse(success=True, document_id=doc_id, message="Document updated.")


# ---------------------------------------------------------------------------
# GET /processed/{id}  — serve watermarked image
# ---------------------------------------------------------------------------

@router.get("/processed/{doc_id}")
def get_processed_image(doc_id: int, db: Session = Depends(get_db)):
    doc = storage_svc.get_document(db, doc_id)
    if not doc or not doc.processed_image_path:
        raise DocumentNotFoundError(doc_id)
    if not os.path.exists(doc.processed_image_path):
        raise DocumentNotFoundError(doc_id)
    return FileResponse(doc.processed_image_path, media_type="image/png")


# ---------------------------------------------------------------------------
# Dashboard endpoints
# ---------------------------------------------------------------------------

@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(db: Session = Depends(get_db)):
    return storage_svc.get_dashboard_stats(db)


@router.get("/dashboard/status")
def dashboard_status(db: Session = Depends(get_db)):
    return storage_svc.get_status_distribution(db)


@router.get("/dashboard/daily")
def dashboard_daily(db: Session = Depends(get_db)):
    return storage_svc.get_daily_uploads(db)
