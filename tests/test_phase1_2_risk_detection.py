"""
Regression and Integration Test Suite for Phase 1.2
---------------------------------------------------
Verifies:
1. Exact clause segmentation on Painter.pdf (exactly 5 clauses, no document title counted, no false headings).
2. Risk detection improvements for:
   - Unilateral price increase without client approval (Clause 3 -> MEDIUM risk).
   - Immediate termination or work stoppage without notice (Clause 4 -> MEDIUM risk).
   - Contradictory liability and damage disclaimer (Clause 5 -> MEDIUM risk).
3. Normal clauses (Clause 1 and 2) evaluated as LOW risk with 0 false positive rule matches.
4. Semantic appropriateness of clause categories (no spurious 'Insurance' for house painting).
5. Grounded combined future scenario generation across contract risks.
6. Positive and negative test cases for all 3 risk categories.
"""

from pathlib import Path
import pytest

from src.document_processing.loader import DocumentLoader
from src.document_processing.models import SourceType
from src.clause_segmentation.segmenter import ClauseSegmenter
from src.clause_segmentation.models import SegmentedClause
from src.clause_segmentation.patterns import detect_clause_header
from src.risk_analysis.rule_engine import RuleEngine
from src.risk_analysis.analyzer import ContractRiskAnalyzer
from src.risk_analysis.scoring import HybridScorer
from src.risk_analysis.scenario_predictor import FutureScenarioPredictor
from src.risk_analysis.models import RiskLevel, RiskCategory
from src.api.dependencies import get_risk_analyzer, get_clause_segmenter, get_document_loader


@pytest.fixture
def loader():
    return DocumentLoader()


@pytest.fixture
def segmenter():
    return ClauseSegmenter()


@pytest.fixture
def rule_engine():
    return RuleEngine()


@pytest.fixture
def analyzer():
    return get_risk_analyzer()


@pytest.fixture
def painter_doc(loader):
    pdf_path = Path("scratch/Painter.pdf")
    if not pdf_path.exists():
        pytest.skip("scratch/Painter.pdf removed per user requirement 6")
    return loader.load_document(pdf_path)


@pytest.fixture
def customer_doc(loader):
    pdf_path = Path("scratch/Customer.pdf")
    if not pdf_path.exists():
        pytest.skip("scratch/Customer.pdf not present")
    return loader.load_document(pdf_path)


# =========================================================================
# 1. SEGMENTATION & DOCUMENT Provenance Tests
# =========================================================================

def test_painter_pdf_exact_five_clauses(painter_doc, segmenter):
    """Verify exactly 5 clauses are segmented and no titles or headers are miscounted."""
    res = segmenter.segment(painter_doc)
    assert len(res.clauses) == 5, f"Expected exactly 5 clauses, got {len(res.clauses)}"
    assert res.total_clauses == 5

    # Verify clause numbers 1 to 5
    for idx, c in enumerate(res.clauses, start=1):
        assert c.clause_number == str(idx), f"Clause at index {idx} has number {c.clause_number}"

    # Verify Clause 2 does not have a full sentence extracted as heading
    c2 = res.clauses[1]
    assert c2.clause_heading is None or len(c2.clause_heading.split()) <= 4, (
        f"Clause 2 has full sentence mistakenly captured as heading: {c2.clause_heading}"
    )


# =========================================================================
# 2. PAINTER.PDF RISK DETECTION & SCORING PIPELINE
# =========================================================================

