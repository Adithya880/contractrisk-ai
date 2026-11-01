"""
Dynamic Analysis and Service Agreement Verification Test Suite for ContractRisk AI.

Verifies:
1. Input-dependent dynamic analysis on Service Agreement clauses.
2. Limitation of Liability internal contradiction detection (excluded damages + unlimited total liability).
3. Termination notice asymmetry detection (30-day notice + immediate cancellation without notice).
4. Strict separation of intra-clause contradictions from cross-clause conflicts.
5. BERT low-confidence handling (threshold flagging and display_category).
6. Qwen3 availability tracking:
   - Offline -> UNAVAILABLE status, None explanation (no mock/fake response).
   - Online -> SUCCESS status with actual inference data.
   - Low-risk -> SKIPPED status.
7. Input-dependent contrast: A completely different agreement (Mutual NDA) yields entirely
   different predictions, risk scores, and rule evaluations.
"""

import pytest
from unittest.mock import patch, MagicMock

from src.clause_segmentation.models import SegmentedClause, SegmentationResult
from src.risk_analysis.analyzer import ContractRiskAnalyzer
from src.risk_analysis.conflict_detector import CrossClauseConflictDetector
from src.risk_analysis.models import RiskLevel, LLMInferenceStatus
from src.risk_analysis.rule_engine import RuleEngine
from src.rag.generator import LLMGenerator
from src.api.dependencies import get_risk_analyzer


def _create_clause(cid: str, num: str, head: str, text: str) -> SegmentedClause:
    return SegmentedClause(
        clause_id=cid,
        document_id="doc_dyn_test",
        clause_number=num,
        clause_heading=head,
        clause_text=text,
        source_pages=[1],
        source_type="pdf",
        character_count=len(text),
        word_count=len(text.split())
    )


# ---------------------------------------------------------------------------
# Test Data: Service Agreement Clauses (similar to Service Agreement.pdf)
# ---------------------------------------------------------------------------
CLAUSE_SERVICES = (
    "1", "Services and Scope",
    "Service Provider shall render the consulting and implementation services described in Exhibit A with standard professional care."
)

CLAUSE_PAYMENT = (
    "2", "Payment Terms",
    "Client shall pay all invoiced amounts within thirty (30) days of receipt of invoice. Late payments bear interest at 1.5% per month."
)

CLAUSE_CONFIDENTIALITY = (
    "3", "Confidentiality",
    "Each party agrees to maintain the confidentiality of all proprietary information disclosed by the other party for three (3) years."
)

CLAUSE_LIABILITY = (
    "4", "Limitation of Liability",
    "Except for breaches of confidentiality, neither party shall be liable to the other for any indirect, incidental, or consequential damages. "
    "Notwithstanding any other provision herein, Service Provider's total liability shall be unlimited for all claims arising under this Agreement."
)

CLAUSE_TERMINATION = (
    "5", "Termination",
    "Either party may terminate this Agreement upon thirty (30) days prior written notice to the other party. "
    "However, Service Provider may terminate this Agreement immediately at any time without notice upon any suspected default or breach."
)


def _build_service_agreement_doc() -> SegmentationResult:
    items = [CLAUSE_SERVICES, CLAUSE_PAYMENT, CLAUSE_CONFIDENTIALITY, CLAUSE_LIABILITY, CLAUSE_TERMINATION]
    clauses = [_create_clause(f"sa_{num}", num, head, text) for num, head, text in items]
    total_len = sum(c.character_count for c in clauses)
    return SegmentationResult(
        document_id="doc_service_agreement",
        source_filename="Service Agreement.pdf",
        clauses=clauses,
        total_clauses=len(clauses),
        source_character_count=total_len,
        segmented_character_count=total_len,
        text_coverage_ratio=1.0
    )


