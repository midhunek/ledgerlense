"""
Moderation gate unit tests — all OpenAI API calls are mocked.
Tests cover the allow/block decision logic without making real network calls.

The moderation service now auto-bypasses when Groq is active.
These tests patch settings to simulate both OpenAI and Groq environments.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from unittest.mock import MagicMock, patch
import pytest

from services.moderation import moderate_image, BLOCK_THRESHOLD


def _make_mock_moderation_response(flagged: bool, scores: dict):
    """Helper to build a mock OpenAI moderation API response."""
    result = MagicMock()
    result.flagged = flagged
    result.category_scores = MagicMock()
    result.category_scores.__dict__ = scores
    response = MagicMock()
    response.results = [result]
    return response


# Patch settings to simulate OpenAI environment (not Groq)
# so the bypass check doesn't short-circuit the real tests
_openai_settings = MagicMock()
_openai_settings.OPENAI_BASE_URL = None
_openai_settings.OPENAI_API_KEY = "sk-test-openai-key"
_openai_settings.MODERATION_MODEL = "omni-moderation-latest"

# Patch settings to simulate Groq environment
_groq_settings = MagicMock()
_groq_settings.OPENAI_BASE_URL = "https://api.groq.com/openai/v1"
_groq_settings.OPENAI_API_KEY = "gsk_test_groq_key"
_groq_settings.MODERATION_MODEL = "omni-moderation-latest"


class TestModerationGate:

    @patch("services.moderation.settings", _openai_settings)
    @patch("services.moderation.client")
    def test_clean_image_passes(self, mock_client):
        """An image with all-low scores should be allowed (OpenAI mode)."""
        mock_client.moderations.create.return_value = _make_mock_moderation_response(
            flagged=False,
            scores={"hate": 0.01, "violence": 0.02, "sexual": 0.005},
        )
        result = moderate_image(b"fake_image_bytes")
        assert result.allowed is True
        assert result.blocked_reason is None

    @patch("services.moderation.settings", _openai_settings)
    @patch("services.moderation.client")
    def test_flagged_image_blocked(self, mock_client):
        """An image flagged by the API should be blocked (OpenAI mode)."""
        mock_client.moderations.create.return_value = _make_mock_moderation_response(
            flagged=True,
            scores={"hate": 0.8, "violence": 0.1, "sexual": 0.05},
        )
        result = moderate_image(b"bad_image_bytes")
        assert result.allowed is False
        assert result.blocked_reason is not None

    @patch("services.moderation.settings", _openai_settings)
    @patch("services.moderation.client")
    def test_high_score_triggers_block(self, mock_client):
        """A score above BLOCK_THRESHOLD should block even if flagged=False (OpenAI mode)."""
        mock_client.moderations.create.return_value = _make_mock_moderation_response(
            flagged=False,
            scores={"hate": BLOCK_THRESHOLD + 0.1, "violence": 0.01},
        )
        result = moderate_image(b"edge_case_bytes")
        assert result.allowed is False

    @patch("services.moderation.settings", _openai_settings)
    @patch("services.moderation.client")
    def test_scores_returned_in_result(self, mock_client):
        """ModerationResult.scores should reflect what the API returned (OpenAI mode)."""
        mock_client.moderations.create.return_value = _make_mock_moderation_response(
            flagged=False,
            scores={"hate": 0.03, "violence": 0.01},
        )
        result = moderate_image(b"fine_image")
        assert "hate" in result.scores
        assert result.scores["hate"] == pytest.approx(0.03)

    @patch("services.moderation.settings", _groq_settings)
    @patch("services.moderation.client")
    def test_groq_bypass_always_allows(self, mock_client):
        """When Groq is active, moderation gate is bypassed and always allows."""
        result = moderate_image(b"any_image")
        assert result.allowed is True
        assert result.blocked_reason is None
        assert result.scores == {}
        # Ensure the actual moderation API was NOT called
        mock_client.moderations.create.assert_not_called()

    @patch("services.moderation.settings", _groq_settings)
    @patch("services.moderation.client")
    def test_groq_bypass_detected_by_api_key_prefix(self, mock_client):
        """Groq keys start with 'gsk_' — bypass should trigger on key prefix alone."""
        result = moderate_image(b"test_bytes")
        assert result.allowed is True
        mock_client.moderations.create.assert_not_called()
