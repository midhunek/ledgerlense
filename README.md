# 🔍 LedgerLens — Vision-Based Document Extraction

> AI-powered invoice & receipt extraction with per-field confidence scores,
> a human review queue, PIL watermarking, PII redaction, and full observability.
>
> **IIT Roorkee New Age Software Engineering Program — Cohort C Capstone Project**

---

## ✨ Features

| Feature | Implementation |
|---|---|
| 📤 **Upload any invoice/receipt** | Streamlit `st.file_uploader` (JPG / PNG) |
| 🛡️ **Moderation gate** | `omni-moderation-latest` image endpoint — blocks before any LLM call |
| 🤖 **GPT-4o vision extraction** | `client.beta.chat.completions.parse()` with Pydantic `response_format` |
| 📊 **Per-field confidence scores** | Every field carries `confidence: float` (0–1) |
| ⚠️ **Confidence threshold router** | Fields < 0.75 → review queue; ≥ 0.75 → auto-approved |
| 🔍 **Human review UI** | `st.data_editor` for in-line field corrections |
| 🖼️ **PIL watermarking** | Alpha-composite provenance stamp before archival |
| 🔒 **PII redaction** | Regex middleware scrubs SSN/email/phone from all log lines |
| 📈 **Prometheus + Grafana** | 5 metrics: latency, token cost, approval rate, throughput |
| 🐳 **Docker Compose** | Backend + Frontend + Prometheus + Grafana in one command |
| ⚙️ **GitHub Actions CI** | pytest schema tests → docker build on every push |

---

## 🏗️ Architecture

```
[Streamlit UI :8501]
        │
        ▼ POST /ingest
[FastAPI Backend :8000]
        │
        ├─ 1. MODERATION GATE (omni-moderation-latest)
        │      ↳ score > 0.5 → 422 Blocked
        │
        ├─ 2. PIL RESIZE ≤ 2048px + base64 encode
        │
        ├─ 3. GPT-4o EXTRACTION (response_format=InvoiceExtraction)
        │      ↳ vendor, date, total, line_items — each with confidence float
        │
        ├─ 4. CONFIDENCE ROUTER
        │      ↳ field.confidence < 0.75 → pending_review
        │      ↳ all fields ≥ 0.75 → auto_approved
        │
        ├─ 5. PIL WATERMARK + STORE (SQLite)
        │
        └─ 6. PROMETHEUS METRICS (token cost, latency, throughput)
                        │
               [Prometheus :9090] → [Grafana :3000]
```

---

## 🚀 Quick Start (Local)

