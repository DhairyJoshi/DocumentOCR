import os
import sys
import shutil
import tempfile
import logging
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from ocr_service import OCRService

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Document OCR API",
    description="Offline document OCR powered by Tesseract",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

ocr_service = OCRService()

@app.get("/api/health")
async def health_check():
    """Check if the API and Tesseract are working correctly."""
    try:
        version = ocr_service.get_tesseract_version()
        available_langs = ocr_service.get_available_languages()
        return {
            "status": "ok",
            "tesseract_version": version,
            "available_languages": available_langs,
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Tesseract not available: {str(e)}")


ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".pdf", ".webp"}
MAX_FILE_SIZE_MB = 25


@app.post("/api/ocr/extract")
async def extract_text(
    file: UploadFile = File(...),
    language: str = Form(default="eng"),
):
    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Supported: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    content = await file.read()

    size_mb = len(content) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({size_mb:.1f} MB). Maximum allowed: {MAX_FILE_SIZE_MB} MB",
        )

    logger.info(f"Processing '{file.filename}' ({size_mb:.2f} MB) | lang={language}")

    tmp_path = UPLOAD_DIR / f"tmp_{file.filename}"
    try:
        with open(tmp_path, "wb") as f:
            f.write(content)

        result = ocr_service.extract_text(
            file_path=tmp_path,
            file_bytes=content,
            filename=file.filename,
            language=language,
        )

        logger.info(
            f"Done: {result['word_count']} words, {result['char_count']} chars, "
            f"{result['page_count']} page(s)"
        )
        return JSONResponse(content=result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OCR failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(str(FRONTEND_DIR / "index.html"))

    @app.get("/result")
    async def serve_result():
        return FileResponse(str(FRONTEND_DIR / "result.html"))

    @app.get("/{filename}")
    async def serve_static(filename: str):
        file_path = FRONTEND_DIR / filename
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        raise HTTPException(status_code=404, detail="File not found")