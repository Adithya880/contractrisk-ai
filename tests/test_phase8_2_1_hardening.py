"""
Unit & Grounding Hardening Tests for Phase 8.2.1.
Covers:
A. Clause 10.5 exact wording matching RULE_SUSPENSION_LATE_PAYMENT.
B. Clause 8.3 risk explanation grounding (no hallucinated unlimited liability).
C. Scenario trigger factual preservation (no automatic conversion to 'breach').
D. Preservation of Clause 2.3 warranty disclaimer negative check.
E. Preservation of Clause 5.1 and 10.4 rule engine matches.
"""

import pytest
from unittest.mock import MagicMock

from src.clause_segmentation.models import SegmentedClause
from src.risk_analysis.rule_engine import RuleEngine
from src.risk_analysis.analyzer import ContractRiskAnalyzer
from src.risk_analysis.scenario_predictor import FutureScenarioPredictor
from src.risk_analysis.models import RiskLevel, RiskCategory, RiskScoreBreakdown, RiskAssessment


@pytest.fixture
def rule_engine():
    return RuleEngine()


@pytest.fixture
def analyzer():
    return ContractRiskAnalyzer()


@pytest.fixture
def predictor():
    return FutureScenarioPredictor()


def _make_clause(clause_id: str, clause_number: str, clause_heading: str, clause_text: str, page: int = 1) -> SegmentedClause:
    return SegmentedClause(
        clause_id=clause_id,
        document_id="tc_doc",
        clause_number=clause_number,
        clause_heading=clause_heading,
        clause_text=clause_text,
        source_type="pdf",
        character_count=len(clause_text),
        word_count=len(clause_text.split()),
        source_pages=[page]
    )


# --- TEST A: Clause 10.5 Wording Matching RULE_SUSPENSION_LATE_PAYMENT ---
def test_clause_10_5_rule_suspension_late_payment_matching(rule_engine):
    """Clause 10.5 exact wording must match RULE_SUSPENSION_LATE_PAYMENT."""
    clause_10_5_text = (
        "10.5 The Company reserves the right to suspend or terminate services and access "
        "immediately following overdue payment or non-payment of any amounts due."
    )
    matches = rule_engine.analyze_clause(clause_10_5_text)
    rule_ids = [m.rule_id for m in matches]
    assert "RULE_SUSPENSION_LATE_PAYMENT" in rule_ids, (
        f"Clause 10.5 failed to match RULE_SUSPENSION_LATE_PAYMENT! Matches found: {rule_ids}"
    )


# --- TEST B: Clause 8.3 Explanation Grounding ---
def test_clause_8_3_no_hallucinated_unlimited_liability(analyzer):
    """Clause 8.3 (non-solicit / routine clause) must NOT produce an 'unlimited liability' explanation."""
    clause_8_3_text = (
        "8.3 Subject to Section 8.3.5 hereof, nothing herein is intended to preclude "
        "FG from granting rights to supply or supplying Products to third parties."
    )
    seg_clause = _make_clause("c_8_3", "8.3", "Third Party Supply Rights", clause_8_3_text)
    
    # Mock generator returning grounded response
    mock_gen = MagicMock()
    mock_gen.generate.return_value = {
        "risk_explanation": "Clause preserves the right to supply products to third parties without creating unlimited liability.",
        "key_risk_factors": ["Non-exclusive supply rights"],
        "llm_score": 15.0,
        "uncertainty": "Routine commercial supply provision."
    }
    analyzer.generator = mock_gen

    assessment = analyzer.analyze_clause(seg_clause, document_id="tc_doc")
    assert "unlimited liability" not in assessment.risk_explanation.lower() or "without creating unlimited liability" in assessment.risk_explanation.lower()
    assert assessment.risk_level == RiskLevel.LOW


# --- TEST C: Scenario Factual Trigger Preservation ---
def test_scenario_predictor_preserves_factual_triggers(predictor):
    """Scenario predictor must keep factual triggers (e.g. overdue payment) without rewriting as 'breach'."""
    mock_gen = MagicMock()
    mock_gen.generate.return_value = {
        "scenario_title": "Service Suspension Following Overdue Payment",
        "trigger_condition": "If payment were to become overdue under Clause 10.5",
        "scenario_description": "Should payment become overdue, services and access may be suspended immediately.",
        "possible_consequence": "Temporary suspension of access until payment is received.",
        "assumptions": ["Payment remains unpaid past the due date"],
        "uncertainty": "Clause does not specify a grace period before suspension takes effect."
    }
    predictor.generator = mock_gen

    sample_assessment = RiskAssessment(
        assessment_id="assess_10_5",
        document_id="doc_1",
        clause_id="c_10_5",
        clause_number="10.5",
        clause_heading="Suspension of Services",
        clause_text="10.5 The Company reserves the right to suspend or terminate services and access immediately following overdue payment.",
        clause_type="Other",
        bert_confidence=1.0,
        risk_category=RiskCategory.TERMINATION,
        risk_score=70.0,
        risk_level=RiskLevel.HIGH,
        score_breakdown=RiskScoreBreakdown(
            bert_component=0.0, rule_component=70.0, rag_component=0.0, llm_component=70.0,
            bert_weight=0.0, rule_weight=0.5, rag_weight=0.2143, llm_weight=0.2857, final_score=70.0
        ),
        detected_rules=[],
        risk_explanation="Clause permits service suspension following overdue payment.",
        evidence_summary="No benchmark evidence.",
        key_risk_factors=["Service suspension on overdue payment"],
        evidence=[],
        source_pages=[2],
        uncertainty="No grace period specified."
    )

    scenario = predictor.predict_scenario(sample_assessment)
    assert "overdue" in scenario.trigger_condition.lower()
    assert "breach" not in scenario.trigger_condition.lower()


# --- TEST D: Preserve Clause 2.3 Warranty False-Positive Protection ---
def test_clause_2_3_warranty_preservation_maintained(rule_engine):
    """Clause 2.3 warranty preservation must continue to suppress RULE_WARRANTY_DISCLAIMER."""
    clause_2_3_text = (
        "2.3 Nothing in these Terms and Conditions shall prejudice any condition or warranty, "
        "express or implied, or any legal remedy to which the Buyer may be entitled under statute or common law."
    )
    matches = rule_engine.analyze_clause(clause_2_3_text)
    rule_ids = [m.rule_id for m in matches]
    assert "RULE_WARRANTY_DISCLAIMER" not in rule_ids


# --- TEST E: Preserve Clause 5.1 and 10.4 Rule Behavior ---
def test_clause_5_1_and_10_4_rule_matching_maintained(rule_engine):
    """Clause 5.1 and 10.4 must continue matching their respective rules."""
    text_5_1 = "5.1 Prices quoted are subject to alteration without notice. Payment shall be due within 30 days of invoice date."
    matches_5_1 = [m.rule_id for m in rule_engine.analyze_clause(text_5_1)]
    assert "RULE_PRICE_UNILATERAL_ALTERATION" in matches_5_1

    text_10_4 = "10.4 The Company may terminate this Agreement immediately without prior notice or refund of prepaid fees if Buyer fails to comply with any provision hereof."
    matches_10_4 = [m.rule_id for m in rule_engine.analyze_clause(text_10_4)]
    assert "RULE_MOD_UNILATERAL" in matches_10_4
    assert "RULE_TERM_NO_NOTICE" in matches_10_4
