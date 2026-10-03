"""
CLI Verification & Live Smoke Test Script for Phase 7.2 Future Scenario Predictor.
Runs full scenario predictor workflow on High, Medium, Low risk clauses, insufficient evidence,
and malformed LLM response handling against live Qwen3 via LM Studio.
"""

import sys
from unittest.mock import MagicMock
from src.clause_segmentation.models import SegmentedClause, SegmentationResult
from src.document_processing.models import SourceType
from src.risk_analysis.analyzer import ContractRiskAnalyzer
from src.risk_analysis.scenario_predictor import FutureScenarioPredictor
from src.risk_analysis.scenario_models import FutureScenario
from src.risk_analysis.models import RiskAssessment, RiskLevel, RiskCategory, RiskScoreBreakdown


def print_formatted_scenario(assessment: RiskAssessment, scenario: FutureScenario, case_name: str):
    print("=" * 70)
    print(f" FUTURE SCENARIO PREDICTOR -- [{case_name}]")
    print("=" * 70)
    print(f"Clause        : {assessment.clause_number or ''} — {assessment.clause_heading or 'Untitled'}")
    print(f"Clause ID     : {assessment.clause_id}")
    print(f"Risk Level    : {assessment.risk_level.value}")
    print(f"Risk Score    : {assessment.risk_score:.2f} / 100.0")
    print(f"BERT Category : {assessment.clause_type}")
    print(f"Fallback Active: {scenario.fallback_active}")
    print("-" * 70)
    print(f"\nScenario Title:\n  {scenario.scenario_title}")
    print(f"\nTrigger Condition:\n  {scenario.trigger_condition}")
    print(f"\nScenario Description:\n  {scenario.scenario_description}")
    print(f"\nPossible Consequence:\n  {scenario.possible_consequence}")
    print(f"\nSupporting Evidence ({len(scenario.supporting_evidence)} Citations):")
    for cit in scenario.supporting_evidence:
        pages_str = f" (Pages: {cit.source_pages})" if cit.source_pages else ""
        num_str = f" Clause {cit.clause_number}" if cit.clause_number else ""
        print(f"  * [{cit.clause_id}]{num_str}{pages_str}")
    print(f"\nAssumptions:")
    for a in scenario.assumptions:
        print(f"  - {a}")
    print(f"\nUncertainty:\n  {scenario.uncertainty}")
    print("=" * 70 + "\n")


