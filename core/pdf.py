"""PDF text extraction helper for the Resume–Job Matching Agent.

Strategy:
- Primary: pypdf (fast, lightweight)
- Fallback: pdfplumber (better layout reconstruction for complex PDFs)
- No OCR — text-layer PDFs only.
"""

from __future__ import annotations

import io
import re


_MIN_TEXT_LENGTH = 100  # chars; below this we consider extraction "near-empty"


def extract_pdf_text_bytes(pdf_bytes: bytes) -> str:
    """Extract plain text from a PDF given its raw bytes.

    Tries pypdf first. Falls back to pdfplumber if the result is empty or
    near-empty (< 100 characters after cleaning).

    Args:
        pdf_bytes: Raw bytes of a PDF file.

    Returns:
        Cleaned, normalised plain-text string.

    Raises:
        ValueError: If both extraction attempts produce no usable text.
        RuntimeError: If an unexpected extraction error occurs.
    """
    text = _extract_with_pypdf(pdf_bytes)

    if len(text) < _MIN_TEXT_LENGTH:
        text = _extract_with_pdfplumber(pdf_bytes)

    if not text.strip():
        raise ValueError(
            "No extractable text found in PDF. "
            "The file may be image-only or encrypted."
        )

    return text


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _extract_with_pypdf(pdf_bytes: bytes) -> str:
    """Extract text using pypdf."""
    try:
        import pypdf  # noqa: PLC0415

        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        pages: list[str] = []
        for page in reader.pages:
            page_text = page.extract_text() or ""
            pages.append(page_text)
        return _clean_text("\n".join(pages))
    except Exception:  # noqa: BLE001
        return ""


def _extract_with_pdfplumber(pdf_bytes: bytes) -> str:
    """Extract text using pdfplumber (fallback)."""
    try:
        import pdfplumber  # noqa: PLC0415

        pages: list[str] = []
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                pages.append(page_text)
        return _clean_text("\n".join(pages))
    except Exception:  # noqa: BLE001
        return ""


def _clean_text(raw: str) -> str:
    """Normalise whitespace and remove excessive blank lines."""
    # Collapse runs of spaces/tabs to a single space per line.
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in raw.splitlines()]
    # Collapse 3+ consecutive blank lines into 2.
    cleaned = re.sub(r"\n{3,}", "\n\n", "\n".join(lines))
    return cleaned.strip()
