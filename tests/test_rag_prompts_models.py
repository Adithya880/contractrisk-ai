"""
Unit Test Suite for RAG Prompts and Pydantic Models
"""

import pytest
from src.rag.models import Citation, RAGEvidenceItem, RAGResponse
from src.rag.prompts import RAG_SYSTEM_PROMPT, build_user_prompt


def test_rag_system_prompt_rules():
    assert "contract analysis decision-support assistant" in RAG_SYSTEM_PROMPT
    assert "insufficient_evidence" in RAG_SYSTEM_PROMPT
    assert "citations" in RAG_SYSTEM_PROMPT


def test_build_user_prompt():
    prompt = build_user_prompt("What is the rent?", "[Evidence 1]\n1.2 Rent is $5,000")
    assert "CONTRACT EVIDENCE:" in prompt
    assert "USER QUESTION:" in prompt
    assert "What is the rent?" in prompt


def test_rag_response_pydantic_serialization():
    ev = RAGEvidenceItem(
        clause_id="doc1:clause:001",
        document_id="doc1",
        clause_number="1.1",
        clause_heading="Definitions",
        clause_text="1.1 Definitions.",
        source_pages=[1],
        similarity_score=0.88,
    )
    cit = Citation(clause_id="doc1:clause:001", clause_number="1.1", source_pages=[1])

    resp = RAGResponse(
        query="What is defined?",
        answer="Premises is defined.",
        evidence=[ev],
        citations=[cit],
        insufficient_evidence=False,
        model_name="qwen3-4b-instruct-2507",
    )

    json_str = resp.model_dump_json()
    assert "qwen3-4b-instruct-2507" in json_str
    assert "doc1:clause:001" in json_str
