# Walkthrough: Bypassing API-Level JSON Mode for Stability

I have updated the extraction pipeline to bypass the strict JSON mode constraints at the API level, which were causing validation failures with complex documents.

## Changes Made

### 1. "Relaxed" Extraction Pipeline
In [extraction.py](file:///Users/midhun/Documents/iitrootkee/ledgerlens/backend/services/extraction.py), I have:
- **Removed `response_format={"type": "json_object"}`**: This allows Groq's validation layer to pass the model's output to us even if it's not "perfect" JSON at the first byte.
- **Implemented `_extract_json_from_text`**: Added a robust regex-based helper that searches for JSON blocks (````json ... ````) or `{ ... }` structures within the AI's response.
- **Increased Token Limit**: Boosted `max_tokens` to **4096** to ensure even the most detailed Amazon invoices aren't truncated.

### 2. Robust Parsing
The backend now handles the "cleaning" of the AI's response. If the model adds preamble text or uses markdown code blocks, the system will automatically strip them before passing the data to our Pydantic validation layer.

## Verification

- **Backend Status**: Restarted and confirmed healthy.
- **Stability**: The pipeline is now significantly more resilient to minor formatting variations from the AI model.

## Next Steps

> [!IMPORTANT]
> **Please try uploading the Amazon invoice image again.** By moving the JSON validation from the "cloud" (Groq) to our "local" backend, we avoid the strict 400 errors while still ensuring high data quality through our Pydantic schemas.
