"""
Unit and Integration Tests for Phase 8.1 Risk Analysis Calibration & Scenario Consistency.
Tests requirements A through G:
A. Clause 2.3 must not trigger warranty disclaimer.
B. Clause 5.1 must not generate a generic Low Risk Baseline scenario.
C. Clause 10.4 must not generate a generic Low Risk Baseline scenario.
D. Clause 10.5 must not generate a generic Low Risk Baseline scenario.
E. Clause 10.6 must not generate a generic Low Risk Baseline scenario.
F. BERT 'Other' must not automatically create a strong risk contribution merely because confidence is 1.0.
G. Scenario output must remain conditional and evidence-grounded.
"""

import pytest
from src.clause_segmentation.models import SegmentedClause
from src.risk_analysis.rule_engine import RuleEngine
from src.risk_analysis.bert_risk_mapper import BERTRiskMapper
from src.risk_analysis.scoring import HybridScorer
from src.risk_analysis.analyzer import ContractRiskAnalyzer
from src.risk_analysis.scenario_predictor import FutureScenarioPredictor
from src.risk_analysis.models import RiskLevel, RiskCategory


@pytest.fixture
def rule_engine():
    return RuleEngine()


@pytest.fixture
def bert_mapper():
    return BERTRiskMapper()


@pytest.fixture
def scorer():
    return HybridScorer()


@pytest.fixture
def analyzer():
    return ContractRiskAnalyzer()


@pytest.fixture
def predictor():
    return FutureScenarioPredictor()


# --- TEST A: Clause 2.3 Warranty Preservation ---
def test_clause_2_3_warranty_preservation(rule_engine):
    """Clause 2.3 preserves warranties/remedies and must NOT match RULE_WARRANTY_DISCLAIMER."""
    clause_text = (
        "2.3 Nothing in these Terms and Conditions shall prejudice any condition or warranty, "
        "express or implied, or any legal remedy to which the Buyer may be entitled under statute or common law."
    )
    matches = rule_engine.analyze_clause(clause_text)
    rule_ids = [m.rule_id for m in matches]
    assert "RULE_WARRANTY_DISCLAIMER" not in rule_ids, "Clause 2.3 falsely triggered RULE_WARRANTY_DISCLAIMER!"


def test_positive_warranty_disclaimer_matching(rule_engine):
    """Positive warranty disclaimers must be detected correctly."""
    disclaimer_text = (
        "Company disclaims all warranties express or implied including any implied warranty "
        "of merchantability or fitness for a particular purpose. Products are provided as is."
    )
    matches = rule_engine.analyze_clause(disclaimer_text)
    rule_ids = [m.rule_id for m in matches]
    assert "RULE_WARRANTY_DISCLAIMER" in rule_ids, "Actual warranty disclaimer failed to match RULE_WARRANTY_DISCLAIMER!"


# --- TEST F: BERT "Other" Confidence 1.0 Calibration ---
def test_bert_other_zero_contribution(bert_mapper, scorer):
    """BERT 'Other' category must output 0.0 component score regardless of 1.0 confidence."""
    score = bert_mapper.calculate_bert_component_score("Other", 1.0)
    assert score == 0.0, f"BERT 'Other' returned non-zero score {score}!"

    weight, cat = bert_mapper.get_clause_risk_info("Other")
    assert weight == 0.0, f"BERT 'Other' base weight should be 0.0, got {weight}"
    assert cat == RiskCategory.OTHER


def test_hybrid_score_transparent_weights(scorer):
    """When BERT is 0.0 (Other), transparent weights strictly apply without silent rescaling."""
    # Rule = 70 (0.35 * 70 = 24.5), LLM = 75 (0.20 * 75 = 15.0), BERT = 0, RAG = 0 -> Final = 39.5
    breakdown = scorer.compute_hybrid_score(
        bert_score=0.0,
        rule_score=70.0,
        rag_score=0.0,
        llm_score=75.0
    )
    assert breakdown.final_score == 39.5, f"Expected transparent score 39.5, got {breakdown.final_score}"
    assert breakdown.final_score >= 35.0, f"Score {breakdown.final_score} is correctly in MEDIUM risk range"


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


