from __future__ import annotations
"""
Application logger with PII redaction.

Every log record passes through PIIRedactingFormatter before being written
to disk or stdout — SSNs, emails, and phone numbers are replaced with
[REDACTED] automatically.
"""
import logging
import os
from logging.handlers import RotatingFileHandler

from services.pii_redactor import redact


class PIIRedactingFormatter(logging.Formatter):
    """Custom formatter that scrubs PII from all log messages."""

    def format(self, record: logging.LogRecord) -> str:
        original = super().format(record)
        return redact(original)


def _build_logger(name: str = "ledgerlens") -> logging.Logger:
    log = logging.getLogger(name)
    if log.handlers:
        return log  # already configured

    log.setLevel(logging.INFO)

    fmt = PIIRedactingFormatter(
        "%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    # Console handler
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    log.addHandler(ch)

    # File handler (rotating, max 10 MB × 3 backups)
    os.makedirs("logs", exist_ok=True)
    fh = RotatingFileHandler("logs/ledgerlens.log", maxBytes=10_485_760, backupCount=3)
    fh.setFormatter(fmt)
    log.addHandler(fh)

    return log


logger = _build_logger()
