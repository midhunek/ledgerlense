from __future__ import annotations
"""
GPT-4o vision extraction service.

Pipeline:
  1. Open image with Pillow, resize to ≤ 2048px on the longest side (cost control)
  2. Base64-encode the resized image
  3. Call client.beta.chat.completions.parse() with InvoiceExtraction as
     response_format — the SDK validates the JSON shape and returns a typed object
  4. Return the parsed InvoiceExtraction + token usage for cost tracking

Using client.beta.chat.completions.parse() (OpenAI SDK ≥ 1.40) is the correct
way to pass a Pydantic model as response_format. It returns a .parsed attribute
of the correct Pydantic type — no json.loads() needed.
"""
import base64
import io
from dataclasses import dataclass

import json
from openai import OpenAI
from PIL import Image

from config.settings import settings
from core.logger import logger
from schemas.invoice import InvoiceExtraction

client = OpenAI(
    api_key=settings.OPENAI_API_KEY,
    base_url=settings.OPENAI_BASE_URL
)

MAX_PX = 2048  # longest-side limit for cost control

EXTRACTION_PROMPT = """You are an expert invoice and receipt data extractor.

Extract all available fields from the invoice/receipt image. For EVERY field, 
set a confidence score between 0.0 (completely uncertain) and 1.0 (certain).

Rules:
- Set confidence < 0.75 for any field you are not fully certain about
- If a field is not present in the image, set value to null and confidence to 0.0
- For line_items, extract every visible line item. Set item confidence based on 
  how clearly the values are readable
- overall_confidence should reflect your general certainty about the full extraction
- Date should be in YYYY-MM-DD format when possible
- Currency should be a 3-letter code (INR, USD, EUR, GBP, etc.)
- All monetary values should be numeric (no currency symbols)
"""


@dataclass
class ExtractionResult:
    extraction: InvoiceExtraction
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    estimated_cost_usd: float


def _resize_image(image_bytes: bytes) -> tuple[bytes, str]:
    """
    Resize image so longest side ≤ MAX_PX. Returns (bytes, mime_type).
    Always outputs PNG for consistency.
    """
    img = Image.open(io.BytesIO(image_bytes))
    img = img.convert("RGB")

    w, h = img.size
    if max(w, h) > MAX_PX:
        scale = MAX_PX / max(w, h)
        new_w, new_h = int(w * scale), int(h * scale)
        img = img.resize((new_w, new_h), Image.LANCZOS)
        logger.info("Resized image from %dx%d to %dx%d", w, h, new_w, new_h)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue(), "image/png"


def extract_invoice(image_bytes: bytes) -> ExtractionResult:
    """
    Extract structured invoice data from raw image bytes.

    Args:
        image_bytes: Raw binary image data (JPG or PNG).

    Returns:
        ExtractionResult containing the parsed InvoiceExtraction and token usage.

    Raises:
        RuntimeError: If the OpenAI API call fails or returns a refusal.
    """
    # Step 1: resize image
    resized_bytes, mime_type = _resize_image(image_bytes)

    # Step 2: base64 encode
    b64_str = base64.standard_b64encode(resized_bytes).decode("utf-8")
    data_uri = f"data:{mime_type};base64,{b64_str}"

    logger.info(
        "Sending image to %s for extraction (%d bytes after resize)",
        settings.OPENAI_MODEL,
        len(resized_bytes),
    )

    # Step 3: call completion
    # Note: Using standard create + manual parse for broad provider compatibility (Groq/OpenAI)
    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": data_uri, "detail": "high"},
                    },
                    {
                        "type": "text",
                        "text": f"{EXTRACTION_PROMPT}\n\nReturn the result in JSON format matching this schema: {json.dumps(InvoiceExtraction.model_json_schema())}",
                    },
                ],
            }
        ],
        response_format={"type": "json_object"},
    )

    choice = response.choices[0]
    content = choice.message.content

    if not content:
        raise RuntimeError("AI returned empty content")

    # Handle API refusals or errors in content
    try:
        data = json.loads(content)
        extracted = InvoiceExtraction(**data)
    except Exception as e:
        logger.error("Failed to parse AI response as InvoiceExtraction: %s", content)
        raise RuntimeError(f"Failed to parse extraction result: {str(e)}")

    usage = response.usage
    total_tokens = usage.total_tokens if usage else 0
    prompt_tokens = usage.prompt_tokens if usage else 0
    completion_tokens = usage.completion_tokens if usage else 0
    cost = total_tokens * settings.MODEL_COST_PER_TOKEN

    logger.info(
        "Extraction complete. vendor=%s overall_confidence=%.2f tokens=%d cost=$%.5f",
        extracted.vendor.value,
        extracted.overall_confidence,
        total_tokens,
        cost,
    )

    return ExtractionResult(
        extraction=extracted,
        total_tokens=total_tokens,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        estimated_cost_usd=cost,
    )
