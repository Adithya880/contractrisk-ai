"""
DOCX Document Extractor Module for ContractRisk AI

Extracts paragraphs, heading styles, tables, and structural metadata from Microsoft Word (.docx)
contracts using python-docx. Preserves element sequence order and table cell structure.
"""

import hashlib
import os
from pathlib import Path
from typing import Union
import docx

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


class DOCXExtractor:
    """
    Extractor for Microsoft Word (.docx) contract documents utilizing python-docx.
    """

    def extract(self, file_path: Union[str, Path]) -> ExtractedDocument:
        """
        Extracts structural text elements, headings, tables, and metadata from a DOCX file.

        Args:
            file_path: Path to the DOCX file.

        Returns:
            ExtractedDocument containing metadata, paragraph/table elements, and aggregated text.

        Raises:
            CorruptedDocumentError: If the DOCX cannot be opened or parsed.
            EmptyDocumentError: If the DOCX contains no paragraphs or text content.
        """
        file_path_obj = Path(file_path).resolve()
        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: '{file_path}'")

        try:
            raw_bytes = file_path_obj.read_bytes()
        except Exception as e:
            raise CorruptedDocumentError(str(file_path_obj), cause=str(e))

        file_size_bytes = len(raw_bytes)
        doc_id = hashlib.sha256(raw_bytes).hexdigest()[:16]

        try:
            docx_doc = docx.Document(file_path_obj)
        except Exception as e:
            raise CorruptedDocumentError(str(file_path_obj), cause=f"python-docx open error: {e}")

        # Extract Core Properties
        core_props = docx_doc.core_properties
        author = core_props.author or None
        title = core_props.title or None
        created_dt = core_props.created.strftime("%Y-%m-%d %H:%M:%S") if core_props.created else None

        elements: list[DocumentElement] = []
        extraction_warnings: list[str] = []

        paragraph_count = len(docx_doc.paragraphs)
        table_count = len(docx_doc.tables)

        # 1. Process Paragraphs
        for p_idx, p in enumerate(docx_doc.paragraphs):
            raw_p_text = p.text
            norm_p_text = normalize_text(raw_p_text)
            if not norm_p_text:
                continue

            # Determine if paragraph has a Heading style
            heading_level = None
            elem_type = ElementType.PARAGRAPH
            style_name = (p.style.name or "") if p.style else ""

            if style_name.startswith("Heading"):
                elem_type = ElementType.HEADING
                try:
                    heading_level = int(style_name.replace("Heading", "").strip())
                except ValueError:
                    heading_level = 1

            elem = DocumentElement(
                element_id=f"{doc_id}_p_{p_idx}",
                element_type=elem_type,
                text=norm_p_text,
                raw_text=raw_p_text,
                paragraph_index=p_idx,
                heading_level=heading_level,
                char_count=len(norm_p_text),
                source_location=f"Paragraph {p_idx}" if elem_type == ElementType.PARAGRAPH else f"Heading Level {heading_level}",
            )
            elements.append(elem)

        # 2. Process Tables
        for t_idx, table in enumerate(docx_doc.tables):
            for r_idx, row in enumerate(table.rows):
                for c_idx, cell in enumerate(row.cells):
                    raw_cell_text = cell.text
                    norm_cell_text = normalize_text(raw_cell_text)
                    if not norm_cell_text:
                        continue

                    cell_id = f"{doc_id}_t{t_idx}_r{r_idx}_c{c_idx}"
                    # Check if cell text was already added (python-docx merges can duplicate cell refs)
                    if any(e.element_id == cell_id for e in elements):
                        continue

                    elem = DocumentElement(
                        element_id=cell_id,
                        element_type=ElementType.TABLE_CELL,
                        text=norm_cell_text,
                        raw_text=raw_cell_text,
                        table_index=t_idx,
                        row_index=r_idx,
                        col_index=c_idx,
                        char_count=len(norm_cell_text),
                        source_location=f"Table {t_idx} Row {r_idx} Col {c_idx}",
                    )
                    elements.append(elem)

        if not elements:
            raise EmptyDocumentError(str(file_path_obj))

        full_cleaned_text = "\n\n".join(e.text for e in elements if e.text)

        metadata = DocumentMetadata(
            filename=file_path_obj.name,
            file_path=str(file_path_obj),
            file_type=SourceType.DOCX,
            file_size_bytes=file_size_bytes,
            author=author,
            creation_date=created_dt,
            title=title,
            page_count=None,
            paragraph_count=paragraph_count,
            table_count=table_count,
            requires_ocr=False,
            ocr_reason=None,
            extraction_warnings=extraction_warnings,
        )

        return ExtractedDocument(
            document_id=doc_id,
            source_filename=file_path_obj.name,
            source_path=str(file_path_obj),
            source_type=SourceType.DOCX,
            metadata=metadata,
            elements=elements,
            full_cleaned_text=full_cleaned_text,
            requires_ocr=False,
        )
