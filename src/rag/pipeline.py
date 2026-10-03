"""
RAG Pipeline Facade Module for ContractRisk AI

Coordinates evidence retrieval, context building, LLM generation, and grounding validation
to answer contract questions with verifiable evidence citations.
"""

from typing import Optional
from src.embeddings import ClauseEmbedder, FAISSIndexManager
from src.rag.context_builder import ContextBuilder
from src.rag.generator import LLMGenerator
from src.rag.models import RAGResponse
from src.rag.retriever import RAGRetriever
from src.rag.validators import validate_grounding


class RAGPipeline:
    """
    Facade class coordinating the complete RAG workflow.
    """

    DEFAULT_TOP_K: int = 5
    DEFAULT_THRESHOLD: float = 0.65

    def __init__(
        self,
        index_manager: FAISSIndexManager,
        embedder: ClauseEmbedder,
        generator: Optional[LLMGenerator] = None,
        context_builder: Optional[ContextBuilder] = None,
    ):
        self.retriever = RAGRetriever(
            index_manager=index_manager,
            embedder=embedder,
            default_top_k=self.DEFAULT_TOP_K,
            default_threshold=self.DEFAULT_THRESHOLD,
        )
        self.generator = generator or LLMGenerator()
        self.context_builder = context_builder or ContextBuilder()

    def answer_query(
        self,
        query: str,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
    ) -> RAGResponse:
        """
        Executes evidence-grounded RAG query answering.

        Args:
            query: User natural language contract question.
            top_k: Maximum evidence items to retrieve (default 5).
            similarity_threshold: Minimum Cosine similarity score cutoff (default 0.65).

        Returns:
            RAGResponse object containing answer, evidence items, verified citations, and flags.
        """
        actual_top_k = top_k if top_k is not None else self.DEFAULT_TOP_K
        actual_threshold = (
            similarity_threshold
            if similarity_threshold is not None
            else self.DEFAULT_THRESHOLD
        )
        model_name = self.generator.get_active_model_id()

        if not query or not query.strip():
            return RAGResponse(
                query=query,
                answer="The retrieved contract evidence is insufficient to answer this question.",
                evidence=[],
                citations=[],
                insufficient_evidence=True,
                model_name=model_name,
                retrieval_top_k=actual_top_k,
                retrieval_threshold=actual_threshold,
            )

        # 1. Retrieve evidence
        evidence_items = self.retriever.retrieve_evidence(
            query=query,
            top_k=actual_top_k,
            similarity_threshold=actual_threshold,
        )

        # 2. Check for empty retrieval / below threshold fallback
        if not evidence_items:
            return RAGResponse(
                query=query,
                answer="The retrieved contract evidence is insufficient to answer this question.",
                evidence=[],
                citations=[],
                insufficient_evidence=True,
                model_name=model_name,
                retrieval_top_k=actual_top_k,
                retrieval_threshold=actual_threshold,
            )

        # 3. Format Context Block
        context_str = self.context_builder.build_context(evidence_items)

        # 4. Generate Answer via Local LLM
        try:
            raw_response = self.generator.generate(query=query, context=context_str)
        except Exception as e:
            # Fallback error handling when LM Studio is unreachable or errors
            return RAGResponse(
                query=query,
                answer=f"Generation Error: {e}",
                evidence=evidence_items,
                citations=[],
                insufficient_evidence=True,
                model_name=model_name,
                retrieval_top_k=actual_top_k,
                retrieval_threshold=actual_threshold,
            )

        # 5. Validate Grounding & Citations
        answer, citations, insufficient = validate_grounding(raw_response, evidence_items)

        return RAGResponse(
            query=query,
            answer=answer,
            evidence=evidence_items,
            citations=citations,
            insufficient_evidence=insufficient,
            model_name=model_name,
            retrieval_top_k=actual_top_k,
            retrieval_threshold=actual_threshold,
        )
