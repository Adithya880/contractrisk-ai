# Phase 4 Document Processing Technical Report

> **System**: ContractRisk AI  
> **Phase**: Phase 4 — Document Ingestion, Structural Extraction & Text Normalization  
> **Environment**: Python 3.11 (`.venv`), PyMuPDF (`fitz`), `python-docx`, Pydantic v2  

---

## 1. Phase 4 Objective

The objective of Phase 4 is to construct a modular, deterministic document ingestion pipeline capable of extracting structured content and metadata from **PDF** (`.pdf`) and Microsoft Word (**DOCX**, `.docx`) contracts. The pipeline converts raw binary files into a standardized, strongly-typed internal representation (`ExtractedDocument`) designed for direct consumption by Phase 5 (Clause Segmentation).

---

## 2. Implemented Modules & Architecture

The document processing framework is housed under `src/document_processing/`:

```
src/
  document_processing/
    __init__.py          # Package exports & public API
    models.py            # Pydantic v2 schemas (ExtractedDocument, DocumentElement, DocumentMetadata)
    exceptions.py        # Exception hierarchy for file, format, and corruption errors
    normalizer.py        # Conservative text cleaner preserving legal punctuation/numbering
    pdf_extractor.py     # PyMuPDF-based PDF page text & metadata extractor
    docx_extractor.py    # python-docx based paragraph, heading & table cell extractor
    loader.py            # Unified DocumentLoader facade
```

---

## 3. Supported Formats & Extraction Approach

| Format | Library | Extracted Elements | Structural Features Preserved |
| :--- | :--- | :--- | :--- |
| **PDF** (`.pdf`) | PyMuPDF (`fitz`) | Page text, Page numbers (1-indexed), Char counts | Page boundaries, total pages, author, title |
| **DOCX** (`.docx`) | `python-docx` | Paragraphs, Headings, Table cells | Heading levels (1-6), 0-indexed paragraph indices, table/row/col indices |

### Scanned / Image PDF Detection
Phase 4 implements automatic scanned PDF detection. If total extracted text across all pages is under **50 characters**, the document is flagged with:
- `requires_ocr = True`
- `ocr_reason = "Total extracted text length (<50 chars) is below minimum threshold. Document appears scanned or image-only."`

---

## 4. Output Data Model (`ExtractedDocument`)

The extraction pipeline produces a strongly-typed Pydantic model (`ExtractedDocument`):

```json
{
  "document_id": "592c24fca44c3514",
  "source_filename": "sample_contract.pdf",
  "source_path": "C:\\path\\to\\sample_contract.pdf",
  "source_type": "pdf",
  "metadata": {
    "filename": "sample_contract.pdf",
    "file_path": "C:\\path\\to\\sample_contract.pdf",
    "file_type": "pdf",
    "file_size_bytes": 10420,
    "page_count": 2,
    "requires_ocr": false,
    "ocr_reason": null,
    "extraction_warnings": []
  },
  "elements": [
    {
      "element_id": "592c24fca44c3514_page_1",
      "element_type": "page_text",
      "text": "MASTER SOFTWARE LICENSE AGREEMENT...",
      "raw_text": "MASTER SOFTWARE LICENSE AGREEMENT...",
      "page_number": 1,
      "char_count": 312,
      "source_location": "Page 1"
    }
  ],
  "full_cleaned_text": "MASTER SOFTWARE LICENSE AGREEMENT...\n\n2. LIMITATION OF LIABILITY...",
  "requires_ocr": false
}
```

---

## 5. Text Normalization Rules

Text normalization (`src/document_processing/normalizer.py`) is strictly conservative:

1. **Space Normalization**: Non-breaking spaces (`\xa0`) and zero-width spaces (`\u200b`) converted to standard spaces.
2. **Quote & Dash Standardization**: Smart quotes (`“`, `”`, `‘`, `’`) converted to ASCII (`"`, `'`); em/en-dashes (`—`, `–`) converted to `-`.
3. **Line Ending Standardization**: `\r\n` and `\r` normalized to standard `\n`.
4. **Horizontal Whitespace Collapsing**: Multiple consecutive spaces per line collapsed to a single space.
5. **Paragraph Separation Preservation**: Consecutive newlines capped at maximum 2 (`\n\n`) to preserve paragraph structure.
6. **Legal Formatting Preservation**: Legal clause numbering (e.g. `Section 12.1(a)(iii)`), monetary amounts (`$500,000.00`), and punctuation remain untouched.

---

## 6. Error Handling & Exception Hierarchy

Custom exceptions inherit from `DocumentProcessingError`:

- `UnsupportedFileTypeError`: Raised when attempting to load unsupported formats (e.g., `.txt`, `.jpg`, `.csv`).
- `CorruptedDocumentError`: Raised when PyMuPDF or `python-docx` fails to open a damaged/corrupt binary file.
- `EmptyDocumentError`: Raised when a document contains 0 pages, 0 paragraphs, or 0 extractable text characters.
- `FileNotFoundError`: Standard Python error raised if the specified input file path does not exist.

---

## 7. OCR Limitation

> [!IMPORTANT]
> **OCR Out of Scope**: Optical Character Recognition (OCR) is **NOT** implemented in Phase 4. Image-based or scanned contracts without an embedded text layer will be flagged (`requires_ocr = True`), allowing downstream systems or human review pipelines to route them to external OCR engines.