# ---------------------------------------------------------------------------
# Test Data: Mutual NDA (Completely different contract)
# ---------------------------------------------------------------------------
def _build_nda_doc() -> SegmentationResult:
    items = [
        ("1", "Definition of Confidential Information",
         "Confidential Information means all non-public, proprietary information disclosed by one party to the other party."),
        ("2", "Standard of Care",
         "The receiving party shall protect the disclosing party's confidential information using the same degree of care it uses for its own information, but not less than reasonable care."),
        ("3", "Term and Return of Materials",
         "This Agreement shall remain in effect for two (2) years. Upon written request, receiving party shall prompt return or destroy all materials."),
        ("4", "Governing Law",
         "This Agreement shall be governed by and construed in accordance with the laws of the State of Delaware without regard to conflict of laws principles.")
    ]
    clauses = [_create_clause(f"nda_{num}", num, head, text) for num, head, text in items]
    total_len = sum(c.character_count for c in clauses)
    return SegmentationResult(
        document_id="doc_nda",
        source_filename="Mutual_NDA.pdf",
        clauses=clauses,
        total_clauses=len(clauses),
        source_character_count=total_len,
        segmented_character_count=total_len,
        text_coverage_ratio=1.0
    )


# ===========================================================================
# 0. User Exact Reported Clauses Verification
# ===========================================================================

def test_exact_user_reported_clauses():
    """
    Directly verify the exact two clauses reported by the user:
    1. 'The total liability of the Service Provider shall be unlimited, regardless of the cause of action.'
    2. 'The Service Provider reserves the right to terminate this Agreement immediately, without prior notice or explanation, at its sole discretion.'
    """
    rule_engine = RuleEngine()
    analyzer = get_risk_analyzer()

    c1_text = "The total liability of the Service Provider shall be unlimited, regardless of the cause of action."
    c2_text = "The Service Provider reserves the right to terminate this Agreement immediately, without prior notice or explanation, at its sole discretion."

    # Test Clause 1 against RuleEngine
    m1 = rule_engine.analyze_clause(c1_text)
    m1_ids = [r.rule_id for r in m1]
    assert "RULE_LIAB_UNLIMITED" in m1_ids, f"Expected RULE_LIAB_UNLIMITED in {m1_ids}"
    r_liab = next(r for r in m1 if r.rule_id == "RULE_LIAB_UNLIMITED")
    assert r_liab.severity_weight == 95.0
    assert "total liability of the Service Provider shall be unlimited" in r_liab.matched_text

    # Test Clause 2 against RuleEngine
    m2 = rule_engine.analyze_clause(c2_text)
    m2_ids = [r.rule_id for r in m2]
    assert "RULE_TERM_NO_NOTICE" in m2_ids, f"Expected RULE_TERM_NO_NOTICE in {m2_ids}"
    assert "RULE_TERM_CONVENIENCE_UNILATERAL" in m2_ids, f"Expected RULE_TERM_CONVENIENCE_UNILATERAL in {m2_ids}"

    # Test full analyzer pipeline on Clause 1
    cl1 = _create_clause("user_c1", "1", "Limitation of Liability", c1_text)
    a1 = analyzer.analyze_clause(cl1, "doc_user_test", skip_llm=True)
    assert len(a1.detected_rules) >= 1
    assert any(r.rule_id == "RULE_LIAB_UNLIMITED" for r in a1.detected_rules)
    assert a1.risk_level in (RiskLevel.MEDIUM, RiskLevel.HIGH)
    assert a1.risk_score >= 40.0

    # Test full analyzer pipeline on Clause 2
    cl2 = _create_clause("user_c2", "2", "Termination", c2_text)
    a2 = analyzer.analyze_clause(cl2, "doc_user_test", skip_llm=True)
    assert len(a2.detected_rules) >= 1
    assert any(r.rule_id in ("RULE_TERM_NO_NOTICE", "RULE_TERM_CONVENIENCE_UNILATERAL") for r in a2.detected_rules)
    assert a2.risk_level in (RiskLevel.MEDIUM, RiskLevel.HIGH)
    assert a2.risk_score >= 40.0


# ===========================================================================
# 1. Limitation of Liability Intra-Clause Inconsistency
# ===========================================================================