def test_painter_pdf_risk_analysis(painter_doc, segmenter, analyzer):
    """
    Primary regression test on Painter.pdf:
    - Clause 3: Meaningful price modification risk (MEDIUM).
    - Clause 4: Meaningful termination risk (MEDIUM).
    - Clause 5: Potential liability contradiction (MEDIUM).
    - Clause 1 & 2: Normal low-risk provisions (LOW).
    - Overall contract: MEDIUM risk with exactly 3 problematic clauses.
    """
    seg_res = segmenter.segment(painter_doc)
    summary = analyzer.analyze_document(seg_res)

    # Assessments mapped by clause number
    assess_by_num = {a.clause_number: a for a in summary.all_assessments}
    assert len(assess_by_num) == 5

    # --- Clause 1: Normal Scope / Services ---
    a1 = assess_by_num["1"]
    assert a1.risk_level == RiskLevel.LOW, f"Clause 1 expected LOW risk, got {a1.risk_level} (score {a1.risk_score})"
    assert len(a1.detected_rules) == 0
    assert a1.clause_type != "Insurance", "Clause 1 must not be miscategorized as Insurance"

    # --- Clause 2: Normal Payment ---
    a2 = assess_by_num["2"]
    assert a2.risk_level == RiskLevel.LOW, f"Clause 2 expected LOW risk, got {a2.risk_level} (score {a2.risk_score})"
    assert len(a2.detected_rules) == 0

    # --- Clause 3: Unilateral Price Increase ---
    a3 = assess_by_num["3"]
    assert a3.risk_level == RiskLevel.MEDIUM, f"Clause 3 expected MEDIUM risk, got {a3.risk_level} (score {a3.risk_score})"
    assert a3.risk_score >= 35.0
    a3_rules = [r.rule_id for r in a3.detected_rules]
    assert "RULE_PRICE_UNILATERAL_ALTERATION" in a3_rules, f"Clause 3 failed to trigger price rule: {a3_rules}"
    assert a3.risk_category == RiskCategory.PAYMENT_TERMS

    # --- Clause 4: Immediate Termination Without Notice ---
    a4 = assess_by_num["4"]
    assert a4.risk_level == RiskLevel.MEDIUM, f"Clause 4 expected MEDIUM risk, got {a4.risk_level} (score {a4.risk_score})"
    assert a4.risk_score >= 35.0
    a4_rules = [r.rule_id for r in a4.detected_rules]
    assert "RULE_TERM_NO_NOTICE" in a4_rules, f"Clause 4 failed to trigger termination rule: {a4_rules}"
    assert a4.risk_category == RiskCategory.TERMINATION

    # --- Clause 5: Contradictory Damage Liability ---
    a5 = assess_by_num["5"]
    assert a5.risk_level == RiskLevel.MEDIUM, f"Clause 5 expected MEDIUM risk, got {a5.risk_level} (score {a5.risk_score})"
    assert a5.risk_score >= 35.0
    a5_rules = [r.rule_id for r in a5.detected_rules]
    assert "RULE_LIAB_CONTRADICTORY_DAMAGE" in a5_rules, f"Clause 5 failed to trigger liability rule: {a5_rules}"
    assert a5.risk_category == RiskCategory.LIABILITY

    # --- Overall Contract Summary ---
    assert summary.contract_risk_level == RiskLevel.MEDIUM
    assert summary.contract_risk_score >= 35.0
    assert summary.medium_risk_clauses_count == 3
    assert summary.low_risk_clauses_count == 2
    assert summary.high_risk_clauses_count == 0


# =========================================================================
# 3. COMBINED FUTURE SCENARIO GROUNDING
# =========================================================================

def test_painter_pdf_combined_future_scenario(painter_doc, segmenter, analyzer):
    """Verify that a concise, grounded combined scenario is generated across contract risks."""
    seg_res = segmenter.segment(painter_doc)
    summary = analyzer.analyze_document(seg_res)

    comb = summary.combined_scenario
    assert comb is not None, "summary.combined_scenario was not generated"
    assert comb.scenario_title, "Combined scenario title is missing"
    assert "3" in comb.clause_number and "4" in comb.clause_number and "5" in comb.clause_number, (
        f"Triggering clauses should reference 3, 4, and 5: {comb.clause_number}"
    )

    # Narrative grounding
    desc = comb.scenario_description
    conseq = comb.possible_consequence
    assert len(desc) > 20, "Combined scenario description too short"
    assert len(conseq) > 20, "Combined scenario consequence too short"

    # Conditional phrasing check (anti-hallucination requirement)
    lower_desc = desc.lower()
    assert any(w in lower_desc for w in ["if", "could", "were to", "in the event", "should", "potential"]), (
        f"Scenario description must use conditional phrasing: {desc}"
    )


