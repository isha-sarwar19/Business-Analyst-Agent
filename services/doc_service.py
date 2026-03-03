"""
services/doc_service.py — PDF text extraction for uploaded documents.

Used to extract readable text from a user-uploaded PDF so the agent
can reference it during conversation or inject content into a PRD.
"""
import fitz  # PyMuPDF
from core.logging_config import get_logger

logger = get_logger(__name__)


def extract_pdf_text(file_bytes: bytes, filename: str = "document") -> str:
    """
    Extract all readable text from a PDF file given its raw bytes.
    Returns a single concatenated string of all page texts.
    Raises ValueError if the PDF has no extractable text.
    """
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        pages_text = []
        for page_num, page in enumerate(doc, 1):
            text = page.get_text().strip()
            if text:
                pages_text.append(f"--- Page {page_num} ---\n{text}")

        doc.close()

        if not pages_text:
            raise ValueError(
                f"No extractable text found in '{filename}'. "
                "It may be a scanned/image-only PDF."
            )

        full_text = "\n\n".join(pages_text)
        logger.info(
            "PDF extracted | file=%s | pages=%d | chars=%d",
            filename, len(pages_text), len(full_text)
        )
        return full_text

    except ValueError:
        raise
    except Exception as e:
        logger.error("PDF extraction failed | file=%s | error=%s", filename, e)
        raise ValueError(f"Could not read PDF '{filename}': {e}") from e
