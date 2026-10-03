"""
Unit Test Suite for ContextBuilder Module
"""

import pytest
from src.rag.context_builder import ContextBuilder
from src.rag.models import RAGEvidenceItem


def test_context_builder_formatting():
    items = [
        RAGEvidenceItem(
            clause_id="doc1:clause:001",
            document_id="doc1",
            clause_number="1.1",
            clause_heading="Definitions",
            clause_text="1.1 Definitions. 'Premises' means Suite 400.",
            source_pages=[1, 2],
            similarity_score=0.8251,
        )
    ]

    builder = ContextBuilder()
    context = builder.build_context(items)

    assert "[Evidence 1]" in context
    assert "Clause ID: doc1:clause:001" in context
    assert "Clause Number: 1.1" in context
    assert "Source Page(s): 1, 2" in context
    assert "1.1 Definitions. 'Premises' means Suite 400." in context


def test_context_builder_budget_capping():
    items = [
        RAGEvidenceItem(
            clause_id=f"doc1:clause:{i:03d}",
            document_id="doc1",
            clause_number=f"{i}.0",
            clause_heading=f"Heading {i}",
            clause_text=f"{i}.0 Clause text repeat string " * 20,
            source_pages=[i],
            similarity_score=0.80,
        )
        for i in range(1, 10)
    ]

    # Set small budget of 1000 chars
    builder = ContextBuilder(max_char_budget=1000)
    context = builder.build_context(items)

    assert "[Evidence 1]" in context
    assert len(context) <= 1500
    # Should contain fewer than 9 evidence items due to budget capping
    assert "[Evidence 9]" not in context
