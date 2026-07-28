"""
Content moderation gate using OpenAI omni-moderation-latest.

Every uploaded image is screened BEFORE any LLM vision call.
The image endpoint requires:
  - model="omni-moderation-latest"
  - input as a structured list with type="image_url"
  - URL in data URI format: "data:image/png;base64,{b64}"

Decision logic:
  - Any category score above BLOCK_THRESHOLD → block (return 422)
  - All scores below threshold → allow
"""
from __future__ import annotations

import base64
from dataclasses import dataclass

from openai import OpenAI
from config.settings import settings
from core.logger import logger

client = OpenAI(
    api_key=settings.OPENAI_API_KEY,
    base_url=settings.OPENAI_BASE_URL
)

# Categories that trigger a hard block if their score exceeds this threshold
BLOCK_THRESHOLD = 0.5


@dataclass
class ModerationResult:
    allowed: bool
    blocked_reason: str | None
    scores: dict[str, float]


def moderate_image(image_bytes: bytes, mime_type: str = "image/png") -> ModerationResult:
    """
    Run the moderation gate. Bypassed if using non-OpenAI provider (like Groq).
    """
    is_groq = (settings.OPENAI_BASE_URL and "groq" in settings.OPENAI_BASE_URL.lower()) or \
              (settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.startswith("gsk_"))

    if is_groq:
        logger.info("Bypassing moderation gate (Groq/non-OpenAI provider active)")
        return ModerationResult(allowed=True, blocked_reason=None, scores={})

    b64_str = base64.standard_b64encode(image_bytes).decode("utf-8")
    data_uri = f"data:{mime_type};base64,{b64_str}"

    logger.info("Running moderation gate on uploaded image (%d bytes)", len(image_bytes))

    response = client.moderations.create(
        model=settings.MODERATION_MODEL,
        input=[
            {
                "type": "image_url",
                "image_url": {"url": data_uri},
            }
        ],
    )

    result = response.results[0]
    scores: dict[str, float] = {
        k: v for k, v in result.category_scores.__dict__.items()
        if isinstance(v, float)
    }

    # Find the highest-scoring category
    top_category = max(scores, key=scores.get) if scores else None
    top_score = scores.get(top_category, 0.0) if top_category else 0.0

    if result.flagged or top_score >= BLOCK_THRESHOLD:
        reason = f"{top_category} (score={top_score:.3f})" if top_category else "flagged"
        logger.warning("Image blocked by moderation gate: %s", reason)
        return ModerationResult(allowed=False, blocked_reason=reason, scores=scores)

    logger.info("Image passed moderation gate (top score: %.3f)", top_score)
    return ModerationResult(allowed=True, blocked_reason=None, scores=scores)
