"""
Segmented Clause Models for ContractRisk AI

Defines Pydantic v2 data models representing extracted clauses,
their hierarchical relationships, structural provenance, and segmentation results.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from src.document_processing.models import SourceType


class SegmentedClause(BaseModel):
    """
    Represents an individual segmented clause from a contract document.
    Maintains text, legal numbering, hierarchy, and complete page/element provenance.
    """
    model_config = ConfigDict(frozen=True)

    clause_id: str = Field(description="Deterministic unique clause ID ({document_id}:clause:{sequence:03d}).")
    document_id: str = Field(description="Unique ID of the parent extracted document.")
    clause_number: Optional[str] = Field(default=None, description="Legal section/clause number (e.g. '1.1', 'ARTICLE II', '(a)').")
    clause_heading: Optional[str] = Field(default=None, description="Clause title or heading if present.")
    clause_text: str = Field(description="Full normalized text content of the clause.")
    source_type: SourceType = Field(description="Source document format (PDF or DOCX).")
    source_pages: List[int] = Field(default_factory=list, description="All 1-indexed page numbers spanned by this clause.")
    start_page: Optional[int] = Field(default=None, description="First page number where clause begins.")
    end_page: Optional[int] = Field(default=None, description="Last page number where clause ends.")
    source_element_ids: List[str] = Field(default_factory=list, description="List of Phase 4 DocumentElement IDs forming this clause.")
    parent_clause_number: Optional[str] = Field(default=None, description="Clause number of parent section if applicable.")
    hierarchy_level: int = Field(default=1, description="1-based structural depth level (1=Section/Article, 2=Subclause, etc.).")
    character_count: int = Field(description="Total character count of clause_text.")
    word_count: int = Field(description="Total word count of clause_text.")


class SegmentationResult(BaseModel):
    """
    Container representing the complete clause segmentation output for a contract document.
    Includes validation metrics and text coverage analysis.
    """
    document_id: str = Field(description="Parent document unique identifier.")
    source_filename: str = Field(description="Base filename of the input contract.")
    clauses: List[SegmentedClause] = Field(default_factory=list, description="List of segmented clauses in document sequence.")
    total_clauses: int = Field(description="Total count of segmented clauses.")
    source_character_count: int = Field(description="Total character count of raw extracted document elements.")
    segmented_character_count: int = Field(description="Aggregated character count of all segmented clauses.")
    text_coverage_ratio: float = Field(description="Ratio of segmented characters to source characters (segmented / source).")
    unsegmented_elements_count: int = Field(default=0, description="Count of structural elements not included in any clause.")
