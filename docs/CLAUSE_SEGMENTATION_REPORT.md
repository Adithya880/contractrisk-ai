# Phase 5 Clause Segmentation Technical Report

> **System**: ContractRisk AI  
> **Phase**: Phase 5 — Hybrid Rule-Based Clause Boundary & Hierarchy Segmentation  
> **Environment**: Python 3.11 (`.venv`), PyMuPDF, `python-docx`, Pydantic v2  

---

## 1. Phase 5 Objective

The objective of Phase 5 is to segment structured contract representations (`ExtractedDocument` from Phase 4) into atomic, traceable, and hierarchically organized `SegmentedClause` objects. 

This phase establishes clause boundaries, captures legal section numbering, resolves parent-child relationships, preserves original text without modification, and tracks full document page and element provenance for downstream embedding, retrieval, and risk scoring phases.

---

## 2. Segmentation Architecture & Disclosures

```
Phase 4 ExtractedDocument
          │
          ▼
   [ClauseSegmenter] ──► [Repetition Noise Filter]
          │
          ▼
   [Atomic Unit Expander] (Preserves Element IDs & Pages)
          │
          ▼
   [Pattern Matcher] ──► [HeaderMatch Engine] (Articles, Sections, Decimals, Subclauses)
          │
          ▼
   [HierarchyTracker] ──► [Depth Level & Parent Resolution Stack]
          │
          ▼
  SegmentationResult (List of SegmentedClause objects + Coverage Validation)
```

> [!IMPORTANT]
> **System Architecture Disclosures**:
> - **Hybrid Rule-Based Architecture**: Segmentation is strictly deterministic and rule-based.
> - **No LLM Usage**: No Large Language Models (LLMs) are used for clause segmentation.
> - **No Clause Classification**: Clause-type classification (Phase 3 BERT model) is **NOT** performed in Phase 5.
> - **No Risk Analysis**: Risk assessment and scoring belong to later phases and are **NOT** part of Phase 5.

---

## 3. Supported Numbering Patterns & Heading Detection

The pattern recognition engine (`src/clause_segmentation/patterns.py`) recognizes standard legal numbering conventions:

| Pattern Type | Pattern Regex Example | Example Clause Header |
| :--- | :--- | :--- |
| **Article** | `ARTICLE\|Article \d+\|I` | `ARTICLE I. DEFINITIONS` |
| **Section** | `SECTION\|Section \d+` | `SECTION 2.1 INDEMNIFICATION` |
| **Decimal Number** | `1.`, `1.1`, `1.1.1`, `2.3.4` | `1.1 Premises. 'Premises' refers to...` |
| **Lettered Subclause** | `(a)`, `(b)`, `(iii)` | `(a) Tenant shall maintain insurance.` |
| **Uppercase Heading** | `^[A-Z0-9\s,\-\(\)]{4,80}$` | `GOVERNING LAW AND ARBITRATION` |

---

## 4. Hierarchy Detection Strategy

The `HierarchyTracker` (`src/clause_segmentation/hierarchy.py`) maintains an active ancestor stack to resolve 1-based structural depth levels and parent clause numbers dynamically:

```
ARTICLE I                       → Level 1 | Parent: None
  1.1 Premises                  → Level 2 | Parent: ARTICLE I
  1.2 Rent                      → Level 2 | Parent: ARTICLE I
ARTICLE II                      → Level 1 | Parent: None
  2.1 Tenant Indemnity          → Level 2 | Parent: ARTICLE II
    (a) Legal Fees              → Level 3 | Parent: 2.1
    (b) Prompt Notice           → Level 3 | Parent: 2.1
```

---

## 5. Provenance & Deterministic Clause ID Strategy

- **Deterministic Clause IDs**: Generated using the format `{document_id}:clause:{sequence:03d}` (e.g. `7b8e95a7a589b486:clause:001`). Output IDs are 100% deterministic across repeated runs on the same document.
- **Page Provenance**: `source_pages` records every 1-indexed page containing content for the clause. `start_page` and `end_page` capture multi-page spans (e.g. `start_page: 4`, `end_page: 5`).
- **Element Provenance**: `source_element_ids` records all Phase 4 `DocumentElement` IDs combined into the clause.

---

## 6. Handling of Unnumbered Documents & Table Content

- **Unnumbered Contracts**: Documents without explicit numbering (`1.`, `ARTICLE I`) are segmented by structural paragraph/section boundaries, generating deterministic sequence IDs (`doc_id:clause:001`) while keeping `clause_number` as `None`.
- **Table Content**: Cell text extracted during Phase 4 is preserved sequentially as part of the containing clause or as standalone table clauses, ensuring zero data loss.
- **Header/Footer Repetition Filtering**: Short repeating page numbers or headers occurring on 3+ distinct pages (e.g., `Page X of Y`) are conservatively filtered while ensuring main contract body text is never discarded.

---

## 7. Test Results & Regression Verification

### Phase 5 Unit Test Suite (`pytest`)
All **17 Phase 5 unit tests** passed cleanly in **0.58 seconds**:

