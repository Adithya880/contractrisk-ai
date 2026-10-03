"""
Structured Document Models for ContractRisk AI

Defines Pydantic data models representing extracted contract documents,
page/paragraph structural elements, and document metadata.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class SourceType(str, Enum):
    """Supported contract document source types."""
    PDF = "pdf"
    DOCX = "docx"


class ElementType(str, Enum):
    """Document element structural types."""
    PAGE_TEXT = "page_text"
    PARAGRAPH = "paragraph"
    HEADING = "heading"
    TABLE_CELL = "table_cell"


class DocumentElement(BaseModel):
    """
    Represents an atomic structural unit extracted from a contract document
    (e.g., a page of text, a paragraph, heading, or table cell).
    """
    model_config = ConfigDict(frozen=True)

    element_id: str = Field(description="Unique identifier for the document element.")
    element_type: ElementType = Field(description="Structural type of the element.")
    text: str = Field(description="Normalized text content of the element.")
    raw_text: str = Field(description="Unprocessed raw text content of the element.")
    page_number: Optional[int] = Field(default=None, description="1-indexed page number (applicable to PDF).")
    paragraph_index: Optional[int] = Field(default=None, description="0-indexed paragraph sequence number (applicable to DOCX).")
    heading_level: Optional[int] = Field(default=None, description="Heading hierarchy level if applicable (e.g. 1, 2, 3).")
    table_index: Optional[int] = Field(default=None, description="0-indexed table sequence number if extracted from a table.")
    row_index: Optional[int] = Field(default=None, description="Table row index if extracted from a table cell.")
    col_index: Optional[int] = Field(default=None, description="Table column index if extracted from a table cell.")
    char_count: int = Field(description="Character count of the normalized text.")
    source_location: str = Field(description="Human-readable provenance location (e.g. 'Page 1', 'Paragraph 5', 'Table 0 R1 C2').")


class DocumentMetadata(BaseModel):
    """
    Metadata attributes describing the input contract document.
    """
    filename: str = Field(description="Base filename of the input contract.")
    file_path: str = Field(description="Full path to the source file.")
    file_type: SourceType = Field(description="Source format (PDF or DOCX).")
    file_size_bytes: int = Field(description="Size of the input file in bytes.")
    author: Optional[str] = Field(default=None, description="Author metadata if present.")
    creation_date: Optional[str] = Field(default=None, description="Creation timestamp if available.")
    title: Optional[str] = Field(default=None, description="Title metadata if available.")
    page_count: Optional[int] = Field(default=None, description="Total page count (for PDFs).")
    paragraph_count: Optional[int] = Field(default=None, description="Total paragraph count (for DOCX).")
    table_count: Optional[int] = Field(default=None, description="Total table count (for DOCX).")
    requires_ocr: bool = Field(default=False, description="True if document appears scanned or has insufficient text layer.")
    ocr_reason: Optional[str] = Field(default=None, description="Explanation if OCR is required.")
    extraction_warnings: List[str] = Field(default_factory=list, description="Non-fatal warnings recorded during extraction.")


class ExtractedDocument(BaseModel):
    """
    Container representing a fully extracted and normalized contract document.
    Maintains metadata, ordered structural elements, and aggregated full text.
    """
    document_id: str = Field(description="Deterministic unique ID computed from file content hash.")
    source_filename: str = Field(description="Base filename of the extracted document.")
    source_path: str = Field(description="Full path to the source file.")
    source_type: SourceType = Field(description="Source document format.")
    metadata: DocumentMetadata = Field(description="Document metadata container.")
    elements: List[DocumentElement] = Field(default_factory=list, description="Ordered list of structural document elements.")
    full_cleaned_text: str = Field(default="", description="Aggregated, normalized full text of the contract.")
    requires_ocr: bool = Field(default=False, description="Quick-flag indicating whether OCR pipeline is required.")
