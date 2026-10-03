"""
Unit Test Suite for DocumentLoader Facade Module
"""

import tempfile
from pathlib import Path
import docx
import fitz
import pytest

from src.document_processing.exceptions import UnsupportedFileTypeError
from src.document_processing.loader import DocumentLoader
from src.document_processing.models import SourceType


@pytest.fixture
def temp_pdf():
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    doc = fitz.open()
    p = doc.new_page()
    p.insert_text((50, 50), "PDF Document Facade Loader Test.")
    doc.save(tmp_path)
    doc.close()

    yield tmp_path
    if tmp_path.exists():
        tmp_path.unlink()


@pytest.fixture
def temp_docx():
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    doc = docx.Document()
    doc.add_paragraph("DOCX Document Facade Loader Test.")
    doc.save(tmp_path)

    yield tmp_path
    if tmp_path.exists():
        tmp_path.unlink()


@pytest.fixture
def temp_txt():
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
        tmp.write(b"Plain text file content.")
        tmp_path = Path(tmp.name)

    yield tmp_path
    if tmp_path.exists():
        tmp_path.unlink()


def test_loader_pdf(temp_pdf):
    loader = DocumentLoader()
    doc = loader.load_document(temp_pdf)

    assert doc.source_type == SourceType.PDF
    assert "PDF Document Facade Loader Test." in doc.full_cleaned_text


def test_loader_docx(temp_docx):
    loader = DocumentLoader()
    doc = loader.load_document(temp_docx)

    assert doc.source_type == SourceType.DOCX
    assert "DOCX Document Facade Loader Test." in doc.full_cleaned_text


def test_loader_unsupported_file_type(temp_txt):
    loader = DocumentLoader()
    with pytest.raises(UnsupportedFileTypeError):
        loader.load_document(temp_txt)


def test_loader_file_not_found():
    loader = DocumentLoader()
    with pytest.raises(FileNotFoundError):
        loader.load_document("missing_contract_file_12345.pdf")