def test_low_risk_contract_scenario_baseline():
    """Verify contracts with only low-risk clauses produce an appropriate baseline message."""
    predictor = FutureScenarioPredictor()
    scenario = predictor.predict_combined_scenario([])
    assert "Baseline" in scenario.scenario_title or "Standard" in scenario.scenario_title
    assert "No meaningful contractual risks" in scenario.scenario_description


# =========================================================================
# 4. POSITIVE AND NEGATIVE RULE VALIDATION TESTS
# =========================================================================

def test_unilateral_price_positive_and_negative(rule_engine):
    """Validate positive detections and ensure zero false positives for price rules."""
    positives = [
        "The Painter can increase the agreed price at any time without asking the Client.",
        "The Client must pay the new amount even if the Client does not agree with the increase.",
        "Company reserves the right to increase prices at any time without notice.",
        "Provider may unilaterally adjust fees without customer consent.",
        "The vendor may raise the agreed rate at any time without asking the customer."
    ]
    for text in positives:
        matches = rule_engine.analyze_clause(text)
        rule_ids = [m.rule_id for m in matches]
        assert "RULE_PRICE_UNILATERAL_ALTERATION" in rule_ids, f"Failed to match positive price case: '{text}'"

    negatives = [
        "The Client agrees to pay ₹40,000 for the work.",
        "The Client must pay ₹20,000 before the work starts and the remaining amount after completion.",
        "Any increase in fees shall require sixty (60) days prior written notice and mutual agreement.",
        "Prices may only be adjusted upon the mutual written agreement of both parties.",
        "Any price changes must be agreed upon in writing by the Client."
    ]
    for text in negatives:
        matches = rule_engine.analyze_clause(text)
        rule_ids = [m.rule_id for m in matches]
        assert "RULE_PRICE_UNILATERAL_ALTERATION" not in rule_ids, f"False positive on price case: '{text}'"


def test_immediate_termination_positive_and_negative(rule_engine):
    """Validate positive detections and ensure zero false positives for termination rules."""
    positives = [
        "However, the Painter can stop the work immediately without giving any reason or notice.",
        "Contractor may cease the work immediately without giving any reason.",
        "Provider reserves the right to terminate this agreement immediately without notice.",
        "Either party may stop work immediately without cause or explanation.",
        "Company may terminate immediately without prior notice or refund of fees."
    ]
    for text in positives:
        matches = rule_engine.analyze_clause(text)
        rule_ids = [m.rule_id for m in matches]
        assert "RULE_TERM_NO_NOTICE" in rule_ids, f"Failed to match positive termination case: '{text}'"

    negatives = [
        "Either party can end this Agreement by giving 15 days' written notice.",
        "Either party may terminate this agreement upon thirty (30) days prior written notice.",
        "Client may terminate for cause following thirty days written notice and failure to cure.",
        "Work shall continue until project completion within 20 days."
    ]
    for text in negatives:
        matches = rule_engine.analyze_clause(text)
        rule_ids = [m.rule_id for m in matches]
        assert "RULE_TERM_NO_NOTICE" not in rule_ids, f"False positive on termination case: '{text}'"


def test_contradictory_liability_positive_and_negative(rule_engine):
    """Validate positive detections and ensure zero false positives for contradictory liability rules."""
    positives = [
        "The service provider accepts responsibility for any damage caused to the customer's property during the work but shall not be required to pay compensation for such damage under any circumstances.",
        "The Painter accepts full responsibility for any damage caused to the Client's property. However, under no circumstances shall the Painter be held liable or required to pay for any repairs or damage.",
        "The Painter is responsible for any damage caused to the Client's property during the work. However, the Painter will not pay for any damage under any circumstances.",
        "Vendor accepts responsibility for property damage, but shall not pay for any damage under any circumstances.",
        "Contractor is responsible for site damage caused by workers; however, Contractor will not pay for any damage.",
        "Service provider will not pay for any damage under any circumstances."
    ]
    for text in positives:
        matches = rule_engine.analyze_clause(text)
        rule_ids = [m.rule_id for m in matches]
        assert "RULE_LIAB_CONTRADICTORY_DAMAGE" in rule_ids, f"Failed to match positive contradictory liability: '{text}'"

    negatives = [
        "The Painter is responsible for any damage caused to the Client's property during the work and agrees to repair all damage.",
        "Contractor shall be liable for direct physical damage to property caused by Contractor's negligence.",
        "Neither party shall be liable for indirect, incidental, or consequential damages.",
        "Aggregate liability shall be capped at the total amount paid under this agreement.",
        "The service provider's liability for property damage shall be limited to ₹10,000.",
        "Neither party shall be liable for indirect or consequential damages under this agreement.",
        "The service provider accepts responsibility for damage caused by its workers and will promptly pay all repair costs.",
        "Contractor accepts responsibility for defects and will rectify them within 30 days."
    ]
    for text in negatives:
        matches = rule_engine.analyze_clause(text)
        rule_ids = [m.rule_id for m in matches]
        assert "RULE_LIAB_CONTRADICTORY_DAMAGE" not in rule_ids, f"False positive on liability case: '{text}'"


