"""
Unit Test Suite for PDFExtractor Module
"""

import tempfile
from pathlib import Path
import fitz
import pytest

from src.document_processing.exceptions import CorruptedDocumentError
from src.document_processing.pdf_extractor import PDFExtractor
from src.document_processing.models import SourceType


@pytest.fixture
def sample_pdf_file():
    """Generates a synthetic 3-page PDF document."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    doc = fitz.open()
    # Page 1
    page1 = doc.new_page()
    page1.insert_text((50, 50), "SECTION 1. GOVERNING LAW\nThis Agreement shall be governed by California law.")
    # Page 2
    page2 = doc.new_page()
    page2.insert_text((50, 50), "SECTION 2. INDEMNIFICATION\nLicensor agrees to indemnify Licensee against claims.")
    # Page 3
    page3 = doc.new_page()
    page3.insert_text((50, 50), "IN WITNESS WHEREOF, the Parties have executed this Agreement.")
    
    doc.save(tmp_path)
    doc.close()
    
    yield tmp_path
    if tmp_path.exists():
        tmp_path.unlink()


@pytest.fixture
def pdf_with_empty_page():
    """Generates a synthetic PDF with an empty page."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    doc = fitz.open()
    p1 = doc.new_page()
    p1.insert_text((50, 50), "Valid clause text on page 1.")
    p2 = doc.new_page()  # Empty page
    
    doc.save(tmp_path)
    doc.close()
    
    yield tmp_path
    if tmp_path.exists():
        tmp_path.unlink()


@pytest.fixture
def scanned_pdf_mock():
    """Generates a synthetic PDF with minimal text to mock a scanned/image PDF."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    doc = fitz.open()
    p1 = doc.new_page()
    p1.insert_text((50, 50), "Scan")
    doc.save(tmp_path)
    doc.close()

    yield tmp_path
    if tmp_path.exists():
        tmp_path.unlink()


def test_pdf_multi_page_extraction(sample_pdf_file):
    extractor = PDFExtractor()
    doc = extractor.extract(sample_pdf_file)

    assert doc.source_type == SourceType.PDF
    assert doc.metadata.page_count == 3
    assert len(doc.elements) == 3
    assert doc.requires_ocr is False

    # Verify Page 1
    p1 = doc.elements[0]
    assert p1.page_number == 1
    assert "GOVERNING LAW" in p1.text
    assert p1.char_count > 0

    # Verify Page 2
    p2 = doc.elements[1]
    assert p2.page_number == 2
    assert "INDEMNIFICATION" in p2.text

    # Verify Page 3
    p3 = doc.elements[2]
    assert p3.page_number == 3
    assert "WITNESS" in p3.text


def test_pdf_empty_page_handling(pdf_with_empty_page):
    extractor = PDFExtractor()
    doc = extractor.extract(pdf_with_empty_page)

    assert doc.metadata.page_count == 2
    assert len(doc.elements) == 2
    assert doc.elements[1].char_count == 0
    assert len(doc.metadata.extraction_warnings) > 0


def test_pdf_scanned_detection(scanned_pdf_mock):
    extractor = PDFExtractor()
    doc = extractor.extract(scanned_pdf_mock)

    assert doc.requires_ocr is True
    assert doc.metadata.requires_ocr is True
    assert "below minimum threshold" in doc.metadata.ocr_reason


def test_pdf_corrupted_file():
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(b"NOT_A_REAL_PDF_HEADER_DATA")
        tmp_path = Path(tmp.name)

    extractor = PDFExtractor()
    with pytest.raises(CorruptedDocumentError):
        extractor.extract(tmp_path)

    if tmp_path.exists():
        tmp_path.unlink()


def test_pdf_missing_file():
    extractor = PDFExtractor()
    with pytest.raises(FileNotFoundError):
        extractor.extract("non_existent_file_xyz123.pdf")