def main():
    print("\n================================================================================")
    print(" CONTRACTRISK AI -- PHASE 7.2 FUTURE SCENARIO PREDICTOR SMOKE TEST")
    print("================================================================================")

    # 1. Prepare synthetic clauses & run Phase 7.1 Risk Analysis
    c1_text = (
        "Under no circumstances shall Vendor have any unlimited liability for breaches of contract. "
        "Customer agrees to defend, indemnify and hold harmless Vendor from all claims, damages, and costs. "
        "Vendor reserves the right to terminate this agreement for convenience at any time without cause."
    )
    c2_text = (
        "During the term and for 2 years thereafter, Contractor shall not directly or indirectly compete "
        "or engage in any competing business. This Agreement shall automatically renew for successive terms."
    )
    c3_text = (
        "This Agreement is entered into on October 1, 2026 by and between Party A and Party B. "
        "This Agreement shall be governed by and construed in accordance with the laws of Delaware."
    )
    c4_text = (
        "Notice of non-renewal must be delivered in writing."
    )

    clauses = [
        SegmentedClause(
            clause_id="clause_142",
            document_id="doc_scenario_smoke",
            clause_number="14.2",
            clause_heading="Limitation of Liability & Indemnification",
            clause_text=c1_text,
            source_type=SourceType.PDF,
            source_pages=[5],
            character_count=len(c1_text),
            word_count=len(c1_text.split())
        ),
        SegmentedClause(
            clause_id="clause_81",
            document_id="doc_scenario_smoke",
            clause_number="8.1",
            clause_heading="Non-Compete & Renewal",
            clause_text=c2_text,
            source_type=SourceType.PDF,
            source_pages=[3],
            character_count=len(c2_text),
            word_count=len(c2_text.split())
        ),
        SegmentedClause(
            clause_id="clause_11",
            document_id="doc_scenario_smoke",
            clause_number="1.1",
            clause_heading="Effective Date & Governing Law",
            clause_text=c3_text,
            source_type=SourceType.PDF,
            source_pages=[1],
            character_count=len(c3_text),
            word_count=len(c3_text.split())
        ),
        SegmentedClause(
            clause_id="clause_insufficient",
            document_id="doc_scenario_smoke",
            clause_number="19.1",
            clause_heading="Notice Formalities",
            clause_text=c4_text,
            source_type=SourceType.PDF,
            source_pages=[8],
            character_count=len(c4_text),
            word_count=len(c4_text.split())
        )
    ]

    total_chars = sum(c.character_count for c in clauses)

    seg_result = SegmentationResult(
        document_id="doc_scenario_smoke",
        source_filename="master_commercial_agreement.pdf",
        clauses=clauses,
        total_clauses=len(clauses),
        source_character_count=total_chars,
        segmented_character_count=total_chars,
        text_coverage_ratio=1.0
    )

    bert_predictions = {
        "clause_142": ("Uncapped Liability", 0.94),
        "clause_81": ("Non-Compete", 0.88),
        "clause_11": ("Effective Date", 0.96),
        "clause_insufficient": ("Other", 0.35)
    }

    analyzer = ContractRiskAnalyzer()
    summary = analyzer.analyze_document(
        segmentation_result=seg_result,
        predicted_clause_types=bert_predictions
    )

    assessments_by_id = {a.clause_id: a for a in summary.highest_risk_assessments}

    # Instantiate FutureScenarioPredictor (connects to live Qwen3 via LM Studio)
    predictor = FutureScenarioPredictor()

    # 1. High-Risk Clause
    high_assess = assessments_by_id["clause_142"]
    high_scen = predictor.predict_scenario(high_assess)
    print_formatted_scenario(high_assess, high_scen, "CASE 1: HIGH RISK CLAUSE")

    # 2. Medium-Risk Clause
    med_assess = assessments_by_id["clause_81"]
    med_scen = predictor.predict_scenario(med_assess)
    print_formatted_scenario(med_assess, med_scen, "CASE 2: MEDIUM RISK CLAUSE")

    # 3. Low-Risk Clause
    low_assess = assessments_by_id["clause_11"]
    low_scen = predictor.predict_scenario(low_assess)
    print_formatted_scenario(low_assess, low_scen, "CASE 3: LOW RISK CLAUSE")

    # 4. Insufficient-Evidence / Ambiguous Case
    insuf_assess = assessments_by_id["clause_insufficient"]
    insuf_scen = predictor.predict_scenario(insuf_assess)
    print_formatted_scenario(insuf_assess, insuf_scen, "CASE 4: INSUFFICIENT EVIDENCE / AMBIGUOUS CLAUSE")

    # 5. Malformed/Invalid LLM Response Handling (Mocked error generator)
    print("[TESTING CASE 5] Testing malformed/invalid LLM response handling with fallback execution...")
    mock_err_gen = MagicMock()
    mock_err_gen.generate.side_effect = Exception("LM Studio HTTP 500: Server Error / Malformed JSON")
    fallback_predictor = FutureScenarioPredictor(generator=mock_err_gen)
    malformed_scen = fallback_predictor.predict_scenario(high_assess)
    print_formatted_scenario(high_assess, malformed_scen, "CASE 5: MALFORMED/INVALID LLM RESPONSE FALLBACK")

    print("[SUCCESS] Phase 7.2 Future Scenario Predictor Live Smoke Test Completed Successfully!")


if __name__ == "__main__":
    main()
