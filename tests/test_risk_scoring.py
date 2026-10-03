"""
Unit tests for BERTRiskMapper, HybridScorer, and Contract Aggregation in Phase 7.1.
"""

import pytest
from src.risk_analysis.bert_risk_mapper import BERTRiskMapper
from src.risk_analysis.scoring import HybridScorer
from src.risk_analysis.models import (
    RiskCategory,
    RiskLevel,
    RiskRuleMatch,
    RiskAssessment,
    RiskScoreBreakdown
)


def test_bert_risk_mapper_scaling():
    mapper = BERTRiskMapper()
    # Uncapped Liability base weight is 95.0
    weight_full = mapper.calculate_bert_component_score("Uncapped Liability", 1.0)
    assert weight_full == 95.0

    weight_half = mapper.calculate_bert_component_score("Uncapped Liability", 0.5)
    assert weight_half == 47.5

    # Low confidence clamping
    weight_zero = mapper.calculate_bert_component_score("Uncapped Liability", 0.0)
    assert weight_zero == 0.0

    # Unknown category fallback (default base weight 0.0 under Phase 8.1 calibration)
    unknown_score = mapper.calculate_bert_component_score("NonExistentCategory", 1.0)
    assert unknown_score == 0.0


def test_asymptotic_rule_score_aggregation():
    scorer = HybridScorer()
    matches = [
        RiskRuleMatch(
            rule_id="R1",
            risk_category=RiskCategory.LIABILITY,
            pattern="p1",
            description="d1",
            severity_weight=50.0,
            matched_text="m1"
        ),
        RiskRuleMatch(
            rule_id="R2",
            risk_category=RiskCategory.LIABILITY,
            pattern="p2",
            description="d2",
            severity_weight=50.0,
            matched_text="m2"
        )
    ]
    # S_rule = 100 * (1 - (1 - 0.5) * (1 - 0.5)) = 100 * (1 - 0.25) = 75.0
    rule_score = scorer.calculate_rule_component_score(matches)
    assert rule_score == 75.0


def test_hybrid_score_exact_weights():
    scorer = HybridScorer()
    # 30% BERT(100) + 35% Rule(100) + 15% RAG(100) + 20% LLM(100) = 100.0
    breakdown_max = scorer.compute_hybrid_score(100.0, 100.0, 100.0, 100.0)
    assert breakdown_max.final_score == 100.0

    # 30% * 50 + 35% * 40 + 15% * 20 + 20% * 60 = 15 + 14 + 3 + 12 = 44.0
    breakdown_custom = scorer.compute_hybrid_score(50.0, 40.0, 20.0, 60.0)
    assert breakdown_custom.final_score == 44.0


def test_risk_level_thresholds():
    scorer = HybridScorer()
    assert scorer.determine_risk_level(10.0) == RiskLevel.LOW
    assert scorer.determine_risk_level(34.9) == RiskLevel.LOW
    assert scorer.determine_risk_level(35.0) == RiskLevel.MEDIUM
    assert scorer.determine_risk_level(69.9) == RiskLevel.MEDIUM
    assert scorer.determine_risk_level(70.0) == RiskLevel.HIGH
    assert scorer.determine_risk_level(95.0) == RiskLevel.HIGH


def test_contract_risk_aggregation():
    scorer = HybridScorer()

    def make_dummy_assessment(score: float, level: RiskLevel) -> RiskAssessment:
        return RiskAssessment(
            assessment_id="a1",
            document_id="doc1",
            clause_id="c1",
            clause_number="1.1",
            clause_heading="Heading",
            clause_text="Text",
            clause_type="Cap On Liability",
            bert_confidence=0.9,
            risk_category=RiskCategory.LIABILITY,
            risk_score=score,
            risk_level=level,
            score_breakdown=RiskScoreBreakdown(
                bert_component=score,
                rule_component=score,
                rag_component=score,
                llm_component=score,
                final_score=score
            ),
            detected_rules=[],
            risk_explanation="Exp",
            evidence_summary="Sum",
            key_risk_factors=[],
            evidence=[],
            source_pages=[1],
            uncertainty="None"
        )

    assessments = [
        make_dummy_assessment(90.0, RiskLevel.HIGH),
        make_dummy_assessment(30.0, RiskLevel.LOW),
        make_dummy_assessment(30.0, RiskLevel.LOW),
    ]
    # Max = 90.0, Mean = (90 + 30 + 30) / 3 = 50.0
    # Contract Score = 0.6 * 90.0 + 0.4 * 50.0 = 54.0 + 20.0 = 74.0
    summary = scorer.aggregate_contract_risk("doc1", "contract.pdf", assessments)
    assert summary.contract_risk_score == 74.0
    assert summary.contract_risk_level == RiskLevel.HIGH
    assert summary.analyzed_clauses_count == 3
    assert summary.high_risk_clauses_count == 1
    assert summary.low_risk_clauses_count == 2
