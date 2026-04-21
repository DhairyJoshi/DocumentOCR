import io
import logging
from PIL import Image, ImageEnhance, ImageFilter
from pdf2image import convert_from_bytes

logger = logging.getLogger(__name__)

POPPLER_PATH = r"X:\DocumentOCR\poppler\Library\bin"

def preprocess_image(img: Image.Image) -> Image.Image:
    logger.debug("Preprocessing image for OCR...")
    
    if img.mode != "RGB":
        img = img.convert("RGB")
    gray = img.convert("L")
    
    enhancer = ImageEnhance.Contrast(gray)
    high_contrast = enhancer.enhance(2.0)
    
    sharp = high_contrast.filter(ImageFilter.SHARPEN)
    
    return sharp

def pdf_to_images(pdf_bytes: bytes) -> list[Image.Image]:
    try:
        images = convert_from_bytes(
            pdf_bytes,
            dpi=300,
            fmt='png',
            poppler_path=POPPLER_PATH
        )
        return images
    except FileNotFoundError as e:
        logger.error(f"Failed to find Poppler: {e}")
        raise RuntimeError(
            "Poppler is required for PDF support but was not found. "
            "Please install Poppler for Windows and ensure it is in your PATH."
        ) from e
    except Exception as e:
        logger.error(f"Error converting PDF to images: {e}")
        raise ValueError(f"Failed to read PDF: {e}") from e