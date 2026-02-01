"""
Lightweight PDF parser using PyMuPDF (fitz).
Replaces docling for text-based PDFs (no OCR for scanned documents).
"""

import logging
from typing import Optional

logging.basicConfig(level=logging.INFO)


class PDFParser:
    """
    Simple PDF text extractor using PyMuPDF.
    
    For text-based PDFs (where text is selectable), this works well.
    For scanned/image-based PDFs, consider using docling with OCR.
    """

    def __init__(self):
        logging.info("Initializing PDFParser (pymupdf)...")

    def extract_text(self, pdf_bytes: bytes, filename: str = "document.pdf") -> Optional[str]:
        """
        Extract text from PDF bytes.

        Args:
            pdf_bytes: Raw PDF file content
            filename: Name of the file for logging

        Returns:
            Extracted text as string, or None if extraction fails
        """
        try:
            import fitz  # pymupdf

            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            text_parts = []
            for page_num, page in enumerate(doc):
                page_text = page.get_text()
                if page_text.strip():
                    text_parts.append(page_text)
            doc.close()

            full_text = "\n\n".join(text_parts)
            if full_text.strip():
                logging.info(f"[PDFParser] Extracted {len(full_text)} chars from {filename}")
                return full_text
            else:
                logging.warning(f"[PDFParser] No text found in {filename} (may be scanned/image-based)")
                return None

        except ImportError:
            logging.error(f"[PDFParser] pymupdf not installed, cannot parse {filename}")
            return None
        except Exception as e:
            logging.error(f"[PDFParser] Failed to parse {filename}: {e}")
            return None

    def convert_document(self, pdf_bytes: bytes, name: str = "document.pdf") -> "ConversionResult":
        """
        Compatibility method matching DoclingPDFParser interface.
        Returns a simple object with the extracted text.
        """
        text = self.extract_text(pdf_bytes, name)
        return ConversionResult(text=text, filename=name)

    def conversion_to_markdown(self, conversion: "ConversionResult") -> Optional[str]:
        """
        Compatibility method matching DoclingPDFParser interface.
        Returns the extracted text (already plain text, not markdown).
        """
        return conversion.text


class ConversionResult:
    """Simple result object for compatibility with existing code."""
    
    def __init__(self, text: Optional[str], filename: str):
        self.text = text
        self.filename = filename
