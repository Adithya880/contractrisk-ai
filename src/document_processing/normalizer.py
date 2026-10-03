"""
Text Normalization Module for ContractRisk AI

Provides conservative text cleaning and normalization for extracted contract text,
standardizing whitespace, line endings, quotes, and punctuation while strictly
preserving legal numbering, formatting, and structural paragraph/page boundaries.
"""

import re
from src.document_processing.models import ExtractedDocument, DocumentElement


def normalize_text(text: str) -> str:
    """
    Performs conservative text normalization on a raw string.

    Rules applied:
    1. Replaces non-breaking spaces (\\xa0) and zero-width spaces with standard spaces.
    2. Standardizes curly/smart quotes (“ ” ‘ ’) and dashes (— –) to standard ASCII equivalents.
    3. Normalizes line endings (\\r\\n and \\r to \\n).
    4. Replaces tab characters with spaces.
    5. Collapses horizontal spaces per line (multiple spaces -> single space).
    6. Trims trailing/leading whitespace per line.
    7. Limits consecutive newlines to maximum 2 (preserving structural paragraph breaks).
    8. Preserves all legal numbering, bullet points, and legal punctuation.
    """
    if not text:
        return ""

    # 1. Non-breaking and special space replacement
    cleaned = text.replace("\xa0", " ").replace("\u200b", "").replace("\ufeff", "")

    # 2. Smart quotes and special dashes replacement
    quote_dash_map = {
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "`": "'",
        "—": "-",
        "–": "-",
        "―": "-",
    }
    for char, replacement in quote_dash_map.items():
        cleaned = cleaned.replace(char, replacement)

    # 3. Line ending normalization
    cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")

    # 4. Tab normalization
    cleaned = cleaned.replace("\t", " ")

    # 5. Horizontal space collapsing per line
    lines = cleaned.split("\n")
    normalized_lines = [re.sub(r" +", " ", line).strip() for line in lines]
    cleaned = "\n".join(normalized_lines)

    # 6. Collapse consecutive newlines to maximum 2
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    return cleaned.strip()


def normalize_document(doc: ExtractedDocument) -> ExtractedDocument:
    """
    Applies text normalization to all elements within an ExtractedDocument instance
    and re-aggregates the document's full cleaned text.
    """
    updated_elements: list[DocumentElement] = []

    for elem in doc.elements:
        norm_text = normalize_text(elem.text)
        # Create updated element preserving original raw_text and provenance
        updated_elem = DocumentElement(
            element_id=elem.element_id,
            element_type=elem.element_type,
            text=norm_text,
            raw_text=elem.raw_text,
            page_number=elem.page_number,
            paragraph_index=elem.paragraph_index,
            heading_level=elem.heading_level,
            table_index=elem.table_index,
            row_index=elem.row_index,
            col_index=elem.col_index,
            char_count=len(norm_text),
            source_location=elem.source_location,
        )
        updated_elements.append(updated_elem)

    # Re-aggregate full cleaned text with double newline structural separators
    non_empty_texts = [e.text for e in updated_elements if e.text]
    full_text = "\n\n".join(non_empty_texts)

    # Reconstruct document model with updated elements and full text
    return ExtractedDocument(
        document_id=doc.document_id,
        source_filename=doc.source_filename,
        source_path=doc.source_path,
        source_type=doc.source_type,
        metadata=doc.metadata,
        elements=updated_elements,
        full_cleaned_text=full_text,
        requires_ocr=doc.requires_ocr,
    )
