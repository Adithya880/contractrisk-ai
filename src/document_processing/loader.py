"""
Document Loader Facade Module for ContractRisk AI

Provides a unified interface (DocumentLoader) to ingest PDF and DOCX contract files,
dispatching to the appropriate format extractor and automatically normalizing extracted text.
"""

from pathlib import Path
from typing import Union

from src.document_processing.docx_extractor import DOCXExtractor
from src.document_processing.exceptions import UnsupportedFileTypeError
from src.document_processing.models import ExtractedDocument, SourceType
from src.document_processing.normalizer import normalize_document
from src.document_processing.pdf_extractor import PDFExtractor


class DocumentLoader:
    """
    Unified loader facade for processing contract documents of supported formats (.pdf, .docx).
    """

    def __init__(self):
        self._pdf_extractor = PDFExtractor()
        self._docx_extractor = DOCXExtractor()

    def load_document(self, file_path: Union[str, Path]) -> ExtractedDocument:
        """
        Loads, extracts, and normalizes a contract document from disk.

        Args:
            file_path: Path to the .pdf or .docx file.

        Returns:
            ExtractedDocument instance containing metadata, elements, and normalized text.

        Raises:
            FileNotFoundError: If the file does not exist.
            UnsupportedFileTypeError: If the file extension is not supported.
            CorruptedDocumentError: If the document is damaged or unparseable.
            EmptyDocumentError: If the document contains no extractable text.
        """
        path_obj = Path(file_path).resolve()

        if not path_obj.exists():
            raise FileNotFoundError(f"File not found: '{file_path}'")

        ext = path_obj.suffix.lower()

        if ext == ".pdf":
            raw_doc = self._pdf_extractor.extract(path_obj)
        elif ext == ".docx":
            raw_doc = self._docx_extractor.extract(path_obj)
        else:
            raise UnsupportedFileTypeError(str(path_obj), supported_types=[".pdf", ".docx"])

        # Run text normalization pass over the extracted document
        return normalize_document(raw_doc)
