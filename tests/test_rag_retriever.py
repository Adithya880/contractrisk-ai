"""
Unit Test Suite for RAGRetriever Module
"""

import pytest
from src.clause_segmentation.models import SegmentedClause
from src.document_processing.models import SourceType
from src.embeddings import ClauseEmbedder, FAISSIndexManager
from src.rag.retriever import RAGRetriever


@pytest.fixture(scope="module")
def sample_index():
    embedder = ClauseEmbedder()
    manager = FAISSIndexManager()
    clauses = [
        SegmentedClause(
            clause_id="doc1:clause:001",
            document_id="doc1",
            clause_number="1.1",
            clause_heading="Governing Law",
            clause_text="1.1 Governing Law. This Agreement shall be governed by Delaware law.",
            source_type=SourceType.PDF,
            source_pages=[1],
            character_count=67,
            word_count=9,
        ),
        SegmentedClause(
            clause_id="doc1:clause:002",
            document_id="doc1",
            clause_number="2.1",
            clause_heading="Indemnification",
            clause_text="2.1 Indemnification. Licensor agrees to defend licensee against third-party claims.",
            source_type=SourceType.PDF,
            source_pages=[1],
            character_count=82,
            word_count=10,
        ),
    ]
    manager.build_index(clauses, embedder)
    return manager, embedder


def test_rag_retriever_evidence_formatting(sample_index):
    manager, embedder = sample_index
    retriever = RAGRetriever(index_manager=manager, embedder=embedder, default_threshold=0.30)

    evidence = retriever.retrieve_evidence("Delaware law governing agreement")

    assert len(evidence) > 0
    assert evidence[0].clause_id == "doc1:clause:001"
    assert evidence[0].clause_number == "1.1"
    assert evidence[0].source_pages == [1]
    assert evidence[0].similarity_score > 0.30