### Prerequisites
- Python 3.9+
- Docker Desktop (for the full stack)
- A Groq API key — free at [console.groq.com/keys](https://console.groq.com/keys) *(or an OpenAI key — both supported)*

### Option A — Docker Compose (Recommended)

```bash
# Clone and enter the project
git clone https://github.com/midhunek/ledgerlense.git
cd ledgerlense

# Create your .env file
cp .env.example .env
# Edit .env and set your API key (Groq or OpenAI — see .env.example for both options)

# Spin up everything
docker-compose up --build

# Services:
# Streamlit UI   → http://localhost:8501
# FastAPI docs   → http://localhost:8000/docs
# Prometheus     → http://localhost:9090
# Grafana        → http://localhost:3000  (admin / ledgerlens)
```

### Option B — Local Development (No Docker)

```bash
# Backend setup
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env         # fill in OPENAI_API_KEY
uvicorn app:app --reload --port 8000

# Frontend (new terminal)
cd frontend
pip install -r requirements.txt
API_URL=http://localhost:8000 streamlit run app.py
```

---

## 🧪 Running Tests

```bash
# Install backend deps first
pip install -r backend/requirements.txt

# Schema contract tests (CI gate)
pytest tests/test_schema_contracts.py -v

# Moderation gate tests (mocked)
pytest tests/test_moderation.py -v

# Endpoint tests
pytest tests/test_endpoints.py -v

# All tests
pytest tests/ -v
```

---

## 📐 Data Model

```python
class StringField(BaseModel):
    value: Optional[str]
    confidence: float          # 0.0 – 1.0

class FloatField(BaseModel):
    value: Optional[float]
    confidence: float

class LineItem(BaseModel):
    description: str
    quantity: float
    unit_price: float
    amount: float
    confidence: float          # per-line-item confidence

class InvoiceExtraction(BaseModel):
    vendor: StringField        # Every field has its own confidence
    invoice_number: StringField
    date: StringField
    currency: StringField
    subtotal: FloatField
    tax: FloatField
    total: FloatField
    line_items: list[LineItem]
    overall_confidence: float
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/ingest` | Upload image → full pipeline |
| `GET` | `/review` | Fetch pending-review documents |
| `POST` | `/approve/{id}` | Submit reviewer corrections |
| `GET` | `/documents` | Paginated list with filter/sort |
| `GET` | `/document/{id}` | Single document detail |
| `PUT` | `/document/{id}` | Update document fields |
| `GET` | `/processed/{id}` | Serve watermarked image |
| `GET` | `/dashboard` | Aggregate stats |
| `GET` | `/dashboard/status` | Status distribution |
| `GET` | `/dashboard/daily` | Daily upload counts |
| `GET` | `/metrics` | Prometheus scrape endpoint |
| `GET` | `/health` | Health check |

---

## 📊 Prometheus Metrics

| Metric | Type | Description |
|---|---|---|
| `ledgerlens_moderation_latency_seconds` | Histogram | Time for moderation gate |
| `ledgerlens_extraction_latency_seconds` | Histogram | Time for GPT-4o extraction |
| `ledgerlens_token_cost_usd_total` | Counter | Cumulative token cost in USD |
| `ledgerlens_auto_approvals_total` | Counter | Documents auto-approved |
| `ledgerlens_throughput_docs_per_minute` | Gauge | Rolling docs/min |

---

## 🔧 Configuration

All settings via `.env`:

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
MODERATION_MODEL=omni-moderation-latest
REVIEW_THRESHOLD=0.75          # Fields below this go to review queue
MODEL_COST_PER_TOKEN=0.000005  # USD per token for cost tracking
DATABASE_URL=sqlite:///./ledgerlens.db
```

---

## 📁 Project Structure

```
ledgerlens/
├── backend/
│   ├── app.py                     # FastAPI entry point
│   ├── metrics.py                 # Prometheus metrics
│   ├── config/settings.py         # Pydantic settings (loaded from .env)
│   ├── core/                      # logger, middleware, exceptions
│   ├── database/database.py       # SQLAlchemy engine + session
│   ├── models/document.py         # Document ORM model
│   ├── schemas/
│   │   ├── invoice.py             # InvoiceExtraction + per-field confidence
│   │   └── api.py                 # Endpoint request/response schemas
│   ├── services/
│   │   ├── moderation.py          # omni-moderation-latest gate
│   │   ├── extraction.py          # GPT-4o vision extraction
│   │   ├── watermark.py           # PIL provenance stamp
│   │   ├── pii_redactor.py        # SSN/email/phone redaction
│   │   └── storage.py             # CRUD operations
│   └── api/routes.py              # All route handlers
├── frontend/app.py                # Streamlit 4-tab UI
├── tests/                         # pytest test suite
├── docker/                        # Dockerfiles
├── grafana/                       # Pre-provisioned dashboard
├── prometheus.yml                 # Prometheus scrape config
├── docker-compose.yml             # Full stack orchestration
└── .github/workflows/ci.yml       # GitHub Actions CI
```

---

## 👤 Author

Built as part of the **IIT Roorkee New Age Software Engineering Program — Cohort C Capstone Project**.

---

## 📄 License

For educational purposes only — IIT Roorkee Capstone Project.
