"""
Grounding Validator Module for ContractRisk AI RAG Pipeline

Performs lightweight deterministic validation on LLM generation output:
verifying that cited clause IDs exist in retrieved evidence and enforcing
insufficient-evidence consistency.
"""

from typing import List, Tuple
from src.rag.models import Citation, RAGEvidenceItem


def validate_grounding(
    raw_response: dict, evidence_items: List[RAGEvidenceItem]
) -> Tuple[str, List[Citation], bool]:
    """
    Validates evidence citations and grounding consistency of an LLM generation dictionary.

    Args:
        raw_response: Parsed JSON dict from LLMGenerator containing 'answer', 'citations', 'insufficient_evidence'.
        evidence_items: List of RAGEvidenceItem objects actually retrieved.

    Returns:
        Tuple of (validated_answer: str, validated_citations: List[Citation], insufficient_evidence: bool)
    """
    insufficient_evidence = bool(raw_response.get("insufficient_evidence", False))
    raw_answer = str(raw_response.get("answer", "")).strip()

    # 1. No evidence available check
    if not evidence_items:
        return (
            "The retrieved contract evidence is insufficient to answer this question.",
            [],
            True,
        )

    # Map available clause IDs for quick lookup
    evidence_map = {item.clause_id: item for item in evidence_items}

    raw_citations = raw_response.get("citations", [])
    validated_citations: list[Citation] = []

    if isinstance(raw_citations, list):
        for c in raw_citations:
            if not isinstance(c, dict):
                continue
            clause_id = c.get("clause_id")
            # Verify cited clause ID actually exists in retrieved evidence
            if clause_id and clause_id in evidence_map:
                ev_item = evidence_map[clause_id]
                citation = Citation(
                    clause_id=clause_id,
                    clause_number=ev_item.clause_number,
                    source_pages=ev_item.source_pages,
                )
                if citation not in validated_citations:
                    validated_citations.append(citation)

    # 2. Check if answer indicates insufficient evidence
    insufficient_phrases = [
        "insufficient to answer",
        "evidence is insufficient",
        "does not contain sufficient information",
        "no evidence available",
    ]
    if any(phrase in raw_answer.lower() for phrase in insufficient_phrases):
        insufficient_evidence = True

    if insufficient_evidence and not raw_answer:
        raw_answer = "The retrieved contract evidence is insufficient to answer this question."

    return raw_answer, validated_citations, insufficient_evidence
