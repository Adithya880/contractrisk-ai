"""
ContractRisk AI - Phase 4 Document Processing Package
"""

from src.document_processing.docx_extractor import DOCXExtractor
from src.document_processing.exceptions import (
    CorruptedDocumentError,
    DocumentProcessingError,
    EmptyDocumentError,
    UnsupportedFileTypeError,
)
from src.document_processing.loader import DocumentLoader
from src.document_processing.models import (
    DocumentElement,
    DocumentMetadata,
    ElementType,
    ExtractedDocument,
    SourceType,
)
from src.document_processing.normalizer import normalize_document, normalize_text
from src.document_processing.pdf_extractor import PDFExtractor

__all__ = [
    "DocumentLoader",
    "PDFExtractor",
    "DOCXExtractor",
    "normalize_text",
    "normalize_document",
    "ExtractedDocument",
    "DocumentElement",
    "DocumentMetadata",
    "SourceType",
    "ElementType",
    "DocumentProcessingError",
    "UnsupportedFileTypeError",
    "CorruptedDocumentError",
    "EmptyDocumentError",
]
