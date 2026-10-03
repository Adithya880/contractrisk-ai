"""
Unit Test Suite for ClauseEmbedder Module
"""

import numpy as np
import pytest

from src.clause_segmentation.models import SegmentedClause
from src.document_processing.models import SourceType
from src.embeddings.embedder import ClauseEmbedder


@pytest.fixture(scope="module")
def embedder():
    """Initializes shared ClauseEmbedder instance for unit tests."""
    return ClauseEmbedder()


def test_embedding_dimension_and_norm(embedder):
    texts = [
        "This Agreement is governed by Delaware law.",
        "Licensor shall indemnify Licensee against third-party claims.",
    ]
    embeddings = embedder.embed_texts(texts)

    assert embeddings.shape == (2, 384)
    assert embeddings.dtype == np.float32

    # Verify L2 Unit Norm
    norms = np.linalg.norm(embeddings, ord=2, axis=1)
    np.testing.assert_allclose(norms, 1.0, atol=1e-4)


def test_batch_embedding(embedder):
    texts = [f"Sample contractual clause number {i}" for i in range(10)]
    embedder.batch_size = 3
    embeddings = embedder.embed_texts(texts)

    assert embeddings.shape == (10, 384)


def test_embed_clauses(embedder):
    clause1 = SegmentedClause(
        clause_id="doc1:clause:001",
        document_id="doc1",
        clause_number="1.1",
        clause_heading="Definitions",
        clause_text="1.1 Definitions. 'Premises' means Suite 100.",
        source_type=SourceType.PDF,
        source_pages=[1],
        character_count=43,
        word_count=6,
    )

    embeddings, metadata_list = embedder.embed_clauses([clause1])

    assert embeddings.shape == (1, 384)
    assert len(metadata_list) == 1
    assert metadata_list[0].clause_id == "doc1:clause:001"
    assert metadata_list[0].vector_index == 0


def test_empty_embedding(embedder):
    embeddings = embedder.embed_texts([])
    assert embeddings.shape == (0, 384)