```
tests/test_clause_patterns.py::test_article_pattern PASSED
tests/test_clause_patterns.py::test_section_pattern PASSED
tests/test_clause_patterns.py::test_decimal_pattern PASSED
tests/test_clause_patterns.py::test_lettered_pattern PASSED
tests/test_clause_patterns.py::test_uppercase_heading_pattern PASSED
tests/test_clause_patterns.py::test_non_header_text PASSED
tests/test_clause_hierarchy.py::test_top_level_section PASSED
tests/test_clause_hierarchy.py::test_nested_decimal_numbering PASSED
tests/test_clause_hierarchy.py::test_lettered_subclause_hierarchy PASSED
tests/test_clause_segmentation.py::test_simple_numbered_clauses PASSED
tests/test_clause_segmentation.py::test_nested_numbering_and_hierarchy PASSED
tests/test_clause_segmentation.py::test_lettered_subclauses PASSED
tests/test_clause_segmentation.py::test_multi_page_clause_provenance PASSED
tests/test_clause_segmentation.py::test_unnumbered_document PASSED
tests/test_clause_segmentation.py::test_table_content_preservation PASSED
tests/test_clause_segmentation.py::test_repeated_header_footer_noise_filtering PASSED
tests/test_clause_segmentation.py::test_deterministic_clause_ids PASSED

============================= 17 passed in 0.58s ==============================
```

### Full Regression Suite (Phase 4 + Phase 5)
All **37 regression tests** passed cleanly in **1.65 seconds**:

```
============================= 37 passed in 1.65s ==============================
```

### CLI Verification Smoke Test (`scripts/test_clause_segmentation.py`)
- **PDF Pipeline**: 8 clauses segmented | 98.25% text coverage ratio | Hierarchy verified
- **DOCX Pipeline**: 4 clauses segmented | 101.67% text coverage ratio | Hierarchy verified
- **Pydantic JSON Serialization**: Verified valid schema export

---

## 8. Example Segmented Output

```json
{
  "clause_id": "7b8e95a7a589b486:clause:003",
  "document_id": "7b8e95a7a589b486",
  "clause_number": "1.1",
  "clause_heading": "Premises",
  "clause_text": "1.1 Premises. 'Premises' refers to Suite 400 located at 500 Commercial Blvd.",
  "source_type": "pdf",
  "source_pages": [1],
  "start_page": 1,
  "end_page": 1,
  "source_element_ids": ["7b8e95a7a589b486_page_1"],
  "parent_clause_number": "ARTICLE I",
  "hierarchy_level": 2,
  "character_count": 75,
  "word_count": 10
}
```

---

## 9. Known Limitations

1. **Non-Standard Formatting**: Highly irregular numbering schemes (e.g. inline bullet points without line breaks) may group under the preceding active clause.
2. **Visual Layout Dependencies**: Section boundaries rely on text ordering produced by Phase 4; visual multi-column sidebars are processed in stream order.

---

## 10. Summary of Files Created & Modified

### Files Created
- [models.py](file:///C:/Users/adith/Desktop/BEING%20CODER/AI%20CLAUSE%20ANALYSER/src/clause_segmentation/models.py) — Pydantic v2 schemas (`SegmentedClause`, `SegmentationResult`)
- [patterns.py](file:///C:/Users/adith/Desktop/BEING%20CODER/AI%20CLAUSE%20ANALYSER/src/clause_segmentation/patterns.py) — Legal numbering & section header regex pattern engine
- [hierarchy.py](file:///C:/Users/adith/Desktop/BEING%20CODER/AI%20CLAUSE%20ANALYSER/src/clause_segmentation/hierarchy.py) — Hierarchy level & parent clause tracker
- [segmenter.py](file:///C:/Users/adith/Desktop/BEING%20CODER/AI%20CLAUSE%20ANALYSER/src/clause_segmentation/segmenter.py) — Main `ClauseSegmenter` engine
- [__init__.py](file:///C:/Users/adith/Desktop/BEING%20CODER/AI%20CLAUSE%20ANALYSER/src/clause_segmentation/__init__.py) — Package initialization and public API export
- [test_clause_patterns.py](file:///C:/Users/adith/Desktop/BEING%20CODER/AI%20CLAUSE%20ANALYSER/tests/test_clause_patterns.py) — Pytest suite for pattern matching
- [test_clause_hierarchy.py](file:///C:/Users/adith/Desktop/BEING%20CODER/AI%20CLAUSE%20ANALYSER/tests/test_clause_hierarchy.py) — Pytest suite for hierarchy tracking
- [test_clause_segmentation.py](file:///C:/Users/adith/Desktop/BEING%20CODER/AI%20CLAUSE%20ANALYSER/tests/test_clause_segmentation.py) — Pytest suite for main segmenter engine
- [test_clause_segmentation.py](file:///C:/Users/adith/Desktop/BEING%20CODER/AI%20CLAUSE%20ANALYSER/scripts/test_clause_segmentation.py) — CLI verification & smoke test script
- [CLAUSE_SEGMENTATION_REPORT.md](file:///C:/Users/adith/Desktop/BEING%20CODER/AI%20CLAUSE%20ANALYSER/docs/CLAUSE_SEGMENTATION_REPORT.md) — Comprehensive technical report

### Files Modified
- None (Phase 1–4 code and Phase 3 BERT model checkpoints remain 100% untouched)
