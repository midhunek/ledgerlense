# Task: Groq Integration and Project Execution

- [x] Update Configuration
    - [x] Update `.env` with Groq API Key and Base URL
    - [x] Update `backend/config/settings.py` to support `OPENAI_BASE_URL`
- [x] Refactor Backend for Groq Compatibility
    - [x] Modify `backend/services/extraction.py` to use Groq-compatible client and parsing
    - [x] Modify `backend/services/moderation.py` to bypass/gracefully handle non-OpenAI providers
- [x] Install Dependencies
    - [x] Install backend requirements
    - [x] Install frontend requirements
- [x] Start Services
    - [x] Start backend (FastAPI)
    - [x] Start frontend (Streamlit)
- [x] Verification
    - [x] Verify extraction with health check
