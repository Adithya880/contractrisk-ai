"""
Unit Test Suite for Main ClauseSegmenter Module
"""

import pytest
from src.clause_segmentation.segmenter import ClauseSegmenter
from src.document_processing.models import (
    DocumentElement,
    DocumentMetadata,
    ElementType,
    ExtractedDocument,
    SourceType,
)


def _build_mock_document(elements: list[DocumentElement], doc_id: str = "mock_doc_001") -> ExtractedDocument:
    metadata = DocumentMetadata(
        filename="contract.pdf",
        file_path="/tmp/contract.pdf",
        file_type=SourceType.PDF,
        file_size_bytes=1000,
        page_count=2,
    )
    full_text = "\n\n".join(e.text for e in elements if e.text)
    return ExtractedDocument(
        document_id=doc_id,
        source_filename="contract.pdf",
        source_path="/tmp/contract.pdf",
        source_type=SourceType.PDF,
        metadata=metadata,
        elements=elements,
        full_cleaned_text=full_text,
    )


def test_simple_numbered_clauses():
    elements = [
        DocumentElement(
            element_id="e1", element_type=ElementType.PARAGRAPH, text="1. DEFINITIONS",
            raw_text="1. DEFINITIONS", page_number=1, char_count=14, source_location="P1"
        ),
        DocumentElement(
            element_id="e2", element_type=ElementType.PARAGRAPH, text="Capitalized terms shall have meaning.",
            raw_text="Capitalized terms shall have meaning.", page_number=1, char_count=37, source_location="P1"
        ),
        DocumentElement(
            element_id="e3", element_type=ElementType.PARAGRAPH, text="2. CONFIDENTIALITY",
            raw_text="2. CONFIDENTIALITY", page_number=1, char_count=18, source_location="P1"
        ),
        DocumentElement(
            element_id="e4", element_type=ElementType.PARAGRAPH, text="Each party shall protect secrets.",
            raw_text="Each party shall protect secrets.", page_number=1, char_count=33, source_location="P1"
        ),
    ]

    doc = _build_mock_document(elements)
    segmenter = ClauseSegmenter()
    result = segmenter.segment(doc)

    assert result.total_clauses == 2
    assert result.clauses[0].clause_number == "1"
    assert "DEFINITIONS" in result.clauses[0].clause_text
    assert "Capitalized terms" in result.clauses[0].clause_text
    assert result.clauses[1].clause_number == "2"
    assert "CONFIDENTIALITY" in result.clauses[1].clause_text


def test_nested_numbering_and_hierarchy():
    elements = [
        DocumentElement(element_id="e1", element_type=ElementType.PARAGRAPH, text="4. GOVERNING LAW", raw_text="4. GOVERNING LAW", page_number=1, char_count=16, source_location="P1"),
        DocumentElement(element_id="e2", element_type=ElementType.PARAGRAPH, text="4.1 Choice of Venue", raw_text="4.1 Choice of Venue", page_number=1, char_count=19, source_location="P1"),
        DocumentElement(element_id="e3", element_type=ElementType.PARAGRAPH, text="4.1.1 Arbitration Rules", raw_text="4.1.1 Arbitration Rules", page_number=1, char_count=23, source_location="P1"),
    ]

    doc = _build_mock_document(elements)
    segmenter = ClauseSegmenter()
    result = segmenter.segment(doc)

    assert result.total_clauses == 3
    assert result.clauses[0].hierarchy_level == 1 and result.clauses[0].parent_clause_number is None
    assert result.clauses[1].hierarchy_level == 2 and result.clauses[1].parent_clause_number == "4"
    assert result.clauses[2].hierarchy_level == 3 and result.clauses[2].parent_clause_number == "4.1"


def test_lettered_subclauses():
    elements = [
        DocumentElement(element_id="e1", element_type=ElementType.PARAGRAPH, text="1.1 License Restrictions.", raw_text="1.1 License Restrictions.", page_number=1, char_count=25, source_location="P1"),
        DocumentElement(element_id="e2", element_type=ElementType.PARAGRAPH, text="(a) No reverse engineering.", raw_text="(a) No reverse engineering.", page_number=1, char_count=27, source_location="P1"),
        DocumentElement(element_id="e3", element_type=ElementType.PARAGRAPH, text="(b) No sublicensing.", raw_text="(b) No sublicensing.", page_number=1, char_count=20, source_location="P1"),
    ]

    doc = _build_mock_document(elements)
    segmenter = ClauseSegmenter()
    result = segmenter.segment(doc)

    assert result.total_clauses == 3
    assert result.clauses[1].clause_number == "(a)"
    assert result.clauses[1].parent_clause_number == "1.1"