def test_customer_clause5_contradictory_damage_risk(rule_engine, analyzer):
    """
    Focused regression test for Customer.pdf Clause 5:
    'The service provider accepts responsibility for any damage caused to the customer's property
    during the work but shall not be required to pay compensation for such damage under any circumstances.'
    """
    clause_text = (
        "The service provider accepts responsibility for any damage caused to the customer's "
        "property during the work but shall not be required to pay compensation for such damage "
        "under any circumstances."
    )
    # 1. Rule matching
    matches = rule_engine.analyze_clause(clause_text)
    rule_ids = [m.rule_id for m in matches]
    assert "RULE_LIAB_CONTRADICTORY_DAMAGE" in rule_ids, (
        f"Clause 5 must trigger RULE_LIAB_CONTRADICTORY_DAMAGE, got {rule_ids}"
    )

    # 2. Pipeline risk assessment
    seg_clause = SegmentedClause(
        clause_id="customer_doc:clause:005",
        document_id="customer_doc",
        clause_number="5",
        clause_heading="Damage & Liability",
        clause_text=clause_text,
        source_type=SourceType.PDF,
        character_count=len(clause_text),
        word_count=len(clause_text.split()),
    )
    assessment = analyzer.analyze_clause(
        clause=seg_clause,
        document_id="customer_doc",
    )
    assert assessment.risk_level in (RiskLevel.MEDIUM, RiskLevel.HIGH), (
        f"Clause 5 must be classified as MEDIUM or HIGH risk, got {assessment.risk_level} (score {assessment.risk_score})"
    )
    assert assessment.risk_score >= 35.0
    assert assessment.risk_category == RiskCategory.LIABILITY
    assert any(r.rule_id == "RULE_LIAB_CONTRADICTORY_DAMAGE" for r in assessment.detected_rules)


def test_customer_pdf_full_contract_analysis(customer_doc, segmenter, analyzer):
    """
    Full pipeline regression on Customer.pdf (5 clauses):
    - Clause 1 & 2: Normal low-risk provisions (LOW).
    - Clause 3: Unilateral price modification (MEDIUM).
    - Clause 4: Immediate termination without notice (MEDIUM).
    - Clause 5: Contradictory damage disclaimer (MEDIUM).
    - Problematic clauses: exactly 3 (Clauses 3, 4, 5).
    """
    seg_res = segmenter.segment(customer_doc)
    assert len(seg_res.clauses) == 5, f"Expected 5 clauses, got {len(seg_res.clauses)}"
    summary = analyzer.analyze_document(seg_res)

    assess_by_num = {a.clause_number: a for a in summary.all_assessments}
    assert assess_by_num["1"].risk_level == RiskLevel.LOW
    assert assess_by_num["2"].risk_level == RiskLevel.LOW
    assert assess_by_num["3"].risk_level == RiskLevel.MEDIUM
    assert assess_by_num["4"].risk_level == RiskLevel.MEDIUM
    assert assess_by_num["5"].risk_level == RiskLevel.MEDIUM

    problematic_numbers = [
        a.clause_number for a in summary.all_assessments if a.risk_level in (RiskLevel.HIGH, RiskLevel.MEDIUM)
    ]
    assert set(problematic_numbers) == {"3", "4", "5"}
    assert summary.medium_risk_clauses_count == 3
    assert summary.low_risk_clauses_count == 2