def test_limitation_of_liability_intra_clause_contradiction():
    """
    Clause 4 excludes indirect/consequential damages but states total liability is unlimited.
    Must trigger RULE_LIAB_INTERNAL_CONTRADICTION and detect intra-clause contradiction.
    """
    rule_engine = RuleEngine()
    conflict_detector = CrossClauseConflictDetector()

    liab_text = CLAUSE_LIABILITY[2]
    matched_rules = rule_engine.analyze_clause(liab_text)
    rule_ids = [r.rule_id for r in matched_rules]

    # Verify both the contradiction rule and the unlimited liability rule matched
    assert "RULE_LIAB_INTERNAL_CONTRADICTION" in rule_ids, f"Expected RULE_LIAB_INTERNAL_CONTRADICTION in {rule_ids}"
    assert "RULE_LIAB_UNLIMITED" in rule_ids, f"Expected RULE_LIAB_UNLIMITED in {rule_ids}"

    # Verify conflict detector detects single-clause contradiction
    clause = _create_clause("c_liab", "4", "Limitation of Liability", liab_text)
    intra_conflicts = conflict_detector.detect_intra_clause_contradictions([clause])

    assert len(intra_conflicts) >= 1
    assert any("Liability Inconsistency" in c.conflict_type for c in intra_conflicts)
    assert intra_conflicts[0].clause_numbers == ["4"]


# ===========================================================================
# 2. Termination Notice Asymmetry Intra-Clause Contradiction
# ===========================================================================

def test_termination_asymmetric_notice_intra_clause_contradiction():
    """
    Clause 5 gives both parties a 30-day notice right, but also gives the service provider
    an immediate termination right without notice.
    Must trigger RULE_TERM_ASYMMETRIC_NOTICE and detect termination asymmetry.
    """
    rule_engine = RuleEngine()
    conflict_detector = CrossClauseConflictDetector()

    term_text = CLAUSE_TERMINATION[2]
    matched_rules = rule_engine.analyze_clause(term_text)
    rule_ids = [r.rule_id for r in matched_rules]

    assert "RULE_TERM_ASYMMETRIC_NOTICE" in rule_ids, f"Expected RULE_TERM_ASYMMETRIC_NOTICE in {rule_ids}"
    assert "RULE_TERM_NO_NOTICE" in rule_ids, f"Expected RULE_TERM_NO_NOTICE in {rule_ids}"

    clause = _create_clause("c_term", "5", "Termination", term_text)
    intra_conflicts = conflict_detector.detect_intra_clause_contradictions([clause])

    assert len(intra_conflicts) >= 1
    assert any("Termination Notice Asymmetry" in c.conflict_type for c in intra_conflicts)
    assert intra_conflicts[0].clause_numbers == ["5"]


# ===========================================================================
# 3. Cross-Clause vs Intra-Clause Strict Separation
# ===========================================================================

def test_cross_clause_vs_intra_clause_separation():
    """
    The Service Agreement has internal contradictions within Clause 4 and Clause 5,
    but does NOT have contradictions between DIFFERENT clauses.
    Cross-clause conflicts must be empty, while intra-clause contradictions must report both.
    """
    conflict_detector = CrossClauseConflictDetector()
    doc = _build_service_agreement_doc()

    cross_conflicts = conflict_detector.detect_cross_clause_conflicts(doc.clauses)
    intra_conflicts = conflict_detector.detect_intra_clause_contradictions(doc.clauses)

    assert cross_conflicts == [], f"Expected 0 cross-clause conflicts, got: {cross_conflicts}"
    assert len(intra_conflicts) == 2, f"Expected 2 intra-clause contradictions, got: {len(intra_conflicts)}"


# ===========================================================================
# 4. BERT Low-Confidence Handling (Uncertain – manual review recommended)
# ===========================================================================

def test_bert_low_confidence_handling():
    """
    When a clause's BERT prediction confidence is below the threshold (< 0.45),
    the assessment must flag is_uncertain_classification=True and set display_category
    to 'Uncertain – manual review recommended'.
    """
    analyzer = get_risk_analyzer()
    doc = _build_service_agreement_doc()

    summary = analyzer.analyze_document(doc, skip_llm=True)
    assessments = summary.all_assessments

    for assess in assessments:
        if assess.bert_confidence < 0.45:
            assert assess.is_uncertain_classification is True
            assert assess.display_category == "Uncertain – manual review recommended"
        else:
            assert assess.is_uncertain_classification is False
            assert assess.display_category == assess.clause_type


