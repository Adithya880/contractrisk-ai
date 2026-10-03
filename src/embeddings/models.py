"""
Embeddings & FAISS Data Models for ContractRisk AI

Defines Pydantic v2 data models for vector metadata mapping, search results,
and index persistence compatibility manifests.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class ClauseMetadata(BaseModel):
    """
    Metadata associated with a vector at a specific index position in FAISS.
    """
    model_config = ConfigDict(frozen=True)

    vector_index: int = Field(description="0-indexed position in FAISS vector array.")
    clause_id: str = Field(description="Unique clause identifier.")
    document_id: str = Field(description="Parent contract document ID.")
    clause_number: Optional[str] = Field(default=None, description="Legal section/clause number.")
    clause_heading: Optional[str] = Field(default=None, description="Clause title or heading.")
    clause_text: str = Field(description="Full text of the segmented clause.")
    source_pages: List[int] = Field(default_factory=list, description="List of source page numbers.")
    start_page: Optional[int] = Field(default=None, description="First page of clause.")
    end_page: Optional[int] = Field(default=None, description="Last page of clause.")
    hierarchy_level: int = Field(default=1, description="1-based hierarchy level.")
    parent_clause_number: Optional[str] = Field(default=None, description="Parent clause number.")


class SearchResult(BaseModel):
    """
    Structure representing a retrieved clause with similarity score.
    """
    clause_id: str = Field(description="Unique clause identifier.")
    document_id: str = Field(description="Parent contract document ID.")
    clause_number: Optional[str] = Field(default=None, description="Legal section/clause number.")
    clause_heading: Optional[str] = Field(default=None, description="Clause title or heading.")
    clause_text: str = Field(description="Full text of the segmented clause.")
    source_pages: List[int] = Field(default_factory=list, description="List of source page numbers.")
    similarity_score: float = Field(description="Inner product (Cosine similarity) score.")
    vector_index: int = Field(description="FAISS vector index position.")
    hierarchy_level: int = Field(default=1, description="Hierarchy depth level.")
    parent_clause_number: Optional[str] = Field(default=None, description="Parent clause number.")


class IndexManifest(BaseModel):
    """
    Persistence manifest for validating FAISS index compatibility during save/load.
    """
    model_name: str = Field(default="all-MiniLM-L6-v2", description="SentenceTransformer model name.")
    embedding_dimension: int = Field(default=384, description="Vector dimension count.")
    normalization: str = Field(default="L2", description="Normalization type applied.")
    faiss_index_type: str = Field(default="IndexFlatIP", description="FAISS index class.")
    total_vectors: int = Field(description="Total number of vectors in index.")
    created_at: str = Field(description="ISO timestamp when index was generated.")
