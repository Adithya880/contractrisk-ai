"""
ContractRisk AI - Phase 7 Retrieval-Augmented Generation (RAG) Package
"""

from src.rag.context_builder import ContextBuilder
from src.rag.generator import LLMGenerator, LLMGeneratorError, LMStudioConnectionError
from src.rag.models import Citation, RAGEvidenceItem, RAGResponse
from src.rag.pipeline import RAGPipeline
from src.rag.retriever import RAGRetriever

__all__ = [
    "RAGPipeline",
    "RAGResponse",
    "RAGEvidenceItem",
    "Citation",
    "LLMGenerator",
    "RAGRetriever",
    "ContextBuilder",
    "LLMGeneratorError",
    "LMStudioConnectionError",
]
