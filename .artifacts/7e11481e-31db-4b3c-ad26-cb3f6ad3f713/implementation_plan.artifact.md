# Project Setup and Execution Plan (Groq Integration)

This plan outlines the steps to set up the LedgerLens project using **Groq** instead of OpenAI to provide a free alternative for LLM extraction and vision tasks.

## User Review Required

> [!IMPORTANT]
> Since we are switching to Groq, we will use the `llama-3.2-11b-vision-preview` model for extraction. Note that Groq does not have a native "Moderation" API like OpenAI, so the moderation gate will be bypassed for now.

## Proposed Changes

### Configuration

#### [MODIFY] [.env](file:///Users/midhun/Documents/iitrootkee/ledgerlens/.env)
- Set `GROQ_API_KEY` with your key.
- Set `OPENAI_API_KEY` to the same Groq key (as a fallback/convenience).
- Update `OPENAI_MODEL` to `llama-3.2-11b-vision-preview`.
- Update `OPENAI_BASE_URL` to `https://api.groq.com/openai/v1`.

### Backend Enhancements

#### [MODIFY] [settings.py](file:///Users/midhun/Documents/iitrootkee/ledgerlens/backend/config/settings.py)
- Add `OPENAI_BASE_URL` to the settings (defaulting to OpenAI if not provided).

#### [MODIFY] [extraction.py](file:///Users/midhun/Documents/iitrootkee/ledgerlens/backend/services/extraction.py)
- Update `OpenAI` client initialization to use `base_url=settings.OPENAI_BASE_URL`.
- Modify `extract_invoice` to use regular `chat.completions.create` with JSON mode if `beta.chat.completions.parse` is not supported by the provider (Groq).

#### [MODIFY] [moderation.py](file:///Users/midhun/Documents/iitrootkee/ledgerlens/backend/services/moderation.py)
- Update to gracefully handle or bypass moderation if the provider is Groq.

### Dependencies

1. **Install Backend Dependencies**:
   - Activate `venv`.
   - Run `pip install -r backend/requirements.txt`.

2. **Install Frontend Dependencies**:
   - Activate `venv`.
   - Run `pip install -r frontend/requirements.txt`.

### Execution

1. **Start Backend**:
   - Run `uvicorn app:app --reload --port 8000` from the `backend` directory.

2. **Start Frontend**:
   - Run `streamlit run app.py` from the `frontend` directory.

## Verification Plan

### Manual Verification
- Upload an invoice and verify that Groq correctly extracts the data.
- Check backend logs to ensure the Groq API is being called.
