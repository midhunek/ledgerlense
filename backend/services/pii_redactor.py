"""
PII redaction utility.

Scrubs SSNs, email addresses, and phone numbers from any string before it
touches a log line. Applied in the logger formatter so nothing leaks to disk.
"""
import re

# Compiled patterns for performance
_PATTERNS = [
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),                   # SSN: 123-45-6789
    re.compile(r"[\w.%+\-]+@[\w.\-]+\.[a-zA-Z]{2,}"),       # Email
    re.compile(r"\+?[\d\s\-().]{10,}"),                      # Phone / international
]


def redact(text: str) -> str:
    """Replace all PII matches in *text* with [REDACTED]."""
    for pattern in _PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    return text
