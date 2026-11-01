"""
Clause Embedder Module for ContractRisk AI

Generates 384-dimensional L2-normalized vector embeddings for contract clauses
using SentenceTransformers (all-MiniLM-L6-v2). Auto-detects GPU/CPU execution.
"""

from typing import List, Optional, Tuple, Union
import numpy as np
import torch
from sentence_transformers import SentenceTransformer

from src.clause_segmentation.models import SegmentedClause
from src.embeddings.models import ClauseMetadata


class ClauseEmbedder:
    """
    Embedding generator for contract clause texts using SentenceTransformer (all-MiniLM-L6-v2).
    """

    MODEL_NAME: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384

    def __init__(self, model_name: str = MODEL_NAME, device: Optional[str] = None, batch_size: int = 32):
        self.model_name = model_name
        self.batch_size = batch_size

        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        self._model: Optional[SentenceTransformer] = None

    def _load_model(self) -> SentenceTransformer:
        """Lazy loader for SentenceTransformer model."""
        if self._model is None:
            try:
                self._model = SentenceTransformer(self.model_name, device=self.device, local_files_only=True)
            except Exception:
                self._model = SentenceTransformer(self.model_name, device=self.device)
        return self._model

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """
        Encodes a list of strings into L2-normalized 384-dimensional float32 embeddings.

        Args:
            texts: List of text strings.

        Returns:
            Numpy float32 array of shape (N, 384) with unit L2 norm.
        """
        if not texts:
            return np.empty((0, self.EMBEDDING_DIM), dtype=np.float32)

        model = self._load_model()
        raw_embeddings = model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=False,
        ).astype(np.float32)

        # Apply explicit L2 normalization
        norms = np.linalg.norm(raw_embeddings, ord=2, axis=1, keepdims=True)
        # Avoid division by zero
        norms[norms == 0] = 1e-12
        normalized_embeddings = raw_embeddings / norms

        return normalized_embeddings

    def embed_clauses(
        self, clauses: List[SegmentedClause]
    ) -> Tuple[np.ndarray, List[ClauseMetadata]]:
        """
        Embeds a list of SegmentedClause objects and produces aligned ClauseMetadata records.

        Args:
            clauses: List of SegmentedClause objects from Phase 5.

        Returns:
            Tuple of (embeddings: np.ndarray, metadata_list: List[ClauseMetadata])
        """
        if not clauses:
            return np.empty((0, self.EMBEDDING_DIM), dtype=np.float32), []

        valid_clauses = [c for c in clauses if c.clause_text and c.clause_text.strip()]
        texts = [c.clause_text for c in valid_clauses]

        embeddings = self.embed_texts(texts)

        metadata_list: list[ClauseMetadata] = []
        for idx, clause in enumerate(valid_clauses):
            meta = ClauseMetadata(
                vector_index=idx,
                clause_id=clause.clause_id,
                document_id=clause.document_id,
                clause_number=clause.clause_number,
                clause_heading=clause.clause_heading,
                clause_text=clause.clause_text,
                source_pages=clause.source_pages,
                start_page=clause.start_page,
                end_page=clause.end_page,
                hierarchy_level=clause.hierarchy_level,
                parent_clause_number=clause.parent_clause_number,
            )
            metadata_list.append(meta)

        return embeddings, metadata_list
