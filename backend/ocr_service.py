import io
import re
import logging
from pathlib import Path
from typing import Optional

import pytesseract
from PIL import Image, ImageFilter, ImageEnhance

from image_utils import preprocess_image, pdf_to_images

logger = logging.getLogger(__name__)

TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


class OCRService:
    def get_tesseract_version(self) -> str:
        return pytesseract.get_tesseract_version().string

    def get_available_languages(self) -> list[str]:
        try:
            langs = pytesseract.get_languages(config="")
            return [l for l in langs if l != "osd"]
        except Exception:
            return ["eng"]

    def extract_text(
        self,
        file_path: Path,
        file_bytes: bytes,
        filename: str,
        language: str = "eng",
    ) -> dict:
        suffix = file_path.suffix.lower()

        if suffix == ".pdf":
            logger.info("Converting PDF to images…")
            images = pdf_to_images(file_bytes)
            if not images:
                raise ValueError("Could not extract any pages from the PDF.")
        else:
            img = Image.open(io.BytesIO(file_bytes))
            images = [img]

        page_count = len(images)
        logger.info(f"Processing {page_count} page(s)…")

        page_texts: list[str] = []
        for idx, img in enumerate(images):
            logger.info(f"  OCR page {idx + 1}/{page_count}…")
            processed = preprocess_image(img)
            text = pytesseract.image_to_string(
                processed,
                lang=language,
                config="--psm 3 --oem 3",
            )
            page_texts.append(text)

        if page_count > 1:
            combined = "\n\n── Page Break ──\n\n".join(page_texts)
        else:
            combined = page_texts[0] if page_texts else ""

        cleaned = self._clean_text(combined)

        return {
            "filename": filename,
            "language": language,
            "page_count": page_count,
            "text": cleaned,
            "word_count": len(cleaned.split()) if cleaned.strip() else 0,
            "char_count": len(cleaned),
        }

    def _clean_text(self, raw: str) -> str:
        text = re.sub(r"\n{3,}", "\n\n", raw)
        text = re.sub(r"[^\x09\x0A\x0D\x20-\x7E\u00A0-\uFFFF]", "", text)
        return text.strip()