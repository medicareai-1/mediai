"""
PDF utilities with no external system dependencies.

Uses PyMuPDF (pymupdf) to render PDF pages to PIL Images. Falls back to
pdf2image + Poppler only if PyMuPDF is unavailable.
"""

from typing import List

from PIL import Image
import io


def pdf_bytes_to_images(pdf_bytes: bytes) -> List[Image.Image]:
    """Convert raw PDF bytes to a list of PIL Images.

    Prefers PyMuPDF which ships as a wheel (no system installs). If PyMuPDF is
    not available, tries pdf2image (requires Poppler on Windows).
    """
    images: List[Image.Image] = []

    # Try PyMuPDF first (no system deps)
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for page in doc:
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x scale for clarity
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            images.append(img.convert("RGB"))
        doc.close()
        if images:
            return images
    except Exception:
        pass

    # Fallback to pdf2image (+ Poppler)
    try:
        from pdf2image import convert_from_bytes
        import os
        poppler_path = os.getenv('POPPLER_PATH', None)
        return convert_from_bytes(pdf_bytes, poppler_path=poppler_path)
    except Exception as e:
        raise RuntimeError(
            "PDF render failed. Install PyMuPDF: pip install pymupdf (preferred)."
        ) from e