def test_multi_page_clause_provenance():
    elements = [
        DocumentElement(element_id="e1", element_type=ElementType.PARAGRAPH, text="5. INDEMNIFICATION", raw_text="5. INDEMNIFICATION", page_number=1, char_count=18, source_location="P1"),
        DocumentElement(element_id="e2", element_type=ElementType.PARAGRAPH, text="Licensor agrees to defend licensee against third-party claims.", raw_text="Licensor agrees to defend licensee against third-party claims.", page_number=1, char_count=62, source_location="P1"),
        DocumentElement(element_id="e3", element_type=ElementType.PARAGRAPH, text="This obligation continues on page 2.", raw_text="This obligation continues on page 2.", page_number=2, char_count=36, source_location="P2"),
    ]

    doc = _build_mock_document(elements)
    segmenter = ClauseSegmenter()
    result = segmenter.segment(doc)

    assert result.total_clauses == 1
    c = result.clauses[0]
    assert c.source_pages == [1, 2]
    assert c.start_page == 1
    assert c.end_page == 2
    assert len(c.source_element_ids) == 3


def test_unnumbered_document():
    elements = [
        DocumentElement(element_id="e1", element_type=ElementType.PARAGRAPH, text="This Master Agreement is entered into by Acme and Client.", raw_text="This Master Agreement is entered into by Acme and Client.", page_number=1, char_count=57, source_location="P1"),
        DocumentElement(element_id="e2", element_type=ElementType.PARAGRAPH, text="Services shall be performed according to Statements of Work.", raw_text="Services shall be performed according to Statements of Work.", page_number=1, char_count=60, source_location="P1"),
    ]

    doc = _build_mock_document(elements)
    segmenter = ClauseSegmenter()
    result = segmenter.segment(doc)

    assert result.total_clauses >= 1
    assert result.clauses[0].clause_number is None
    assert result.clauses[0].clause_id == "mock_doc_001:clause:001"


def test_table_content_preservation():
    elements = [
        DocumentElement(element_id="e1", element_type=ElementType.PARAGRAPH, text="1. PRICING TABLE", raw_text="1. PRICING TABLE", page_number=1, char_count=16, source_location="P1"),
        DocumentElement(element_id="e2", element_type=ElementType.TABLE_CELL, text="Item A: $100", raw_text="Item A: $100", page_number=1, char_count=12, source_location="T0 R0 C0"),
    ]

    doc = _build_mock_document(elements)
    segmenter = ClauseSegmenter()
    result = segmenter.segment(doc)

    assert result.total_clauses == 1
    assert "Item A: $100" in result.clauses[0].clause_text


def test_repeated_header_footer_noise_filtering():
    elements = [
        DocumentElement(element_id="e1", element_type=ElementType.PARAGRAPH, text="Page 1 of 10", raw_text="Page 1 of 10", page_number=1, char_count=12, source_location="P1"),
        DocumentElement(element_id="e2", element_type=ElementType.PARAGRAPH, text="1. DEFINITIONS", raw_text="1. DEFINITIONS", page_number=1, char_count=14, source_location="P1"),
        DocumentElement(element_id="e3", element_type=ElementType.PARAGRAPH, text="Page 1 of 10", raw_text="Page 1 of 10", page_number=2, char_count=12, source_location="P2"),
        DocumentElement(element_id="e4", element_type=ElementType.PARAGRAPH, text="2. TERMINATION", raw_text="2. TERMINATION", page_number=2, char_count=14, source_location="P2"),
        DocumentElement(element_id="e5", element_type=ElementType.PARAGRAPH, text="Page 1 of 10", raw_text="Page 1 of 10", page_number=3, char_count=12, source_location="P3"),
    ]

    doc = _build_mock_document(elements)
    segmenter = ClauseSegmenter()
    result = segmenter.segment(doc)

    assert result.total_clauses == 2
    clause_texts = [c.clause_text for c in result.clauses]
    assert not any("Page 1 of 10" in t for t in clause_texts)


def test_deterministic_clause_ids():
    elements = [
        DocumentElement(element_id="e1", element_type=ElementType.PARAGRAPH, text="1. CLAUSE A", raw_text="1. CLAUSE A", page_number=1, char_count=11, source_location="P1"),
        DocumentElement(element_id="e2", element_type=ElementType.PARAGRAPH, text="2. CLAUSE B", raw_text="2. CLAUSE B", page_number=1, char_count=11, source_location="P1"),
    ]

    doc = _build_mock_document(elements, doc_id="custom_hash_123")
    segmenter = ClauseSegmenter()
    res1 = segmenter.segment(doc)
    res2 = segmenter.segment(doc)

    assert res1.clauses[0].clause_id == "custom_hash_123:clause:001"
    assert res1.clauses[1].clause_id == "custom_hash_123:clause:002"
    assert res1.clauses[0].clause_id == res2.clauses[0].clause_id
