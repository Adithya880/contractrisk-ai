"""
Unit Test Suite for Clause Pattern Recognition Module
"""

import pytest
from src.clause_segmentation.patterns import detect_clause_header


def test_article_pattern():
    header = detect_clause_header("ARTICLE I. DEFINITIONS")
    assert header is not None
    assert header.clause_number == "ARTICLE I"
    assert header.clause_heading == "DEFINITIONS"
    assert header.pattern_type == "article"

    header2 = detect_clause_header("Article 2 - Scope of Agreement")
    assert header2 is not None
    assert header2.clause_number == "ARTICLE 2"
    assert header2.clause_heading == "Scope of Agreement"


def test_section_pattern():
    header = detect_clause_header("SECTION 1.1 INDEMNIFICATION")
    assert header is not None
    assert header.clause_number == "SECTION 1.1"
    assert header.clause_heading == "INDEMNIFICATION"
    assert header.pattern_type == "section"


def test_decimal_pattern():
    header = detect_clause_header("1.1 Confidentiality. Each party shall keep secrets.")
    assert header is not None
    assert header.clause_number == "1.1"
    assert header.clause_heading == "Confidentiality"
    assert header.body_text == "Each party shall keep secrets."
    assert header.pattern_type == "decimal"

    header2 = detect_clause_header("1.2.1 Scope of License")
    assert header2 is not None
    assert header2.clause_number == "1.2.1"
    assert header2.clause_heading == "Scope of License"


def test_lettered_pattern():
    header = detect_clause_header("(a) Licensee shall not reverse engineer.")
    assert header is not None
    assert header.clause_number == "(a)"
    assert header.body_text == "Licensee shall not reverse engineer."
    assert header.pattern_type == "lettered"


def test_uppercase_heading_pattern():
    header = detect_clause_header("GOVERNING LAW AND JURISDICTION")
    assert header is not None
    assert header.clause_number is None
    assert header.clause_heading == "GOVERNING LAW AND JURISDICTION"
    assert header.pattern_type == "uppercase_heading"


def test_non_header_text():
    assert detect_clause_header("This is a standard paragraph of contract text that continues across lines.") is None
    assert detect_clause_header("the party of the first part hereby agrees to the following conditions:") is None