---

## 8. Test Suite & Verification Results

### Unit Test Execution (`pytest`)
All **20 unit tests** passed cleanly in **3.22 seconds**:

```
tests/test_docx_extractor.py::test_docx_paragraph_and_heading_extraction PASSED
tests/test_docx_extractor.py::test_docx_table_extraction PASSED
tests/test_docx_extractor.py::test_docx_empty_file PASSED
tests/test_docx_extractor.py::test_docx_corrupted_file PASSED
tests/test_docx_extractor.py::test_docx_missing_file PASSED
tests/test_loader.py::test_loader_pdf PASSED
tests/test_loader.py::test_loader_docx PASSED
tests/test_loader.py::test_loader_unsupported_file_type PASSED
tests/test_loader.py::test_loader_file_not_found PASSED
tests/test_normalizer.py::test_whitespace_normalization PASSED
tests/test_normalizer.py::test_smart_quotes_and_dashes PASSED
tests/test_normalizer.py::test_line_ending_normalization PASSED
tests/test_normalizer.py::test_consecutive_newline_capping PASSED
tests/test_normalizer.py::test_legal_numbering_preservation PASSED
tests/test_normalizer.py::test_normalize_document PASSED
tests/test_pdf_extractor.py::test_pdf_multi_page_extraction PASSED
tests/test_pdf_extractor.py::test_pdf_empty_page_handling PASSED
tests/test_pdf_extractor.py::test_pdf_scanned_detection PASSED
tests/test_pdf_extractor.py::test_pdf_corrupted_file PASSED
tests/test_pdf_extractor.py::test_pdf_missing_file PASSED

============================= 20 passed in 3.22s ==============================
```

### CLI Smoke Test Script (`scripts/test_document_processing.py`)
- **PDF Extraction**: 2 pages, 557 characters extracted successfully.
- **DOCX Extraction**: 6 paragraphs, 1 table, 628 characters extracted successfully.
- **Pydantic JSON Serialization**: Verified valid schema export.
- **Error Handling**: `FileNotFoundError`, `UnsupportedFileTypeError`, `CorruptedDocumentError` verified.

---

## 9. Limitations & Caveats

1. **Complex PDF Layouts**: PDFs with multi-column text or complex visual sidebars are extracted stream-wise by PyMuPDF; visual bounding box reconstruction is omitted.
2. **Advanced Table Formatting**: DOCX table cell content is extracted sequentially by row and column; nested table structures or cell merging details are flattened into linear cell text elements.
3. **No Image OCR**: Scanned document text cannot be extracted without an OCR extension phase.

---

## 10. Summary of Files Created & Modified

### Files Created
- [exceptions.py](file:///C:/Users/adith/Desktop/BEING%20CODER/AI%20CLAUSE%20ANALYSER/src/document_processing/exceptions.py)
- [models.py](file:///C:/Users/adith/Desktop/BEING%20CODER/AI%20CLAUSE%20ANALYSER/src/document_processing/models.py)
- [normalizer.py](file:///C:/Users/adith/Desktop/BEING%20CODER/AI%20CLAUSE%20ANALYSER/src/document_processing/normalizer.py)
- [pdf_extractor.py](file:///C:/Users/adith/Desktop/BEING%20CODER/AI%20CLAUSE%20ANALYSER/src/document_processing/pdf_extractor.py)
- [docx_extractor.py](file:///C:/Users/adith/Desktop/BEING%20CODER/AI%20CLAUSE%20ANALYSER/src/document_processing/docx_extractor.py)
- [loader.py](file:///C:/Users/adith/Desktop/BEING%20CODER/AI%20CLAUSE%20ANALYSER/src/document_processing/loader.py)
- [__init__.py](file:///C:/Users/adith/Desktop/BEING%20CODER/AI%20CLAUSE%20ANALYSER/src/document_processing/__init__.py)
- [test_pdf_extractor.py](file:///C:/Users/adith/Desktop/BEING%20CODER/AI%20CLAUSE%20ANALYSER/tests/test_pdf_extractor.py)
- [test_docx_extractor.py](file:///C:/Users/adith/Desktop/BEING%20CODER/AI%20CLAUSE%20ANALYSER/tests/test_docx_extractor.py)
- [test_normalizer.py](file:///C:/Users/adith/Desktop/BEING%20CODER/AI%20CLAUSE%20ANALYSER/tests/test_normalizer.py)
- [test_loader.py](file:///C:/Users/adith/Desktop/BEING%20CODER/AI%20CLAUSE%20ANALYSER/tests/test_loader.py)
- [test_document_processing.py](file:///C:/Users/adith/Desktop/BEING%20CODER/AI%20CLAUSE%20ANALYSER/scripts/test_document_processing.py)
- [DOCUMENT_PROCESSING_REPORT.md](file:///C:/Users/adith/Desktop/BEING%20CODER/AI%20CLAUSE%20ANALYSER/docs/DOCUMENT_PROCESSING_REPORT.md)

### Files Modified
- [requirements.txt](file:///C:/Users/adith/Desktop/BEING%20CODER/AI%20CLAUSE%20ANALYSER/requirements.txt) (Appended missing Phase 4 dependencies: `pymupdf`, `python-docx`, `pytest`)
