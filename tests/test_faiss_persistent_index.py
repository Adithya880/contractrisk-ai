"""
Integration and persistence tests for FAISS Vector Index in models/faiss_index.
"""

from pathlib import Path
import pytest
from src.embeddings.embedder import ClauseEmbedder
from src.embeddings.index import FAISSIndexManager
from src.rag.retriever import RAGRetriever

FAISS_DIR = Path("models/faiss_index")


def test_persistent_faiss_index_files_exist():
    assert FAISS_DIR.exists(), "models/faiss_index directory does not exist"
    assert (FAISS_DIR / "contract_clauses.faiss").exists()
    assert (FAISS_DIR / "contract_clauses_metadata.json").exists()
    assert (FAISS_DIR / "manifest.json").exists()


def test_persistent_faiss_index_loading():
    manager = FAISSIndexManager()
    manager.load(FAISS_DIR)
    assert manager.total_vectors >= 9000, f"Expected at least 9000 vectors, got {manager.total_vectors}"


def test_persistent_faiss_semantic_retrieval():
    manager = FAISSIndexManager()
    manager.load(FAISS_DIR)
    embedder = ClauseEmbedder(batch_size=32)
    retriever = RAGRetriever(index_manager=manager, embedder=embedder)

    # Test governing law query
    results = retriever.retrieve_evidence(
        query="This agreement is governed by the laws of New York",
        top_k=3,
        similarity_threshold=0.5
    )
    assert len(results) > 0, "Expected at least 1 retrieval result"
    top_result = results[0]
    assert top_result.similarity_score >= 0.5
    assert "governing law" in top_result.clause_heading.lower() or "governing law" in top_result.clause_text.lower()


def test_faiss_missing_dir_fallback():
    manager = FAISSIndexManager()
    with pytest.raises(FileNotFoundError):
        manager.load("non_existent_faiss_directory")
