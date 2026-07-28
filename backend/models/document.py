"""SQLAlchemy ORM model for the documents table."""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from sqlalchemy.sql import func
from database.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # File info
    filename = Column(String(255), nullable=False)
    image_path = Column(String(500))
    processed_image_path = Column(String(500))

    # Lifecycle status:
    # uploaded → processed → pending_review | auto_approved → approved
    status = Column(String(50), default="uploaded", nullable=False, index=True)

    # Extracted fields (top-level for easy filtering/sorting)
    vendor = Column(String(255))
    invoice_number = Column(String(255))
    invoice_date = Column(String(100))
    currency = Column(String(20))
    subtotal = Column(Float)
    tax = Column(Float)
    total = Column(Float)
    overall_confidence = Column(Float)

    # Raw JSON blobs for full fidelity
    extracted_json = Column(Text)    # Full InvoiceExtraction JSON (with per-field confidence)
    reviewed_json = Column(Text)     # Reviewer-corrected JSON (after approval)
    flagged_fields_json = Column(Text)  # JSON array of flagged field objects

    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