# --- TESTS B, C, D, E: Non-Generic Scenarios for Clauses 5.1, 10.4, 10.5, 10.6 ---
def test_clause_5_1_non_generic_scenario(analyzer, predictor):
    """Clause 5.1 must produce an evidence-grounded non-generic scenario."""
    clause = _make_clause(
        clause_id="tc:clause:5.1",
        clause_number="5.1",
        clause_heading="Prices and Payment",
        clause_text="5.1 Prices quoted are subject to alteration without notice. Payment shall be due within 30 days of invoice date.",
        page=1
    )
    assessment = analyzer.analyze_clause(clause, document_id="tc_doc")
    scenario = predictor.predict_scenario(assessment)

    assert "Low Risk Baseline" not in scenario.scenario_title
    assert "standard commercial language" not in scenario.scenario_description
    assert "No significant adverse scenario is anticipated" not in scenario.scenario_description
    assert "minimal litigation exposure" not in scenario.uncertainty
    assert any(term in scenario.scenario_description.lower() or term in scenario.trigger_condition.lower()
               for term in ["price", "payment", "alteration", "notice", "invoice"])


def test_clause_10_4_non_generic_scenario(analyzer, predictor):
    """Clause 10.4 must produce a conditional scenario around termination without notice/refund."""
    clause = _make_clause(
        clause_id="tc:clause:10.4",
        clause_number="10.4",
        clause_heading="Termination",
        clause_text="10.4 The Company may terminate this Agreement immediately without prior notice or refund of prepaid fees if Buyer fails to comply with any provision hereof.",
        page=2
    )
    assessment = analyzer.analyze_clause(clause, document_id="tc_doc")
    scenario = predictor.predict_scenario(assessment)

    assert "Low Risk Baseline" not in scenario.scenario_title
    assert "standard commercial language" not in scenario.scenario_description
    assert any(term in scenario.scenario_description.lower() or term in scenario.trigger_condition.lower()
               for term in ["terminat", "notice", "refund", "prepaid", "breach", "compl"])


def test_clause_10_5_non_generic_scenario(analyzer, predictor):
    """Clause 10.5 must produce a conditional scenario around service suspension on overdue payment."""
    clause = _make_clause(
        clause_id="tc:clause:10.5",
        clause_number="10.5",
        clause_heading="Suspension",
        clause_text="10.5 The Company reserves the right to suspend or terminate services and access immediately following overdue payment or non-payment of any amounts due.",
        page=2
    )
    assessment = analyzer.analyze_clause(clause, document_id="tc_doc")
    scenario = predictor.predict_scenario(assessment)

    assert "Low Risk Baseline" not in scenario.scenario_title
    assert "standard commercial language" not in scenario.scenario_description
    assert any(term in scenario.scenario_description.lower() or term in scenario.trigger_condition.lower()
               for term in ["suspend", "terminat", "overdue", "payment", "access"])


def test_clause_10_6_non_generic_scenario(analyzer, predictor):
    """Clause 10.6 must produce a conditional scenario around reinstatement requiring approval and new fees/terms."""
    clause = _make_clause(
        clause_id="tc:clause:10.6",
        clause_number="10.6",
        clause_heading="Reinstatement",
        clause_text="10.6 Reinstatement of suspended services or accounts shall require prior written approval by the Company and may be subject to new or different administrative fees and updated commercial terms.",
        page=2
    )
    assessment = analyzer.analyze_clause(clause, document_id="tc_doc")
    scenario = predictor.predict_scenario(assessment)

    assert "Low Risk Baseline" not in scenario.scenario_title
    assert "standard commercial language" not in scenario.scenario_description
    assert any(term in scenario.scenario_description.lower() or term in scenario.trigger_condition.lower()
               for term in ["reinstat", "approval", "fee", "term", "suspend"])


# --- TEST G: Scenario Conditional Phrasing and Evidence Grounding ---
def test_scenario_conditional_phrasing_and_grounding(analyzer, predictor):
    """Scenario output must remain strictly conditional and evidence-grounded."""
    clause = _make_clause(
        clause_id="tc:clause:test",
        clause_number="14.2",
        clause_heading="Limitation of Liability",
        clause_text="14.2 Vendor shall have unlimited liability for gross negligence.",
        page=3
    )
    assessment = analyzer.analyze_clause(clause, document_id="tc_doc")
    scenario = predictor.predict_scenario(assessment)

    # Check conditional phrasing trigger
    trigger_lower = scenario.trigger_condition.lower()
    assert any(cond in trigger_lower for cond in ["if", "should", "in the event", "were to"]), f"Trigger lacks conditional phrasing: {scenario.trigger_condition}"

    # Check no fluff
    assert "standard commercial language" not in scenario.scenario_description
    assert "minimal litigation exposure" not in scenario.uncertainty
