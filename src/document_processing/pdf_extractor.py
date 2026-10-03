"""
PDF Document Extractor Module for ContractRisk AI

Extracts text, page numbers, character counts, and structural metadata from PDF contracts
using PyMuPDF (fitz). Handles empty pages, scanned PDF detection, and error safety.
"""

import hashlib
import os
from pathlib import Path
from typing import Union
import fitz  # PyMuPDF

from src.document_processing.exceptions import (
    CorruptedDocumentError,
    EmptyDocumentError,
)
from src.document_processing.models import (
    DocumentElement,
    DocumentMetadata,
    ElementType,
    ExtractedDocument,
    SourceType,
)
from src.document_processing.normalizer import normalize_text


class PDFExtractor:
    """
    Extractor for PDF contract documents utilizing PyMuPDF (fitz).
    """

    MIN_TEXT_CHARS_THRESHOLD: int = 50

    def extract(self, file_path: Union[str, Path]) -> ExtractedDocument:
        """
        Extracts structural text elements and metadata from a PDF file.

        Args:
            file_path: Path to the PDF file.

        Returns:
            ExtractedDocument containing metadata, page elements, and aggregated text.

        Raises:
            CorruptedDocumentError: If the PDF cannot be opened or parsed.
            EmptyDocumentError: If the PDF has 0 pages or contains zero text.
        """
        file_path_obj = Path(file_path).resolve()
        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: '{file_path}'")

        # Read binary for hash and size
        try:
            raw_bytes = file_path_obj.read_bytes()
        except Exception as e:
            raise CorruptedDocumentError(str(file_path_obj), cause=str(e))

        file_size_bytes = len(raw_bytes)
        doc_id = hashlib.sha256(raw_bytes).hexdigest()[:16]

        # Open PyMuPDF document
        try:
            pdf_doc = fitz.open(stream=raw_bytes, filetype="pdf")
        except Exception as e:
            raise CorruptedDocumentError(str(file_path_obj), cause=f"PyMuPDF open error: {e}")

        page_count = len(pdf_doc)
        if page_count == 0:
            pdf_doc.close()
            raise EmptyDocumentError(str(file_path_obj))

        # Extract document metadata
        fitz_meta = pdf_doc.metadata or {}
        author = fitz_meta.get("author") or None
        title = fitz_meta.get("title") or None
        creation_date = fitz_meta.get("creationDate") or None

        elements: list[DocumentElement] = []
        total_char_count = 0
        extraction_warnings: list[str] = []

        # Iterate through pages (1-indexed)
        for page_idx in range(page_count):
            page_num = page_idx + 1
            try:
                page = pdf_doc.load_page(page_idx)
                raw_page_text = page.get_text("text")
            except Exception as e:
                warning_msg = f"Failed to extract text from page {page_num}: {e}"
                extraction_warnings.append(warning_msg)
                raw_page_text = ""

            norm_page_text = normalize_text(raw_page_text)
            char_count = len(norm_page_text)
            total_char_count += char_count

            if char_count == 0:
                extraction_warnings.append(f"Page {page_num} contains no extractable text.")

            elem = DocumentElement(
                element_id=f"{doc_id}_page_{page_num}",
                element_type=ElementType.PAGE_TEXT,
                text=norm_page_text,
                raw_text=raw_page_text,
                page_number=page_num,
                char_count=char_count,
                source_location=f"Page {page_num}",
            )
            elements.append(elem)

        pdf_doc.close()

        # Scanned PDF / OCR requirement check
        requires_ocr = False
        ocr_reason = None
        if total_char_count < self.MIN_TEXT_CHARS_THRESHOLD:
            requires_ocr = True
            ocr_reason = (
                f"Total extracted text length ({total_char_count} chars) is below "
                f"minimum threshold ({self.MIN_TEXT_CHARS_THRESHOLD} chars). "
                "Document appears to be scanned or image-only."
            )

        full_cleaned_text = "\n\n".join(e.text for e in elements if e.text)

        metadata = DocumentMetadata(
            filename=file_path_obj.name,
            file_path=str(file_path_obj),
            file_type=SourceType.PDF,
            file_size_bytes=file_size_bytes,
            author=author,
            creation_date=creation_date,
            title=title,
            page_count=page_count,
            paragraph_count=None,
            table_count=None,
            requires_ocr=requires_ocr,
            ocr_reason=ocr_reason,
            extraction_warnings=extraction_warnings,
        )

        return ExtractedDocument(
            document_id=doc_id,
            source_filename=file_path_obj.name,
            source_path=str(file_path_obj),
            source_type=SourceType.PDF,
            metadata=metadata,
            elements=elements,
            full_cleaned_text=full_cleaned_text,
            requires_ocr=requires_ocr,
        )
