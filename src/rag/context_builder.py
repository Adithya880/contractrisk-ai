"""
Context Builder Module for ContractRisk AI RAG Pipeline

Formats retrieved RAGEvidenceItem objects into structured evidence prompt context,
enforcing token/character budget limits while preserving exact clause text and provenance.
"""

from typing import List
from src.rag.models import RAGEvidenceItem


class ContextBuilder:
    """
    Formats evidence items into structured prompt context for LLM generation.
    """

    MAX_CHAR_BUDGET: int = 8000  # Approximately 2048 tokens

    def __init__(self, max_char_budget: int = MAX_CHAR_BUDGET):
        self.max_char_budget = max_char_budget

    def build_context(self, evidence_items: List[RAGEvidenceItem]) -> str:
        """
        Formats a list of evidence items into a structured context block.

        Args:
            evidence_items: List of RAGEvidenceItem objects ordered by similarity rank.

        Returns:
            Formatted context string within budget limits.
        """
        if not evidence_items:
            return "No contract evidence available."

        context_blocks: list[str] = []
        current_length = 0

        for idx, item in enumerate(evidence_items, start=1):
            pages_str = ", ".join(str(p) for p in item.source_pages) if item.source_pages else "N/A"
            block = (
                f"[Evidence {idx}]\n"
                f"Clause ID: {item.clause_id}\n"
                f"Clause Number: {item.clause_number or 'None'}\n"
                f"Heading: {item.clause_heading or 'None'}\n"
                f"Source Page(s): {pages_str}\n"
                f"Similarity Score: {item.similarity_score:.4f}\n"
                f"Clause Text:\n{item.clause_text}\n"
            )

            block_len = len(block)
            if current_length + block_len > self.max_char_budget and context_blocks:
                # Stop adding further evidence items to stay within budget limit
                break

            context_blocks.append(block)
            current_length += block_len

        return "\n".join(context_blocks)
