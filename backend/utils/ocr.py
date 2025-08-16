# backend/utils/ocr.py
from io import BytesIO
from typing import Optional
import mimetypes

# PDF
import pdfplumber

# Images
from PIL import Image
import pytesseract

SUPPORTED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/jpg"}
SUPPORTED_PDF_TYPES = {"application/pdf"}

def sniff_mime(filename: str) -> Optional[str]:
    # Fallback: guess the MIME type from extension
    ctype, _ = mimetypes.guess_type(filename.lower())
    return ctype

def extract_text_from_pdf_bytes(file_bytes: bytes) -> str:
    """
    Extract text from a PDF given as bytes using pdfplumber.
    """
    text_chunks = []
    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            try:
                t = page.extract_text() or ""
                text_chunks.append(t)
            except Exception:
                # If a page fails, continue (you could log this)
                continue
    return "\n".join(text_chunks).strip()

def extract_text_from_image_bytes(file_bytes: bytes) -> str:
    """
    Extract text from an image given as bytes using PIL + Tesseract.
    """
    image = Image.open(BytesIO(file_bytes))
    # Optional: Convert to grayscale or increase DPI for better OCR, if needed.
    return pytesseract.image_to_string(image) or ""

def ocr_any(file_bytes: bytes, filename: str, content_type: Optional[str]) -> str:
    """
    Routes bytes to the correct OCR pipeline based on content_type or filename.
    Returns best-effort extracted text (could be empty string).
    """
    # Prefer provided content_type; fallback to guessed MIME from filename
    ctype = content_type or sniff_mime(filename) or ""

    if ctype in SUPPORTED_PDF_TYPES or filename.lower().endswith(".pdf"):
        return extract_text_from_pdf_bytes(file_bytes)

    if ctype in SUPPORTED_IMAGE_TYPES or filename.lower().endswith((".png", ".jpg", ".jpeg")):
        return extract_text_from_image_bytes(file_bytes)

    # Not a supported OCR type; assume it's plain text
    try:
        return file_bytes.decode("utf-8", errors="ignore")
    except Exception:
        return ""
