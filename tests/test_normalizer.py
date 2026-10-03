"""
Unit Test Suite for Text Normalizer Module
"""

from src.document_processing.models import (
    DocumentElement,
    DocumentMetadata,
    ElementType,
    ExtractedDocument,
    SourceType,
)
from src.document_processing.normalizer import normalize_document, normalize_text


def test_whitespace_normalization():
    raw_input = "Section 1.1   Governing   Law.\t\tThis  is  a  test.\xa0Non-breaking space."
    result = normalize_text(raw_input)
    assert result == "Section 1.1 Governing Law. This is a test. Non-breaking space."


def test_smart_quotes_and_dashes():
    raw_input = "“Licensor” means ‘Acme Corp’ — a Delaware corporation."
    result = normalize_text(raw_input)
    assert result == '"Licensor" means \'Acme Corp\' - a Delaware corporation.'


def test_line_ending_normalization():
    raw_input = "Line 1\r\nLine 2\rLine 3\nLine 4"
    result = normalize_text(raw_input)
    assert result == "Line 1\nLine 2\nLine 3\nLine 4"


def test_consecutive_newline_capping():
    raw_input = "Paragraph 1\n\n\n\n\nParagraph 2"
    result = normalize_text(raw_input)
    assert result == "Paragraph 1\n\nParagraph 2"


def test_legal_numbering_preservation():
    raw_input = "12.1(a)(iii) Indemnification amount shall not exceed $1,000,000.00 USD."
    result = normalize_text(raw_input)
    assert result == "12.1(a)(iii) Indemnification amount shall not exceed $1,000,000.00 USD."


def test_normalize_document():
    raw_elem = DocumentElement(
        element_id="elem_1",
        element_type=ElementType.PARAGRAPH,
        text="“Smart  Quotes”  and\xa0spaces.",
        raw_text="“Smart  Quotes”  and\xa0spaces.",
        char_count=30,
        source_location="Paragraph 0",
    )

    metadata = DocumentMetadata(
        filename="test.docx",
        file_path="/tmp/test.docx",
        file_type=SourceType.DOCX,
        file_size_bytes=100,
    )

    doc = ExtractedDocument(
        document_id="doc1",
        source_filename="test.docx",
        source_path="/tmp/test.docx",
        source_type=SourceType.DOCX,
        metadata=metadata,
        elements=[raw_elem],
        full_cleaned_text="“Smart  Quotes”  and\xa0spaces.",
    )

    norm_doc = normalize_document(doc)
    assert norm_doc.elements[0].text == '"Smart Quotes" and spaces.'
    assert norm_doc.elements[0].raw_text == "“Smart  Quotes”  and\xa0spaces."
    assert norm_doc.full_cleaned_text == '"Smart Quotes" and spaces.'
