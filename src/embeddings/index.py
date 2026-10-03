"""
FAISS Vector Index Manager Module for ContractRisk AI

Manages FAISS IndexFlatIP exact inner-product vector indexing, 1-to-1 clause metadata
mapping, top-k similarity search, and index persistence validation.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Union
import faiss
import numpy as np

from src.clause_segmentation.models import SegmentedClause
from src.embeddings.embedder import ClauseEmbedder
from src.embeddings.models import ClauseMetadata, IndexManifest, SearchResult


class FAISSIndexManager:
    """
    Manager for FAISS IndexFlatIP exact similarity search and metadata alignment.
    """

    DIMENSION: int = 384

    def __init__(self, dimension: int = DIMENSION):
        self.dimension = dimension
        self._index: faiss.IndexFlatIP = faiss.IndexFlatIP(self.dimension)
        self._metadata: list[ClauseMetadata] = []

    @property
    def total_vectors(self) -> int:
        """Returns total vector count in index."""
        return self._index.ntotal

    def build_index(
        self, clauses: List[SegmentedClause], embedder: ClauseEmbedder
    ) -> int:
        """
        Generates embeddings for a list of clauses and builds the FAISS vector index.

        Args:
            clauses: List of SegmentedClause objects from Phase 5.
            embedder: Initialized ClauseEmbedder instance.

        Returns:
            Count of indexed vectors.
        """
        if not clauses:
            return 0

        embeddings, metadata_list = embedder.embed_clauses(clauses)
        if len(metadata_list) == 0:
            return 0

        self.add_vectors(embeddings, metadata_list)
        return self.total_vectors

    def add_vectors(
        self, embeddings: np.ndarray, metadata: List[ClauseMetadata]
    ) -> None:
        """
        Adds L2-normalized vector embeddings and aligned metadata to the index.

        Args:
            embeddings: Float32 numpy array of shape (N, 384).
            metadata: List of ClauseMetadata of length N.
        """
        if len(embeddings) == 0:
            return

        if embeddings.shape[1] != self.dimension:
            raise ValueError(
                f"Embedding dimension mismatch: expected {self.dimension}, got {embeddings.shape[1]}"
            )

        if len(embeddings) != len(metadata):
            raise ValueError(
                f"Count mismatch between embeddings ({len(embeddings)}) and metadata ({len(metadata)})"
            )

        start_index = self._index.ntotal
        updated_metadata: list[ClauseMetadata] = []

        for idx, meta in enumerate(metadata):
            # Re-index vector_index to match FAISS absolute position
            aligned_meta = ClauseMetadata(
                vector_index=start_index + idx,
                clause_id=meta.clause_id,
                document_id=meta.document_id,
                clause_number=meta.clause_number,
                clause_heading=meta.clause_heading,
                clause_text=meta.clause_text,
                source_pages=meta.source_pages,
                start_page=meta.start_page,
                end_page=meta.end_page,
                hierarchy_level=meta.hierarchy_level,
                parent_clause_number=meta.parent_clause_number,
            )
            updated_metadata.append(aligned_meta)

        self._index.add(embeddings)
        self._metadata.extend(updated_metadata)

    def search(
        self,
        query: str,
        embedder: ClauseEmbedder,
        top_k: int = 5,
        similarity_threshold: Optional[float] = None,
    ) -> List[SearchResult]:
        """
        Performs semantic similarity search against the indexed clause vectors.

        Args:
            query: Natural language query string.
            embedder: ClauseEmbedder instance to embed query.
            top_k: Maximum number of search results to return.
            similarity_threshold: Optional minimum cosine similarity score cutoff.

        Returns:
            List of SearchResult objects ordered by descending similarity score.
        """
        if self._index.ntotal == 0 or not query or not query.strip():
            return []

        query_vec = embedder.embed_texts([query])
        actual_top_k = min(top_k, self._index.ntotal)

        scores, indices = self._index.search(query_vec, actual_top_k)

        results: list[SearchResult] = []
        score_row = scores[0]
        idx_row = indices[0]

        for score, vec_idx in zip(score_row, idx_row):
            if vec_idx < 0 or vec_idx >= len(self._metadata):
                continue

            sim_score = float(score)

            if similarity_threshold is not None and sim_score < similarity_threshold:
                continue

            meta = self._metadata[vec_idx]
            res = SearchResult(
                clause_id=meta.clause_id,
                document_id=meta.document_id,
                clause_number=meta.clause_number,
                clause_heading=meta.clause_heading,
                clause_text=meta.clause_text,
                source_pages=meta.source_pages,
                similarity_score=sim_score,
                vector_index=meta.vector_index,
                hierarchy_level=meta.hierarchy_level,
                parent_clause_number=meta.parent_clause_number,
            )
            results.append(res)

        return results

    def save(self, dir_path: Union[str, Path]) -> None:
        """
        Persists FAISS index, metadata, and compatibility manifest to a directory.
        """
        target_dir = Path(dir_path).resolve()
        target_dir.mkdir(parents=True, exist_ok=True)

        faiss_file = target_dir / "contract_clauses.faiss"
        meta_file = target_dir / "contract_clauses_metadata.json"
        manifest_file = target_dir / "manifest.json"

        # Save FAISS Index
        faiss.write_index(self._index, str(faiss_file))

        # Save Metadata
        meta_dicts = [m.model_dump() for m in self._metadata]
        meta_file.write_text(json.dumps(meta_dicts, indent=2), encoding="utf-8")

        # Save Manifest
        manifest = IndexManifest(
            total_vectors=self._index.ntotal,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        manifest_file.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")

    def load(self, dir_path: Union[str, Path]) -> None:
        """
        Loads FAISS index and metadata from a directory, performing compatibility validation.

        Raises:
            FileNotFoundError: If index directory or files do not exist.
            ValueError: If manifest schema, dimension, or vector/metadata counts mismatch.
        """
        target_dir = Path(dir_path).resolve()
        faiss_file = target_dir / "contract_clauses.faiss"
        meta_file = target_dir / "contract_clauses_metadata.json"
        manifest_file = target_dir / "manifest.json"

        if not faiss_file.exists() or not meta_file.exists() or not manifest_file.exists():
            raise FileNotFoundError(f"Index files missing in directory '{dir_path}'")

        # Read & Validate Manifest
        manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
        manifest = IndexManifest(**manifest_data)

        if manifest.embedding_dimension != self.dimension:
            raise ValueError(
                f"Manifest dimension mismatch: index specifies {manifest.embedding_dimension}, "
                f"expected {self.dimension}"
            )

        # Load FAISS Index
        loaded_index = faiss.read_index(str(faiss_file))
        if loaded_index.d != self.dimension:
            raise ValueError(
                f"Loaded FAISS dimension mismatch: index is {loaded_index.d}, expected {self.dimension}"
            )

        # Load Metadata
        raw_meta = json.loads(meta_file.read_text(encoding="utf-8"))
        metadata_list = [ClauseMetadata(**m) for m in raw_meta]

        # Compatibility Verification
        if loaded_index.ntotal != len(metadata_list):
            raise ValueError(
                f"Index/Metadata count mismatch: FAISS has {loaded_index.ntotal} vectors, "
                f"metadata has {len(metadata_list)} records"
            )

        self._index = loaded_index
        self._metadata = metadata_list
