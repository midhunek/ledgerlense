# Walkthrough: Robust JSON Extraction for Groq

I have updated the extraction service to resolve the `json_validate_failed` errors when processing complex documents like Amazon invoices.

## Changes Made

### 1. Enhanced Extraction Prompt
In [extraction.py](file:///Users/midhun/Documents/iitrootkee/ledgerlens/backend/services/extraction.py), I've refined the prompt to be more explicit about JSON requirements:
- Added a strict instruction to return only a valid JSON object.
- Explicitly forbade markdown formatting (like ```json) which can sometimes confuse the validation layer.
- Simplified the schema representation.

### 2. Resource Management
- **Token Limit**: Added `max_tokens=2048` to the API call. This ensures that the model has enough "room" to complete the JSON for invoices with many line items without being cut off.
- **Service Stability**: Restarted the backend to ensure the new configuration is active.

## Verification

- **Health Check**: Confirmed backend is active and healthy.
- **Logs**: Verified that the server started successfully without configuration errors.

## Next Steps

> [!TIP]
> **Please try uploading the Amazon invoice image again.** The increased token limit and stricter prompt should allow the model to finish the JSON structure correctly.
