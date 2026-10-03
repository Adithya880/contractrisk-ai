"""
Comprehensive Unit & Persistence Test Suite for Phase 9 Database Layer.
Tests configuration, connection, models, relationships, repositories, transaction rollback, and schema integrity.
"""

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, Session

from src.database.models import (
    Base,
    DocumentModel,
    ClauseModel,
    RiskAssessmentModel,
    RuleMatchModel,
    EvidenceCitationModel,
    FutureScenarioModel,
    ContractSummaryModel,
    AnalysisRunModel
)
from src.database.repositories import ContractRepository
from src.database.config import settings
from src.risk_analysis.models import (
    ContractRiskSummary,
    RiskAssessment,
    RiskScoreBreakdown,
    RiskCategory,
    RiskLevel,
    RiskRuleMatch
)
from src.api.schemas import FutureScenarioSchema


@pytest.fixture
def sqlite_engine():
    """Fixture providing an in-memory SQLite database engine."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session(sqlite_engine):
    """Fixture providing a transactional database session."""
    SessionMaker = sessionmaker(bind=sqlite_engine, autocommit=False, autoflush=False)
    session = SessionMaker()
    yield session
    session.rollback()
    session.close()


def test_database_configuration_settings():
    """Requirement 12.A: Test database configuration setting properties."""
    assert settings.postgres_host is not None
    assert settings.postgres_port is not None
    assert settings.postgres_db is not None
    assert "postgresql" in settings.database_url or len(settings.database_url) > 0


def test_schema_creation(sqlite_engine):
    """Requirement 12.C: Test schema creation for all 8 tables."""
    table_names = sqlite_engine.dialect.get_table_names(sqlite_engine.connect())
    expected_tables = {
        "documents", "clauses", "risk_assessments", "rule_matches",
        "evidence_citations", "future_scenarios", "contract_summaries", "analysis_runs"
    }
    assert expected_tables.issubset(set(table_names))


def test_document_crud(db_session: Session):
    """Requirement 12.D: Test Document CRUD operations."""
    doc = DocumentModel(
        document_id="doc_test_123",
        filename="test_contract.pdf",
        document_type="PDF",
        page_count=2,
        clause_count=5,
        processing_status="COMPLETED"
    )
    db_session.add(doc)
    db_session.commit()

    fetched = db_session.scalars(
        select(DocumentModel).where(DocumentModel.document_id == "doc_test_123")
    ).first()

    assert fetched is not None
    assert fetched.filename == "test_contract.pdf"
    assert fetched.clause_count == 5


def test_clause_document_relationship(db_session: Session):
    """Requirement 12.E: Test clause -> document 1 to many relationship."""
    doc = DocumentModel(
        document_id="doc_rel_001",
        filename="agreement.pdf",
        document_type="PDF",
        page_count=1,
        clause_count=2
    )
    db_session.add(doc)
    db_session.flush()

    clause1 = ClauseModel(
        document_id=doc.document_id,
        clause_id="c_001",
        clause_number="1.1",
        clause_text="First clause text."
    )
    clause2 = ClauseModel(
        document_id=doc.document_id,
        clause_id="c_002",
        clause_number="1.2",
        clause_text="Second clause text."
    )
    db_session.add_all([clause1, clause2])
    db_session.commit()

    fetched_doc = db_session.scalars(
        select(DocumentModel).where(DocumentModel.document_id == "doc_rel_001")
    ).first()

    assert len(fetched_doc.clauses) == 2
    assert fetched_doc.clauses[0].clause_number == "1.1"


def test_risk_assessment_clause_relationship(db_session: Session):
    """Requirement 12.F: Test risk_assessment -> clause 1 to 1 relationship."""
    doc = DocumentModel(document_id="doc_rel_002", filename="file.pdf", document_type="PDF")
    db_session.add(doc)
    db_session.flush()

    clause = ClauseModel(document_id=doc.document_id, clause_id="c_101", clause_text="Clause text")
    db_session.add(clause)
    db_session.flush()

    ra = RiskAssessmentModel(
        clause_db_id=clause.id,
        risk_category="TERMINATION",
        risk_level="HIGH",
        final_score=75.0,
        risk_explanation="High risk termination clause."
    )
    db_session.add(ra)
    db_session.commit()

    fetched_clause = db_session.scalars(
        select(ClauseModel).where(ClauseModel.clause_id == "c_101")
    ).first()

    assert fetched_clause.risk_assessment is not None
    assert fetched_clause.risk_assessment.risk_level == "HIGH"
    assert fetched_clause.risk_assessment.final_score == 75.0


def test_rule_match_persistence(db_session: Session):
    """Requirement 12.G: Test rule_matches 1 to many relationship."""
    doc = DocumentModel(document_id="doc_rm", filename="file.pdf", document_type="PDF")
    db_session.add(doc)
    db_session.flush()

    clause = ClauseModel(document_id=doc.document_id, clause_id="c_rm", clause_text="Clause text")
    db_session.add(clause)
    db_session.flush()

    ra = RiskAssessmentModel(clause_db_id=clause.id, risk_category="MODIFICATION", risk_level="HIGH", final_score=80.0, risk_explanation="Rule matched")
    db_session.add(ra)
    db_session.flush()

    rm1 = RuleMatchModel(risk_assessment_id=ra.id, rule_id="RULE_MOD_UNILATERAL", category="MODIFICATION", severity=85.0, matched_text="modify terms")
    rm2 = RuleMatchModel(risk_assessment_id=ra.id, rule_id="RULE_TERM_NO_NOTICE", category="TERMINATION", severity=80.0, matched_text="without notice")
    db_session.add_all([rm1, rm2])
    db_session.commit()

    fetched_ra = db_session.scalars(select(RiskAssessmentModel).where(RiskAssessmentModel.id == ra.id)).first()
    assert len(fetched_ra.rule_matches) == 2
    rule_ids = [r.rule_id for r in fetched_ra.rule_matches]
    assert "RULE_MOD_UNILATERAL" in rule_ids
    assert "RULE_TERM_NO_NOTICE" in rule_ids


def test_evidence_citation_persistence(db_session: Session):
    """Requirement 12.H: Test evidence/citation persistence."""
    doc = DocumentModel(document_id="doc_ev", filename="file.pdf", document_type="PDF")
    db_session.add(doc)
    db_session.flush()

    clause = ClauseModel(document_id=doc.document_id, clause_id="c_ev", clause_text="Text")
    db_session.add(clause)
    db_session.flush()

    ra = RiskAssessmentModel(clause_db_id=clause.id, risk_category="WARRANTY", risk_level="LOW", final_score=10.0, risk_explanation="Safe")
    db_session.add(ra)
    db_session.flush()

    ev = EvidenceCitationModel(risk_assessment_id=ra.id, source_clause_id="b_001", source_text="Benchmark clause text", similarity_score=0.88)
    db_session.add(ev)
    db_session.commit()

    fetched_ra = db_session.scalars(select(RiskAssessmentModel).where(RiskAssessmentModel.id == ra.id)).first()
    assert len(fetched_ra.evidence_citations) == 1
    assert fetched_ra.evidence_citations[0].similarity_score == 0.88


def test_future_scenario_persistence(db_session: Session):
    """Requirement 12.I: Test future scenario persistence semantics."""
    doc = DocumentModel(document_id="doc_fs", filename="file.pdf", document_type="PDF")
    db_session.add(doc)
    db_session.flush()

    clause = ClauseModel(document_id=doc.document_id, clause_id="c_fs", clause_text="Text")
    db_session.add(clause)
    db_session.flush()

    ra = RiskAssessmentModel(clause_db_id=clause.id, risk_category="PAYMENT_TERMS", risk_level="MEDIUM", final_score=50.0, risk_explanation="Payment risk")
    db_session.add(ra)
    db_session.flush()

    fs = FutureScenarioModel(
        risk_assessment_id=ra.id,
        scenario_id="scen_99",
        clause_id="c_fs",
        scenario_title="Late Payment Scenario",
        trigger_condition="If payment becomes overdue",
        scenario_description="Service suspension narrative",
        possible_consequence="Operational loss",
        assumptions=["Payment not received"],
        uncertainty="High",
        fallback_active=False,
        disclaimer="Not legal advice"
    )
    db_session.add(fs)
    db_session.commit()

    fetched_ra = db_session.scalars(select(RiskAssessmentModel).where(RiskAssessmentModel.id == ra.id)).first()
    assert fetched_ra.future_scenario is not None
    assert fetched_ra.future_scenario.scenario_title == "Late Payment Scenario"
    assert fetched_ra.future_scenario.trigger_condition == "If payment becomes overdue"


def test_contract_summary_persistence(db_session: Session):
    """Requirement 12.J: Test contract summary persistence."""
    doc = DocumentModel(document_id="doc_sum", filename="summary.pdf", document_type="PDF")
    db_session.add(doc)
    db_session.flush()

    summary = ContractSummaryModel(
        document_id=doc.document_id,
        risk_score=45.66,
        risk_level="MEDIUM",
        high_risk_count=1,
        medium_risk_count=2,
        low_risk_count=4,
        clause_count=7
    )
    db_session.add(summary)
    db_session.commit()

    fetched_doc = db_session.scalars(select(DocumentModel).where(DocumentModel.document_id == "doc_sum")).first()
    assert len(fetched_doc.summaries) == 1
    assert fetched_doc.summaries[0].risk_score == 45.66


def test_transaction_rollback_on_failure(db_session: Session):
    """Requirement 12.K: Test transaction rollback when error occurs."""
    doc = DocumentModel(document_id="doc_rollback", filename="file.pdf", document_type="PDF")
    db_session.add(doc)
    db_session.flush()

    # Attempt to insert a invalid/duplicate record that violates a unique constraint
    doc_dup = DocumentModel(document_id="doc_rollback", filename="file2.pdf", document_type="PDF")
    db_session.add(doc_dup)

    with pytest.raises(Exception):
        db_session.commit()

    db_session.rollback()

    # Verify original transaction was rolled back cleanly
    fetched = db_session.scalars(select(DocumentModel).where(DocumentModel.document_id == "doc_rollback")).first()
    assert fetched is None  # Rollback cleared uncommitted transaction


def test_repository_save_analysis_complete(db_session: Session):
    """Requirement 12.L & M: Test complete atomic analysis persistence and duplicate handling."""
    repo = ContractRepository(db_session)

    dummy_breakdown = RiskScoreBreakdown(
        bert_component=0.0, rule_component=70.0, rag_component=0.0, llm_component=25.0,
        bert_weight=0.0, rule_weight=0.5, rag_weight=0.21, llm_weight=0.29, final_score=42.14
    )

    dummy_rule = RiskRuleMatch(
        rule_id="RULE_SUSPENSION_LATE_PAYMENT",
        risk_category=RiskCategory.TERMINATION,
        pattern=r"suspend.*payment",
        description="Suspension following overdue payment",
        severity_weight=70.0,
        matched_text="suspend services following overdue payment"
    )

    dummy_assessment = RiskAssessment(
        assessment_id="assess_1",
        document_id="doc_full_repo",
        clause_id="c_10_5",
        clause_number="10.5",
        clause_heading="Suspension of Services",
        clause_text="10.5 The Company reserves the right to suspend services following overdue payment.",
        risk_category=RiskCategory.TERMINATION,
        risk_level=RiskLevel.MEDIUM,
        risk_score=42.14,
        score_breakdown=dummy_breakdown,
        clause_type="Other",
        bert_confidence=0.65,
        detected_rules=[dummy_rule],
        risk_explanation="Grounded explanation",
        evidence_summary="No evidence",
        key_risk_factors=["Overdue payment"],
        evidence=[],
        source_pages=[1],
        uncertainty="None"
    )

    dummy_summary = ContractRiskSummary(
        document_id="doc_full_repo",
        source_filename="test.pdf",
        contract_risk_score=42.14,
        contract_risk_level=RiskLevel.MEDIUM,
        analyzed_clauses_count=1,
        high_risk_clauses_count=0,
        medium_risk_clauses_count=1,
        low_risk_clauses_count=0,
        highest_risk_assessments=[dummy_assessment]
    )

    dummy_scenario = FutureScenarioSchema(
        scenario_id="scen_105",
        clause_id="c_10_5",
        clause_number="10.5",
        scenario_title="Suspension Following Overdue Payment",
        trigger_condition="If payment becomes overdue",
        scenario_description="Narrative",
        possible_consequence="Operational loss",
        supporting_evidence=[],
        assumptions=["Overdue"],
        uncertainty="None",
        fallback_active=False,
        disclaimer="Disclaimer"
    )

    # First save
    saved_doc = repo.save_analysis(
        summary=dummy_summary,
        all_assessments=[dummy_assessment],
        scenario_map={"c_10_5": dummy_scenario},
        filename="test.pdf",
        document_type="PDF"
    )
    db_session.commit()

    assert saved_doc.document_id == "doc_full_repo"
    assert len(saved_doc.clauses) == 1
    assert saved_doc.clauses[0].risk_assessment.final_score == 42.14
    assert len(saved_doc.clauses[0].risk_assessment.rule_matches) == 1

    # Duplicate / Re-analysis save (Requirement 12.M)
    updated_doc = repo.save_analysis(
        summary=dummy_summary,
        all_assessments=[dummy_assessment],
        scenario_map={"c_10_5": dummy_scenario},
        filename="test.pdf",
        document_type="PDF"
    )
    db_session.commit()

    assert updated_doc.document_id == "doc_full_repo"
    assert len(updated_doc.clauses) == 1
