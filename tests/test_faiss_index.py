"""
Unit Test Suite for FAISSIndexManager Module
"""

import json
import tempfile
from pathlib import Path
import pytest

from src.clause_segmentation.models import SegmentedClause
from src.document_processing.models import SourceType
from src.embeddings.embedder import ClauseEmbedder
from src.embeddings.index import FAISSIndexManager


@pytest.fixture(scope="module")
def embedder():
    return ClauseEmbedder()


@pytest.fixture
def sample_clauses():
    return [
        SegmentedClause(
            clause_id="doc1:clause:001",
            document_id="doc1",
            clause_number="1.1",
            clause_heading="Governing Law",
            clause_text="1.1 Governing Law. This Agreement shall be governed by California law.",
            source_type=SourceType.PDF,
            source_pages=[1],
            character_count=70,
            word_count=10,
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


def test_faiss_index_building_and_alignment(embedder, sample_clauses):
    manager = FAISSIndexManager()
    count = manager.build_index(sample_clauses, embedder)

    assert count == 2
    assert manager.total_vectors == 2
    assert len(manager._metadata) == 2
    assert manager._metadata[0].clause_id == "doc1:clause:001"
    assert manager._metadata[1].clause_id == "doc1:clause:002"


def test_faiss_persistence_save_load(embedder, sample_clauses):
    manager = FAISSIndexManager()
    manager.build_index(sample_clauses, embedder)

    with tempfile.TemporaryDirectory() as tmpdir:
        save_path = Path(tmpdir)
        manager.save(save_path)

        assert (save_path / "contract_clauses.faiss").exists()
        assert (save_path / "contract_clauses_metadata.json").exists()
        assert (save_path / "manifest.json").exists()

        reloaded_manager = FAISSIndexManager()
        reloaded_manager.load(save_path)

        assert reloaded_manager.total_vectors == 2
        assert len(reloaded_manager._metadata) == 2
        assert reloaded_manager._metadata[0].clause_id == "doc1:clause:001"


def test_faiss_mismatch_detection(embedder, sample_clauses):
    manager = FAISSIndexManager()
    manager.build_index(sample_clauses, embedder)

    with tempfile.TemporaryDirectory() as tmpdir:
        save_path = Path(tmpdir)
        manager.save(save_path)

        # Corrupt metadata JSON file by dropping one record
        meta_file = save_path / "contract_clauses_metadata.json"
        meta_data = json.loads(meta_file.read_text(encoding="utf-8"))
        meta_data.pop()
        meta_file.write_text(json.dumps(meta_data), encoding="utf-8")

        reloaded_manager = FAISSIndexManager()
        with pytest.raises(ValueError):
            reloaded_manager.load(save_path)