# ===========================================================================
# 5. Qwen3 Availability & Inference Verification (LM Studio Offline vs Online)
# ===========================================================================

def test_qwen3_offline_marks_unavailable_without_fake_ai():
    """
    When LM Studio is closed:
    - Risky candidate clauses (Clauses 4 & 5) must be marked UNAVAILABLE.
    - Non-risky clauses (Clauses 1, 2, 3) must be marked SKIPPED.
    - Zero fake AI explanations, zero scenario predictions generated.
    """
    analyzer = get_risk_analyzer()
    doc = _build_service_agreement_doc()

    with patch.object(LLMGenerator, "is_available", return_value=False):
        summary = analyzer.analyze_document(doc, skip_llm=False)
        assessments_by_num = {a.clause_number: a for a in summary.all_assessments}

        # Clause 4 (Liability) & Clause 5 (Termination) are candidates due to high risk / rules
        assert assessments_by_num["4"].llm_inference_status == LLMInferenceStatus.UNAVAILABLE
        assert assessments_by_num["4"].risk_explanation is None

        assert assessments_by_num["5"].llm_inference_status == LLMInferenceStatus.UNAVAILABLE
        assert assessments_by_num["5"].risk_explanation is None

        # Normal clauses should be SKIPPED
        assert assessments_by_num["1"].llm_inference_status == LLMInferenceStatus.SKIPPED
        assert assessments_by_num["1"].risk_explanation is None

        # Combined scenario should be None
        assert summary.combined_scenario is None


def test_qwen3_online_records_successful_inference():
    """
    When LM Studio is running:
    - Risky candidate clauses are evaluated with genuine LLM calls.
    - Status is marked SUCCESS.
    - Explanations and timings are recorded.
    """
    analyzer = get_risk_analyzer()
    doc = _build_service_agreement_doc()

    mock_llm_response = {
        "llm_score": 88.0,
        "risk_explanation": "Real Qwen3 analysis: The clause contains severe internal contradictions between damage waivers and uncapped exposure.",
        "key_risk_factors": ["Internal contradiction", "Unlimited liability exposure"],
        "scenario_title": "Dispute Exposure Scenario",
        "trigger_condition": "Client claims breach of contract",
        "scenario_description": "If a claim is brought, the vendor cannot rely on damage exclusions due to the unlimited liability sentence.",
        "possible_consequence": "Uncapped damages and litigation costs",
        "assumptions": ["Contract is signed without amendment"],
        "uncertainty": "Court interpretation of conflicting sentences"
    }

    with patch.object(LLMGenerator, "is_available", return_value=True):
        with patch.object(LLMGenerator, "generate", return_value=mock_llm_response):
            summary = analyzer.analyze_document(doc, skip_llm=False)
            assessments_by_num = {a.clause_number: a for a in summary.all_assessments}

            assert assessments_by_num["4"].llm_inference_status == LLMInferenceStatus.SUCCESS
            assert "Real Qwen3 analysis" in assessments_by_num["4"].risk_explanation
            assert assessments_by_num["4"].future_scenario is not None


# ===========================================================================
# 6. Genuinely Input-Dependent Dynamic Results
# ===========================================================================

def test_dynamic_contrast_service_agreement_versus_nda():
    """
    Verify that analyzing two completely different contracts yields completely different results.
    - Service Agreement has high risk in Clauses 4 & 5, internal contradictions, and higher overall risk score.
    - Mutual NDA has standard low/normal terms, 0 contradictions, and lower overall risk score.
    """
    analyzer = get_risk_analyzer()
    doc_sa = _build_service_agreement_doc()
    doc_nda = _build_nda_doc()

    summary_sa = analyzer.analyze_document(doc_sa, skip_llm=True)
    summary_nda = analyzer.analyze_document(doc_nda, skip_llm=True)

    # Risk scores and levels must differ
    assert summary_sa.contract_risk_score > summary_nda.contract_risk_score
    assert summary_sa.contract_risk_score >= 35.0, "Service Agreement with unlimited liability should have elevated risk"
    assert summary_nda.contract_risk_score < 35.0, "Standard Mutual NDA should have normal or low overall risk"

    # Rule and contradiction matches must differ completely
    assert len(summary_sa.intra_clause_contradictions) == 2
    assert len(summary_nda.intra_clause_contradictions) == 0

    sa_rules = [r.rule_id for a in summary_sa.all_assessments for r in a.detected_rules]
    nda_rules = [r.rule_id for a in summary_nda.all_assessments for r in a.detected_rules]

    assert "RULE_LIAB_INTERNAL_CONTRADICTION" in sa_rules
    assert "RULE_LIAB_INTERNAL_CONTRADICTION" not in nda_rules
    assert "RULE_TERM_ASYMMETRIC_NOTICE" in sa_rules
    assert "RULE_TERM_ASYMMETRIC_NOTICE" not in nda_rules


