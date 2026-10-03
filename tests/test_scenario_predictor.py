"""
Unit tests for Phase 7.2 / Phase 7.2.1 Future Scenario Predictor.
Tests scenario generation across High, Medium, Low risk levels, malformed JSON fallbacks,
anti-hallucination checks, conditional phrasing enforcement, and uncertainty preservation.
"""

from unittest.mock import MagicMock
import pytest

from src.rag.models import Citation
from src.risk_analysis.models import (
    RiskCategory,
    RiskLevel,
    RiskRuleMatch,
    RiskScoreBreakdown,
    RiskAssessment
)
from src.risk_analysis.scenario_models import FutureScenario
from src.risk_analysis.scenario_predictor import FutureScenarioPredictor


@pytest.fixture
def sample_high_risk_assessment():
    return RiskAssessment(
        assessment_id="assess_high_01",
        document_id="doc_100",
        clause_id="c_142",
        clause_number="14.2",
        clause_heading="Limitation of Liability & Indemnification",
        clause_text="Vendor shall have unlimited liability for gross negligence. Customer agrees to defend, indemnify and hold harmless Vendor from all claims.",
        clause_type="Uncapped Liability",
        bert_confidence=0.95,
        risk_category=RiskCategory.LIABILITY,
        risk_score=78.74,
        risk_level=RiskLevel.HIGH,
        score_breakdown=RiskScoreBreakdown(
            bert_component=90.0,
            rule_component=95.0,
            rag_component=0.0,
            llm_component=85.0,
            final_score=78.74
        ),
        detected_rules=[
            RiskRuleMatch(
                rule_id="RULE_LIAB_UNLIMITED",
                risk_category=RiskCategory.LIABILITY,
                pattern="unlimited liability",
                description="Clause creates or imposes unlimited liability",
                severity_weight=95.0,
                matched_text="unlimited liability"
            )
        ],
        risk_explanation="Broad indemnification and uncapped liability clause.",
        evidence_summary="Retrieved 1 benchmark clause.",
        key_risk_factors=["Uncapped financial exposure"],
        evidence=[{"clause_id": "c_bench_01", "clause_number": "5.1", "source_pages": [12]}],
        source_pages=[5],
        uncertainty="Moderate uncertainty."
    )


@pytest.fixture
def sample_medium_risk_assessment():
    return RiskAssessment(
        assessment_id="assess_med_01",
        document_id="doc_100",
        clause_id="c_81",
        clause_number="8.1",
        clause_heading="Non-Compete & Auto-Renewal",
        clause_text="Contractor shall not engage in competing business for 2 years. This Agreement shall automatically renew.",
        clause_type="Non-Compete",
        bert_confidence=0.88,
        risk_category=RiskCategory.NON_COMPETE,
        risk_score=55.0,
        risk_level=RiskLevel.MEDIUM,
        score_breakdown=RiskScoreBreakdown(
            bert_component=70.0,
            rule_component=60.0,
            rag_component=0.0,
            llm_component=50.0,
            final_score=55.0
        ),
        detected_rules=[
            RiskRuleMatch(
                rule_id="RULE_RENEWAL_AUTO",
                risk_category=RiskCategory.RENEWAL,
                pattern="automatically renew",
                description="Automatic renewal clause",
                severity_weight=60.0,
                matched_text="automatically renew"
            )
        ],
        risk_explanation="Auto-renewal and non-compete clause.",
        evidence_summary="No evidence.",
        key_risk_factors=["Restrictive non-compete"],
        evidence=[],
        source_pages=[3],
        uncertainty="Low uncertainty."
    )


@pytest.fixture
def sample_low_risk_assessment():
    return RiskAssessment(
        assessment_id="assess_low_01",
        document_id="doc_100",
        clause_id="c_11",
        clause_number="1.1",
        clause_heading="Effective Date",
        clause_text="This Agreement is entered into on October 1, 2026.",
        clause_type="Effective Date",
        bert_confidence=0.98,
        risk_category=RiskCategory.OTHER,
        risk_score=10.0,
        risk_level=RiskLevel.LOW,
        score_breakdown=RiskScoreBreakdown(
            bert_component=10.0,
            rule_component=0.0,
            rag_component=0.0,
            llm_component=20.0,
            final_score=10.0
        ),
        detected_rules=[],
        risk_explanation="Standard effective date provision.",
        evidence_summary="No evidence.",
        key_risk_factors=[],
        evidence=[],
        source_pages=[1],
        uncertainty="Minimal."
    )


def test_predict_scenario_high_risk_mocked_llm(sample_high_risk_assessment):
    mock_generator = MagicMock()
    mock_generator.generate.return_value = {
        "scenario_title": "Uncapped Liability & Third-Party Indemnity Claim",
        "trigger_condition": "If a third-party customer files a gross negligence lawsuit against Vendor.",
        "scenario_description": "If a third party sues the Vendor, the broad indemnity clause could force Customer to defend Vendor without any financial cap.",
        "possible_consequence": "Severe unmitigated financial losses for Customer.",
        "assumptions": ["Lawsuit filed in jurisdiction enforcing broad indemnities", "No insurance coverage applies"],
        "uncertainty": "Court enforceability depends on specific state public policy on gross negligence indemnification."
    }

    predictor = FutureScenarioPredictor(generator=mock_generator)
    scenario = predictor.predict_scenario(sample_high_risk_assessment)

    assert isinstance(scenario, FutureScenario)
    assert scenario.scenario_title == "Uncapped Liability & Third-Party Indemnity Claim"
    assert "If a third-party" in scenario.trigger_condition
    assert len(scenario.supporting_evidence) == 2  # Primary clause + 1 benchmark citation
    assert scenario.fallback_active is False


