"""
Unit Test Suite for RAGPipeline Module (Mocked LLM Generation)
"""

from unittest.mock import MagicMock, patch
import pytest

from src.clause_segmentation.models import SegmentedClause
from src.document_processing.models import SourceType
from src.embeddings import ClauseEmbedder, FAISSIndexManager
from src.rag.generator import LLMGenerator
from src.rag.pipeline import RAGPipeline


@pytest.fixture(scope="module")
def sample_rag_index():
    embedder = ClauseEmbedder()
    manager = FAISSIndexManager()
    clauses = [
        SegmentedClause(
            clause_id="doc1:clause:001",
            document_id="doc1",
            clause_number="1.1",
            clause_heading="Confidentiality",
            clause_text="1.1 Confidentiality. Each party shall maintain confidentiality of trade secrets.",
            source_type=SourceType.PDF,
            source_pages=[1],
            character_count=80,
            word_count=10,
        ),
        SegmentedClause(
            clause_id="doc1:clause:002",
            document_id="doc1",
            clause_number="2.1",
            clause_heading="Termination",
            clause_text="2.1 Termination. Agreement may be terminated upon 30 days notice.",
            source_type=SourceType.PDF,
            source_pages=[1],
            character_count=67,
            word_count=9,
        ),
    ]
    manager.build_index(clauses, embedder)
    return manager, embedder


def test_rag_pipeline_supported_query(sample_rag_index):
    manager, embedder = sample_rag_index

    mock_gen = MagicMock(spec=LLMGenerator)
    mock_gen.get_active_model_id.return_value = "qwen3-4b-instruct-2507"
    mock_gen.generate.return_value = {
        "answer": "Each party must maintain strict confidentiality of trade secrets.",
        "citations": [{"clause_id": "doc1:clause:001", "source_pages": [1]}],
        "insufficient_evidence": False,
    }

    pipeline = RAGPipeline(index_manager=manager, embedder=embedder, generator=mock_gen)
    response = pipeline.answer_query("What are the confidentiality obligations?", similarity_threshold=0.30)

    assert response.insufficient_evidence is False
    assert "confidentiality" in response.answer.lower()
    assert len(response.citations) == 1
    assert response.citations[0].clause_id == "doc1:clause:001"


def test_rag_pipeline_unsupported_query_insufficient_evidence(sample_rag_index):
    manager, embedder = sample_rag_index

    mock_gen = MagicMock(spec=LLMGenerator)
    mock_gen.get_active_model_id.return_value = "qwen3-4b-instruct-2507"

    pipeline = RAGPipeline(index_manager=manager, embedder=embedder, generator=mock_gen)
    # High threshold 0.99 will drop all evidence
    response = pipeline.answer_query("What is the governing law?", similarity_threshold=0.99)

    assert response.insufficient_evidence is True
    assert "insufficient to answer" in response.answer.lower()
    assert len(response.citations) == 0
    # LLM should NOT have been called when evidence is empty
    mock_gen.generate.assert_not_called()


def test_rag_pipeline_invalid_citation_filtering(sample_rag_index):
    manager, embedder = sample_rag_index

    mock_gen = MagicMock(spec=LLMGenerator)
    mock_gen.get_active_model_id.return_value = "qwen3-4b-instruct-2507"
    mock_gen.generate.return_value = {
        "answer": "Contract ends on 30 days notice.",
        "citations": [
            {"clause_id": "doc1:clause:002", "source_pages": [1]},
            {"clause_id": "FAKE_CLAUSE_ID_999", "source_pages": [9]},  # Fake citation!
        ],
        "insufficient_evidence": False,
    }

    pipeline = RAGPipeline(index_manager=manager, embedder=embedder, generator=mock_gen)
    response = pipeline.answer_query("Termination notice period?", similarity_threshold=0.30)

    assert response.insufficient_evidence is False
    # Grounding validator MUST filter out FAKE_CLAUSE_ID_999
    assert len(response.citations) == 1
    assert response.citations[0].clause_id == "doc1:clause:002"