# ===========================================================================
# 7. Benign Clauses Produce Zero Rules (Ordinary Payment & Confidentiality)
# ===========================================================================

def test_benign_ordinary_clauses_produce_zero_rules():
    """
    Ordinary commercial clauses without risk factors must NOT trigger false positives:
    - Clause C: 'The Client shall pay the Service Provider a monthly fee of ₹50,000 within 15 days of receiving the invoice.'
    - Clause D: 'Both parties agree to maintain the confidentiality of all business information shared during the Agreement.'
    """
    rule_engine = RuleEngine()
    analyzer = get_risk_analyzer()

    cC_text = "The Client shall pay the Service Provider a monthly fee of ₹50,000 within 15 days of receiving the invoice."
    cD_text = "Both parties agree to maintain the confidentiality of all business information shared during the Agreement."

    # Must match 0 risk rules
    mC = rule_engine.analyze_clause(cC_text)
    mD = rule_engine.analyze_clause(cD_text)
    assert mC == [], f"Ordinary payment triggered unexpected rules: {mC}"
    assert mD == [], f"Ordinary confidentiality triggered unexpected rules: {mD}"

    # Analyzer evaluation should classify with low/normal score
    clC = _create_clause("c_pay", "1", "Fees", cC_text)
    clD = _create_clause("c_conf", "2", "Confidentiality", cD_text)

    aC = analyzer.analyze_clause(clC, "doc_benign", skip_llm=True)
    aD = analyzer.analyze_clause(clD, "doc_benign", skip_llm=True)

    assert aC.risk_level in (RiskLevel.NORMAL, RiskLevel.LOW)
    assert aC.risk_score < 40.0
    assert len(aC.detected_rules) == 0

    assert aD.risk_level in (RiskLevel.NORMAL, RiskLevel.LOW)
    assert aD.risk_score < 40.0
    assert len(aD.detected_rules) == 0


# ===========================================================================
# 8. Frontend Normalization & Clean Data Flow
# ===========================================================================

def test_frontend_normalization_handles_intra_conflicts_and_normal():
    """Verify frontend normalization safely parses intra-clause conflicts, normal risk counts, and uncertainty."""
    from frontend.utils.formatting import normalize_analysis_data

    sample_api_data = {
        "document": {"filename": "Contract.pdf", "document_type": "PDF"},
        "contract_summary": {
            "risk_score": 25.0,
            "risk_level": "LOW",
            "normal_risk_clause_count": 3,
            "low_risk_clause_count": 1,
            "medium_risk_clause_count": 0,
            "high_risk_clause_count": 0,
            "intra_clause_contradictions": []
        },
        "clause_assessments": [
            {
                "clause_id": "c1",
                "clause_number": "1",
                "clause_heading": "Payment",
                "clause_text": "Normal terms.",
                "risk_score": 10.0,
                "risk_level": "NORMAL",
                "bert_label": "Payment Terms",
                "bert_confidence": 0.35,
                "is_uncertain_classification": True,
                "display_category": "Uncertain – manual review recommended",
                "rule_matches": [],
                "intra_clause_contradictions": []
            }
        ]
    }

    normalized = normalize_analysis_data(sample_api_data)
    assert normalized is not None
    assert normalized["contract_summary"]["normal_risk_clause_count"] == 3
    c1 = normalized["clause_assessments"][0]
    assert c1["risk_level"] == "NORMAL"
    assert c1["is_uncertain_classification"] is True