def test_predict_scenario_medium_risk_mocked_llm(sample_medium_risk_assessment):
    mock_generator = MagicMock()
    mock_generator.generate.return_value = {
        "scenario_title": "Unexpected Contract Extension & Trade Restriction",
        "trigger_condition": "If Contractor fails to send non-renewal notice prior to expiration.",
        "scenario_description": "The agreement automatically renews for another full term while non-compete remains active.",
        "possible_consequence": "Locked into another term while restricted from taking new clients.",
        "assumptions": ["Notice window missed", "Contract terms enforced strictly"],
        "uncertainty": "Geographic scope ambiguity may affect non-compete enforceability."
    }

    predictor = FutureScenarioPredictor(generator=mock_generator)
    scenario = predictor.predict_scenario(sample_medium_risk_assessment)

    assert scenario.clause_id == "c_81"
    assert "If Contractor fails" in scenario.trigger_condition
    assert scenario.fallback_active is False


def test_predict_scenario_low_risk_baseline(sample_low_risk_assessment):
    mock_generator = MagicMock()
    mock_generator.generate.return_value = {
        "scenario_title": "Potential Other Scenario (1.1)",
        "trigger_condition": "If standard contractual performance occurs as specified.",
        "scenario_description": "Under Clause 1.1, provisions stipulate routine performance.",
        "possible_consequence": "Routine contractual performance.",
        "assumptions": ["Parties perform obligations in good faith"],
        "uncertainty": "Grounded in clause text."
    }
    predictor = FutureScenarioPredictor(generator=mock_generator)
    scenario = predictor.predict_scenario(sample_low_risk_assessment)

    assert scenario.clause_id == "c_11"
    assert "Low Risk Baseline" not in scenario.scenario_title
    assert scenario.fallback_active is False
    mock_generator.generate.assert_called_once()


def test_predict_scenario_malformed_llm_json_fallback(sample_high_risk_assessment):
    mock_generator = MagicMock()
    mock_generator.generate.side_effect = Exception("LM Studio returned invalid non-JSON string")

    predictor = FutureScenarioPredictor(generator=mock_generator)
    scenario = predictor.predict_scenario(sample_high_risk_assessment)

    assert isinstance(scenario, FutureScenario)
    assert scenario.fallback_active is True
    assert "Fallback" in scenario.scenario_title
    assert "Fallback execution mode active" in scenario.uncertainty


def test_predict_scenario_connection_error_fallback(sample_high_risk_assessment):
    mock_generator = MagicMock()
    mock_generator.generate.side_effect = Exception("Connection refused at http://127.0.0.1:1234/v1")

    predictor = FutureScenarioPredictor(generator=mock_generator)
    scenario = predictor.predict_scenario(sample_high_risk_assessment)

    assert scenario.fallback_active is True
    assert scenario.clause_id == "c_142"
    assert len(scenario.supporting_evidence) == 2


# --- PHASE 7.2.1 GROUNDING HARDENING TESTS ---

def test_enforce_conditional_phrasing_on_trigger(sample_high_risk_assessment):
    """Verify that trigger conditions lacking conditional language are automatically formatted conditionally."""
    mock_generator = MagicMock()
    mock_generator.generate.return_value = {
        "scenario_title": "Uncapped Risk",
        "trigger_condition": "Customer files a breach claim",  # Non-conditional phrasing
        "scenario_description": "Liability is uncapped.",
        "possible_consequence": "Financial loss.",
        "assumptions": ["Literal enforcement"],
        "uncertainty": "Jurisdictional variability."
    }

    predictor = FutureScenarioPredictor(generator=mock_generator)
    scenario = predictor.predict_scenario(sample_high_risk_assessment)

    assert scenario.trigger_condition.startswith("If a dispute or trigger event were to occur regarding:")
    assert "Customer files a breach claim" in scenario.trigger_condition


def test_uncertainty_preservation_on_ambiguous_clause(sample_high_risk_assessment):
    """Verify that uncertainty notes are preserved and enriched when financial caps are unstated."""
    mock_generator = MagicMock()
    mock_generator.generate.return_value = {
        "scenario_title": "Uncapped Risk",
        "trigger_condition": "If a claim arises",
        "scenario_description": "Liability is uncapped.",
        "possible_consequence": "Financial loss.",
        "assumptions": ["Literal enforcement"],
        "uncertainty": "Court interpretation varies."
    }

    predictor = FutureScenarioPredictor(generator=mock_generator)
    scenario = predictor.predict_scenario(sample_high_risk_assessment)

    assert "Specific financial limit is unstated in clause text." in scenario.uncertainty


def test_anti_hallucination_fact_assumption_isolation(sample_medium_risk_assessment):
    """Verify that assumptions remain strictly isolated from factual scenario description."""
    mock_generator = MagicMock()
    mock_generator.generate.return_value = {
        "scenario_title": "Non-Compete Renewal Risk",
        "trigger_condition": "If Contractor attempts to engage in competing business during renewal.",
        "scenario_description": "The clause contains non-compete restrictions and automatic renewal provisions.",
        "possible_consequence": "Potential breach of contract action.",
        "assumptions": ["Contractor operates in same geographic market", "No waiver given"],
        "uncertainty": "Geographic scope unstated in clause."
    }

    predictor = FutureScenarioPredictor(generator=mock_generator)
    scenario = predictor.predict_scenario(sample_medium_risk_assessment)

    assert len(scenario.assumptions) == 2
    assert "Contractor operates in same geographic market" in scenario.assumptions
    assert "Geographic scope unstated" in scenario.uncertainty
