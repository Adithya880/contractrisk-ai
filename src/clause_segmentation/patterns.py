"""
Pattern Recognition Module for Contract Clause Boundaries

Provides regex patterns and matching routines to detect legal section headers,
articles, decimal numbering, lettered subclauses, and uppercase headings.
"""

import re
from typing import NamedTuple, Optional


class HeaderMatch(NamedTuple):
    """Encapsulates information extracted from a detected clause header."""
    clause_number: Optional[str]
    clause_heading: Optional[str]
    body_text: str
    pattern_type: str


# Regex Pattern Declarations
_ARTICLE_RE = re.compile(
    r"^(?:ARTICLE|Article)\s+([IVXLCDM\d]+)(?:\s*[:.\-—]?\s*(.*))?$",
    re.IGNORECASE
)

_SECTION_RE = re.compile(
    r"^(?:SECTION|Section)\s+([\d.]+)(?:\s*[:.\-—]?\s*(.*))?$",
    re.IGNORECASE
)

# Decimal numbering: e.g. "1. DEFINITIONS", "1.1 Confidentiality", "1.2.1 Scope"
_DECIMAL_RE = re.compile(
    r"^(\d+(?:\.\d+)*)\.?\s*[:.\-—]?\s*(.*)$"
)

# Lettered/Roman numeral subclauses: e.g. "(a) Text", "(b)", "(i) Text"
_LETTERED_RE = re.compile(
    r"^\(([a-zA-Z]|\d+|[ivxlcdmIVXLCDM]+)\)\s*(.*)$"
)

# Uppercase standalone headings: e.g. "CONFIDENTIALITY AND NON-DISCLOSURE"
_UPPERCASE_HEADING_RE = re.compile(
    r"^([A-Z0-9\s,\-\(\)&]{4,80})$"
)


def detect_clause_header(text: str) -> Optional[HeaderMatch]:
    """
    Analyzes a string (typically the first line or entire text of a paragraph/element)
    to determine if it starts a new legal clause or section.

    Returns:
        HeaderMatch if a header pattern is matched, otherwise None.
    """
    if not text or not text.strip():
        return None

    stripped = text.strip()
    first_line = stripped.split("\n")[0].strip()

    # 1. ARTICLE Pattern (e.g., "ARTICLE 1. DEFINITIONS" or "ARTICLE I")
    m_article = _ARTICLE_RE.match(first_line)
    if m_article:
        num = f"ARTICLE {m_article.group(1)}"
        rest = m_article.group(2) or ""
        heading, body = _split_heading_body(rest, is_lettered=False)
        return HeaderMatch(
            clause_number=num,
            clause_heading=heading,
            body_text=body,
            pattern_type="article"
        )

    # 2. SECTION Pattern (e.g., "SECTION 2.1 INDEMNIFICATION")
    m_section = _SECTION_RE.match(first_line)
    if m_section:
        num = f"SECTION {m_section.group(1)}"
        rest = m_section.group(2) or ""
        heading, body = _split_heading_body(rest, is_lettered=False)
        return HeaderMatch(
            clause_number=num,
            clause_heading=heading,
            body_text=body,
            pattern_type="section"
        )

    # 3. Decimal Number Pattern (e.g., "1.1 Confidentiality. The parties agree...")
    m_decimal = _DECIMAL_RE.match(first_line)
    if m_decimal:
        num = m_decimal.group(1)
        rest = m_decimal.group(2) or ""
        heading, body = _split_heading_body(rest, is_lettered=False)
        return HeaderMatch(
            clause_number=num,
            clause_heading=heading,
            body_text=body,
            pattern_type="decimal"
        )

    # 4. Lettered Subclause Pattern (e.g., "(a) Licensee shall not reverse engineer.")
    m_lettered = _LETTERED_RE.match(first_line)
    if m_lettered:
        num = f"({m_lettered.group(1)})"
        rest = m_lettered.group(2) or ""
        heading, body = _split_heading_body(rest, is_lettered=True)
        return HeaderMatch(
            clause_number=num,
            clause_heading=heading,
            body_text=body,
            pattern_type="lettered"
        )

    # 5. Standalone Uppercase Heading (e.g., "CONFIDENTIALITY")
    if len(first_line) <= 80 and _UPPERCASE_HEADING_RE.match(first_line) and not first_line.endswith("."):
        words = first_line.split()
        if len(words) <= 8 and any(c.isalpha() for c in first_line):
            rest_of_text = "\n".join(stripped.split("\n")[1:]) if "\n" in stripped else ""
            return HeaderMatch(
                clause_number=None,
                clause_heading=first_line,
                body_text=rest_of_text,
                pattern_type="uppercase_heading"
            )

    return None


def _split_heading_body(text: str, is_lettered: bool = False) -> tuple[Optional[str], str]:
    """
    Separates a heading title from the subsequent body text.
    """
    if not text:
        return None, ""

    # Check for inline period/colon delimiter, e.g. "Definitions. The following terms..."
    delims = [". ", ": ", " - ", " – "]
    for d in delims:
        if d in text:
            parts = text.split(d, 1)
            heading = parts[0].strip()
            body = parts[1].strip()
            if len(heading.split()) <= 10:
                return heading, body

    if is_lettered:
        # Lettered subclauses without delimiter are treated as body text
        return None, text.strip()

    # If short text without delimiter (e.g., "DEFINITIONS"), treat as heading
    if len(text.split()) <= 8 and len(text) <= 60 and not text.endswith("."):
        return text.strip(), ""

    return None, text.strip()
