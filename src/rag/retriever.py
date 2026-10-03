"""
RAG Retriever Module for ContractRisk AI

Wraps Phase 6 FAISSIndexManager and ClauseEmbedder to retrieve top-k semantic evidence items
for a natural language query.
"""

from typing import List, Optional
from src.embeddings import ClauseEmbedder, FAISSIndexManager
from src.rag.models import RAGEvidenceItem


class RAGRetriever:
    """
    Retriever facade for RAG pipeline utilizing Phase 6 vector search infrastructure.
    """

    def __init__(
        self,
        index_manager: FAISSIndexManager,
        embedder: ClauseEmbedder,
        default_top_k: int = 5,
        default_threshold: float = 0.65,
    ):
        self.index_manager = index_manager
        self.embedder = embedder
        self.default_top_k = default_top_k
        self.default_threshold = default_threshold

    def retrieve_evidence(
        self,
        query: str,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
    ) -> List[RAGEvidenceItem]:
        """
        Retrieves top-k evidence clauses for a query filtered by similarity threshold.

        Args:
            query: User search query.
            top_k: Optional top-k count (defaults to self.default_top_k).
            similarity_threshold: Optional similarity score threshold (defaults to self.default_threshold).

        Returns:
            List of RAGEvidenceItem objects.
        """
        actual_top_k = top_k if top_k is not None else self.default_top_k
        actual_threshold = (
            similarity_threshold
            if similarity_threshold is not None
            else self.default_threshold
        )

        search_results = self.index_manager.search(
            query=query,
            embedder=self.embedder,
            top_k=actual_top_k,
            similarity_threshold=actual_threshold,
        )

        evidence_list: list[RAGEvidenceItem] = []
        for res in search_results:
            item = RAGEvidenceItem(
                clause_id=res.clause_id,
                document_id=res.document_id,
                clause_number=res.clause_number,
                clause_heading=res.clause_heading,
                clause_text=res.clause_text,
                source_pages=res.source_pages,
                similarity_score=res.similarity_score,
            )
            evidence_list.append(item)

        return evidence_list
