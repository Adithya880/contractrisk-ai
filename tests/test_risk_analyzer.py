"""
Unit tests for ContractRiskAnalyzer facade with mocked LLM/RAG subcomponents.
"""

from unittest.mock import MagicMock
import pytest

from src.clause_segmentation.models import SegmentedClause, SegmentationResult
from src.document_processing.models import SourceType
from src.risk_analysis.analyzer import ContractRiskAnalyzer
from src.risk_analysis.models import RiskLevel, RiskCategory


@pytest.fixture
def sample_segmented_clause():
    text = "In no event shall Vendor be subject to any cap on liability for gross negligence."
    return SegmentedClause(
        clause_id="c_001",
        document_id="doc_100",
        clause_number="12.1",
        clause_heading="Limitation of Liability",
        clause_text=text,
        source_type=SourceType.PDF,
        source_pages=[4],
        character_count=len(text),
        word_count=len(text.split())
    )


@pytest.fixture
def sample_segmentation_result(sample_segmented_clause):
    text_len = sample_segmented_clause.character_count
    return SegmentationResult(
        document_id="doc_100",
        source_filename="master_services_agreement.pdf",
        clauses=[sample_segmented_clause],
        total_clauses=1,
        source_character_count=text_len,
        segmented_character_count=text_len,
        text_coverage_ratio=1.0
    )


def test_analyzer_analyze_clause_fallback_llm(sample_segmented_clause):
    # Mock LLM generator throwing connection exception
    mock_generator = MagicMock()
    mock_generator.generate.side_effect = Exception("LM Studio Offline")

    analyzer = ContractRiskAnalyzer(generator=mock_generator)
    assessment = analyzer.analyze_clause(
        clause=sample_segmented_clause,
        document_id="doc_100",
        predicted_clause_type="Uncapped Liability",
        bert_confidence=0.9
    )

    assert assessment.clause_id == "c_001"
    assert assessment.clause_type == "Uncapped Liability"
    assert assessment.risk_score > 50.0
    assert assessment.risk_level in [RiskLevel.MEDIUM, RiskLevel.HIGH]
    assert "Fallback mode active" in assessment.uncertainty


def test_analyzer_analyze_clause_with_mock_llm(sample_segmented_clause):
    mock_generator = MagicMock()
    mock_generator.generate.return_value = {
        "risk_explanation": "Clause creates uncapped exposure for gross negligence.",
        "key_risk_factors": ["Uncapped financial risk", "Gross negligence liability"],
        "llm_score": 85.0,
        "uncertainty": "Low uncertainty."
    }

    analyzer = ContractRiskAnalyzer(generator=mock_generator)
    assessment = analyzer.analyze_clause(
        clause=sample_segmented_clause,
        document_id="doc_100",
        predicted_clause_type="Uncapped Liability",
        bert_confidence=0.95
    )

    assert assessment.risk_score >= 70.0
    assert assessment.risk_level == RiskLevel.HIGH
    assert assessment.score_breakdown.llm_component == 85.0
    assert "gross negligence" in assessment.risk_explanation.lower()


def test_analyzer_analyze_document(sample_segmentation_result):
    mock_generator = MagicMock()
    mock_generator.generate.return_value = {
        "risk_explanation": "High liability clause.",
        "key_risk_factors": ["Liability exposure"],
        "llm_score": 80.0,
        "uncertainty": "Minimal."
    }

    analyzer = ContractRiskAnalyzer(generator=mock_generator)
    summary = analyzer.analyze_document(sample_segmentation_result)

    assert summary.document_id == "doc_100"
    assert summary.source_filename == "master_services_agreement.pdf"
    assert summary.analyzed_clauses_count == 1
    assert summary.contract_risk_score > 0.0
    assert len(summary.highest_risk_assessments) == 1
