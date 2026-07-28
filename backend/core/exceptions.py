from __future__ import annotations
"""Custom HTTP exceptions for LedgerLens."""
from fastapi import HTTPException, status


class ModerationBlockedError(HTTPException):
    """Raised when an uploaded image fails the moderation gate."""
    def __init__(self, reason: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "moderation_blocked",
                "blocked_reason": reason,
                "message": "Image was blocked by the content moderation gate.",
            },
        )


class DocumentNotFoundError(HTTPException):
    def __init__(self, doc_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "document_id": doc_id},
        )


class ExtractionError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "extraction_failed", "message": detail},
        )
