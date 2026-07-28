"""
FastAPI endpoint contract tests using TestClient.
Tests cover /health, /review, /approve, and /documents endpoints
without making real OpenAI or database calls.
"""
import sys, os, tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import pytest
from fastapi.testclient import TestClient

# Use a temp file-based SQLite so all connections share the same DB
_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_db_file.close()
_TEST_DB_URL = f"sqlite:///{_db_file.name}"

os.environ["OPENAI_API_KEY"] = "sk-test-key"
os.environ["DATABASE_URL"] = _TEST_DB_URL
os.environ["UPLOADS_DIR"] = "/tmp/ledgerlens_test_uploads"
os.environ["PROCESSED_DIR"] = "/tmp/ledgerlens_test_processed"

# Import after setting env vars
import database.database as db_module
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Patch engine to use our temp file DB
test_engine = create_engine(_TEST_DB_URL, connect_args={"check_same_thread": False})
db_module.engine = test_engine
db_module.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Create all tables
from database.database import create_tables
create_tables()

from app import app

client = TestClient(app, raise_server_exceptions=True)


class TestHealthEndpoint:

    def test_health_returns_200(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestReviewEndpoint:

    def test_review_returns_list(self):
        """GET /review should return ReviewListResponse shape."""
        response = client.get("/review")
        assert response.status_code == 200
        body = response.json()
        assert "total" in body
        assert "documents" in body
        assert isinstance(body["documents"], list)


class TestDocumentsEndpoint:

    def test_documents_returns_paginated(self):
        """GET /documents should return DocumentListResponse shape."""
        response = client.get("/documents")
        assert response.status_code == 200
        body = response.json()
        assert "total" in body
        assert "page" in body
        assert "data" in body

    def test_documents_page_param(self):
        response = client.get("/documents?page=1&page_size=5")
        assert response.status_code == 200
        assert response.json()["page"] == 1

    def test_document_not_found(self):
        response = client.get("/document/999999")
        assert response.status_code == 404


class TestApproveEndpoint:

    def test_approve_nonexistent_doc(self):
        """Approving a non-existent document should return 404."""
        payload = {"vendor": "Test Corp", "status": "approved"}
        response = client.post("/approve/999999", json=payload)
        assert response.status_code == 404


class TestDashboardEndpoint:

    def test_dashboard_returns_stats(self):
        response = client.get("/dashboard")
        assert response.status_code == 200
        body = response.json()
        assert "total_documents" in body
        assert "average_confidence" in body
        assert "auto_approved" in body

    def test_dashboard_status_returns_list(self):
        response = client.get("/dashboard/status")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_dashboard_daily_returns_list(self):
        response = client.get("/dashboard/daily")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
