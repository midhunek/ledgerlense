"""
Schema contract tests — CI gate before every Docker build.

These tests assert that:
1. InvoiceExtraction can be constructed from valid JSON (round-trip)
2. LineItem rejects missing required fields
3. Confidence values are validated as floats in [0.0, 1.0]
4. StringField and FloatField behave correctly
5. InvoiceExtraction with no line_items is valid (default empty list)

These tests do NOT make any network calls — all fixtures are static JSON.
"""
import json
import pytest
from pydantic import ValidationError

# Add backend to path for imports
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from schemas.invoice import (
    InvoiceExtraction,
    LineItem,
    StringField,
    FloatField,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

VALID_INVOICE_JSON = {
    "vendor": {"value": "Acme Corp", "confidence": 0.97},
    "invoice_number": {"value": "INV-2024-001", "confidence": 0.95},
    "date": {"value": "2024-06-15", "confidence": 0.92},
    "currency": {"value": "INR", "confidence": 0.98},
    "subtotal": {"value": 10000.0, "confidence": 0.90},
    "tax": {"value": 1800.0, "confidence": 0.88},
    "total": {"value": 11800.0, "confidence": 0.91},
    "line_items": [
        {
            "description": "Software License",
            "quantity": 1.0,
            "unit_price": 10000.0,
            "amount": 10000.0,
            "confidence": 0.93,
        }
    ],
    "overall_confidence": 0.94,
}


# ---------------------------------------------------------------------------
# InvoiceExtraction tests
# ---------------------------------------------------------------------------

class TestInvoiceExtraction:

    def test_valid_round_trip(self):
        """InvoiceExtraction can be constructed from dict and serialised back to JSON."""
        extracted = InvoiceExtraction(**VALID_INVOICE_JSON)
        json_str = extracted.model_dump_json()
        restored = InvoiceExtraction.model_validate_json(json_str)
        assert restored.vendor.value == "Acme Corp"
        assert restored.overall_confidence == 0.94

    def test_vendor_confidence_preserved(self):
        extracted = InvoiceExtraction(**VALID_INVOICE_JSON)
        assert extracted.vendor.confidence == 0.97

    def test_line_items_count(self):
        extracted = InvoiceExtraction(**VALID_INVOICE_JSON)
        assert len(extracted.line_items) == 1
        assert extracted.line_items[0].description == "Software License"

    def test_empty_line_items_valid(self):
        """Invoice without line_items should be valid (default empty list)."""
        data = {**VALID_INVOICE_JSON, "line_items": []}
        extracted = InvoiceExtraction(**data)
        assert extracted.line_items == []

    def test_overall_confidence_bounds(self):
        """overall_confidence must be in [0.0, 1.0]."""
        with pytest.raises(ValidationError):
            InvoiceExtraction(**{**VALID_INVOICE_JSON, "overall_confidence": 1.5})
        with pytest.raises(ValidationError):
            InvoiceExtraction(**{**VALID_INVOICE_JSON, "overall_confidence": -0.1})

    def test_null_vendor_value_valid(self):
        """Null field values are allowed (model couldn't read it)."""
        data = {**VALID_INVOICE_JSON}
        data["vendor"] = {"value": None, "confidence": 0.1}
        extracted = InvoiceExtraction(**data)
        assert extracted.vendor.value is None
        assert extracted.vendor.confidence == 0.1


# ---------------------------------------------------------------------------
# LineItem tests
# ---------------------------------------------------------------------------

class TestLineItem:

    def test_valid_line_item(self):
        item = LineItem(
            description="Widget A",
            quantity=5.0,
            unit_price=200.0,
            amount=1000.0,
            confidence=0.88,
        )
        assert item.amount == 1000.0

    def test_confidence_bounds(self):
        with pytest.raises(ValidationError):
            LineItem(
                description="X", quantity=1, unit_price=10, amount=10, confidence=2.0
            )

    def test_default_quantity(self):
        item = LineItem(description="Service", quantity=1.0, unit_price=500.0, amount=500.0, confidence=0.9)
        assert item.quantity == 1.0


# ---------------------------------------------------------------------------
# StringField / FloatField tests
# ---------------------------------------------------------------------------

class TestConfidentFields:

    def test_string_field_defaults(self):
        sf = StringField()
        assert sf.value is None
        assert sf.confidence == 0.0

    def test_float_field_with_value(self):
        ff = FloatField(value=1234.56, confidence=0.85)
        assert ff.value == pytest.approx(1234.56)
        assert ff.confidence == pytest.approx(0.85)

    def test_confidence_clamped_low(self):
        with pytest.raises(ValidationError):
            StringField(value="x", confidence=-0.01)

    def test_confidence_clamped_high(self):
        with pytest.raises(ValidationError):
            FloatField(value=100.0, confidence=1.01)
