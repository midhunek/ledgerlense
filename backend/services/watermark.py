"""
PIL watermarking service.

Adds a visible provenance stamp to uploaded invoice images before archival:
  - doc_id + timestamp in bottom-right corner
  - Semi-transparent gray text on an RGBA overlay (alpha-composite)
  - Output saved as PNG to processed/{doc_id}_watermarked.png
"""
from __future__ import annotations

import io
import os
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont

from config.settings import settings
from core.logger import logger


def _get_font(size: int = 24) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Try to load a system font; fall back to Pillow's built-in."""
    for font_path in ["arial.ttf", "Arial.ttf", "DejaVuSans.ttf", "/Library/Fonts/Arial.ttf"]:
        try:
            return ImageFont.truetype(font_path, size)
        except (IOError, OSError):
            continue
    return ImageFont.load_default()


def add_watermark(image_bytes: bytes, doc_id: int) -> str:
    """
    Stamp the image with a provenance watermark and save to disk.

    Args:
        image_bytes: Raw image bytes (original upload).
        doc_id:      Database document ID used in the stamp text.

    Returns:
        Absolute path to the saved watermarked image.
    """
    processed_dir = settings.PROCESSED_DIR
    os.makedirs(processed_dir, exist_ok=True)

    # Open and convert to RGBA for alpha-composite overlay
    img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    w, h = img.size

    # Create transparent overlay the same size
    overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)

    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    stamp_text = f"LedgerLens | Doc #{doc_id} | {timestamp}"

    font = _get_font(max(16, w // 40))

    # Measure text to position in bottom-right
    bbox = draw.textbbox((0, 0), stamp_text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    margin = 12
    x = w - text_w - margin
    y = h - text_h - margin

    # Draw semi-transparent gray text (alpha=160 ≈ 63% opacity)
    draw.text((x, y), stamp_text, fill=(80, 80, 80, 160), font=font)

    # Alpha-composite the overlay onto the original
    watermarked = Image.alpha_composite(img, overlay)

    output_path = os.path.join(processed_dir, f"{doc_id}_watermarked.png")
    watermarked.convert("RGB").save(output_path, format="PNG")

    logger.info("Watermarked image saved: %s", output_path)
    return output_path
