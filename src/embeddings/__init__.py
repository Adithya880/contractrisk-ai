"""
ContractRisk AI - Phase 6 Embeddings & FAISS Index Package
"""

from src.embeddings.embedder import ClauseEmbedder
from src.embeddings.index import FAISSIndexManager
from src.embeddings.models import ClauseMetadata, IndexManifest, SearchResult

__all__ = [
    "ClauseEmbedder",
    "FAISSIndexManager",
    "ClauseMetadata",
    "SearchResult",
    "IndexManifest",
]
