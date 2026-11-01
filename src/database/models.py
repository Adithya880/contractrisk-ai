"""
SQLAlchemy 2.x Relational Database Models for ContractRisk AI.
Defines explicit tables, ForeignKey relationships, constraints, and JSON storage for analysis outputs.
"""

from datetime import datetime, timezone
from typing import List, Optional, Any, Dict
from sqlalchemy import (
    Integer, String, Float, Text, Boolean, DateTime, JSON,
    ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utc_now() -> datetime:
    """Return current timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Base declarative class for all SQLAlchemy database models."""
    pass


class DocumentModel(Base):
    """Stores uploaded document metadata."""
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    document_type: Mapped[str] = mapped_column(String(16), nullable=False)  # PDF or DOCX
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    page_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    clause_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processing_status: Mapped[str] = mapped_column(String(32), default="COMPLETED", nullable=False)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships
    clauses: Mapped[List["ClauseModel"]] = relationship(
        "ClauseModel", back_populates="document", cascade="all, delete-orphan"
    )
    summaries: Mapped[List["ContractSummaryModel"]] = relationship(
        "ContractSummaryModel", back_populates="document", cascade="all, delete-orphan"
    )
    runs: Mapped[List["AnalysisRunModel"]] = relationship(
        "AnalysisRunModel", back_populates="document", cascade="all, delete-orphan"
    )


class ClauseModel(Base):
    """Stores segmented contractual clauses."""
    __tablename__ = "clauses"
    __table_args__ = (
        UniqueConstraint("document_id", "clause_id", name="uq_document_clause_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("documents.document_id", ondelete="CASCADE"), index=True, nullable=False
    )
    clause_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    clause_number: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    clause_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    clause_text: Mapped[str] = mapped_column(Text, nullable=False)
    source_pages: Mapped[Optional[List[int]]] = mapped_column(JSON, nullable=True)
    source_element_ids: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    sequence_number: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    document: Mapped["DocumentModel"] = relationship("DocumentModel", back_populates="clauses")
    risk_assessment: Mapped[Optional["RiskAssessmentModel"]] = relationship(
        "RiskAssessmentModel", back_populates="clause", uselist=False, cascade="all, delete-orphan"
    )


class RiskAssessmentModel(Base):
    """Stores hybrid risk assessment and component score breakdown per clause."""
    __tablename__ = "risk_assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    clause_db_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("clauses.id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )
    risk_category: Mapped[str] = mapped_column(String(64), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(16), nullable=False)  # NORMAL, LOW, MEDIUM, HIGH
    final_score: Mapped[float] = mapped_column(Float, nullable=False)
    bert_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    rule_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    rag_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    llm_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    bert_clause_type: Mapped[str] = mapped_column(String(64), default="Other", nullable=False)
    bert_confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    risk_explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    llm_inference_status: Mapped[str] = mapped_column(String(32), default="SKIPPED", nullable=False)
    uncertainty: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    key_risk_factors: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    clause: Mapped["ClauseModel"] = relationship("ClauseModel", back_populates="risk_assessment")
    rule_matches: Mapped[List["RuleMatchModel"]] = relationship(
        "RuleMatchModel", back_populates="risk_assessment", cascade="all, delete-orphan"
    )
    evidence_citations: Mapped[List["EvidenceCitationModel"]] = relationship(
        "EvidenceCitationModel", back_populates="risk_assessment", cascade="all, delete-orphan"
    )
    future_scenario: Mapped[Optional["FutureScenarioModel"]] = relationship(
        "FutureScenarioModel", back_populates="risk_assessment", uselist=False, cascade="all, delete-orphan"
    )


class RuleMatchModel(Base):
    """Stores rule engine pattern matches per risk assessment."""
    __tablename__ = "rule_matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    risk_assessment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("risk_assessments.id", ondelete="CASCADE"), index=True, nullable=False
    )
    rule_id: Mapped[str] = mapped_column(String(128), nullable=False)
    rule_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[float] = mapped_column(Float, nullable=False)
    matched_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationship
    risk_assessment: Mapped["RiskAssessmentModel"] = relationship("RiskAssessmentModel", back_populates="rule_matches")


class EvidenceCitationModel(Base):
    """Stores benchmark evidence retrieved via RAG per risk assessment."""
    __tablename__ = "evidence_citations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    risk_assessment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("risk_assessments.id", ondelete="CASCADE"), index=True, nullable=False
    )
    source_clause_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    source_text: Mapped[str] = mapped_column(Text, nullable=False)
    similarity_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    citation_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationship
    risk_assessment: Mapped["RiskAssessmentModel"] = relationship("RiskAssessmentModel", back_populates="evidence_citations")


class FutureScenarioModel(Base):
    """Stores generated evidence-grounded future risk scenarios."""
    __tablename__ = "future_scenarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    risk_assessment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("risk_assessments.id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )
    scenario_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    clause_id: Mapped[str] = mapped_column(String(128), nullable=False)
    scenario_title: Mapped[str] = mapped_column(String(255), nullable=False)
    trigger_condition: Mapped[str] = mapped_column(Text, nullable=False)
    scenario_description: Mapped[str] = mapped_column(Text, nullable=False)
    possible_consequence: Mapped[str] = mapped_column(Text, nullable=False)
    assumptions: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    uncertainty: Mapped[str] = mapped_column(Text, nullable=False)
    fallback_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    disclaimer: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationship
    risk_assessment: Mapped["RiskAssessmentModel"] = relationship("RiskAssessmentModel", back_populates="future_scenario")


class ContractSummaryModel(Base):
    """Stores aggregated contract-level risk metrics."""
    __tablename__ = "contract_summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("documents.document_id", ondelete="CASCADE"), index=True, nullable=False
    )
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(16), nullable=False)
    normal_risk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    high_risk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    medium_risk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    low_risk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    clause_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationship
    document: Mapped["DocumentModel"] = relationship("DocumentModel", back_populates="summaries")


class AnalysisRunModel(Base):
    """Stores execution run metadata for reproducibility tracking (Section 5)."""
    __tablename__ = "analysis_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    document_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("documents.document_id", ondelete="CASCADE"), index=True, nullable=False
    )
    pipeline_version: Mapped[str] = mapped_column(String(32), default="1.0.0", nullable=False)
    model_info: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="COMPLETED", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationship
    document: Mapped["DocumentModel"] = relationship("DocumentModel", back_populates="runs")
