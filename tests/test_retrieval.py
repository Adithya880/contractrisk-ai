"""
Unit Test Suite for Semantic Similarity Retrieval and Sanity Checks
"""

import pytest
from src.clause_segmentation.models import SegmentedClause
from src.document_processing.models import SourceType
from src.embeddings.embedder import ClauseEmbedder
from src.embeddings.index import FAISSIndexManager


@pytest.fixture(scope="module")
def embedder():
    return ClauseEmbedder()


@pytest.fixture
def synthetic_retrieval_corpus():
    return [
        SegmentedClause(
            clause_id="corpus:clause:001",
            document_id="doc_confidentiality",
            clause_number="1.1",
            clause_heading="Confidentiality",
            clause_text="1.1 Confidentiality. Each party shall maintain strict confidentiality regarding proprietary technical data and trade secrets disclosed hereunder.",
            source_type=SourceType.PDF,
            source_pages=[1],
            character_count=145,
            word_count=18,
        ),
        SegmentedClause(
            clause_id="corpus:clause:002",
            document_id="doc_termination",
            clause_number="2.1",
            clause_heading="Termination",
            clause_text="2.1 Termination. Either party may terminate this Agreement for convenience upon thirty (30) days prior written notice to the other party.",
            source_type=SourceType.PDF,
            source_pages=[1],
            character_count=146,
            word_count=21,
        ),
        SegmentedClause(
            clause_id="corpus:clause:003",
            document_id="doc_governing_law",
            clause_number="3.1",
            clause_heading="Governing Law",
            clause_text="3.1 Governing Law. This contract shall be governed by and construed in accordance with the laws of the State of Delaware.",
            source_type=SourceType.PDF,
            source_pages=[1],
            character_count=123,
            word_count=18,
        ),
        SegmentedClause(
            clause_id="corpus:clause:004",
            document_id="doc_payment",
            clause_number="4.1",
            clause_heading="Payment Terms",
            clause_text="4.1 Payment Terms. All invoices shall be paid in full within thirty (30) days of receipt by Licensee.",
            source_type=SourceType.PDF,
            source_pages=[1],
            character_count=104,
            word_count=17,
        ),
    ]


def test_semantic_retrieval_sanity_check(embedder, synthetic_retrieval_corpus):
    manager = FAISSIndexManager()
    manager.build_index(synthetic_retrieval_corpus, embedder)

    query = "What happens when confidential information is disclosed?"
    results = manager.search(query, embedder, top_k=3)

    assert len(results) > 0
    top_result = results[0]

    # Semantic check: Top result MUST be the Confidentiality clause
    assert top_result.clause_id == "corpus:clause:001"
    assert top_result.clause_heading == "Confidentiality"
    assert top_result.similarity_score > 0.40


def test_top_k_retrieval(embedder, synthetic_retrieval_corpus):
    manager = FAISSIndexManager()
    manager.build_index(synthetic_retrieval_corpus, embedder)

    results = manager.search("termination notice period", embedder, top_k=2)

    assert len(results) == 2
    assert results[0].clause_id == "corpus:clause:002"  # Termination clause


def test_similarity_threshold(embedder, synthetic_retrieval_corpus):
    manager = FAISSIndexManager()
    manager.build_index(synthetic_retrieval_corpus, embedder)

    # High threshold should filter out weakly matching clauses
    results = manager.search(
        "laws of the State of Delaware",
        embedder,
        top_k=5,
        similarity_threshold=0.60
    )

    assert len(results) >= 1
    assert all(r.similarity_score >= 0.60 for r in results)
    assert results[0].clause_id == "corpus:clause:003"  # Governing Law
