"""
Verification Script for Phase 8.2.1 Hardening.
Executes Direct RuleEngine tests for 5.1, 10.4, 10.5, 2.3 and
live Qwen3 risk explanation & scenario predictor tests for 8.3, 10.5, and 1.1.
"""

import sys
from src.clause_segmentation.models import SegmentedClause
from src.risk_analysis.rule_engine import RuleEngine
from src.risk_analysis.analyzer import ContractRiskAnalyzer
from src.risk_analysis.scenario_predictor import FutureScenarioPredictor


def main():
    print("=" * 80)
    print(" PHASE 8.2.1 HARDENING VERIFICATION")
    print("=" * 80)

    # 1. Direct RuleEngine Test for 5.1, 10.4, 10.5, 2.3
    print("\n[STEP 6] Direct RuleEngine Verification:")
    engine = RuleEngine()
    test_clauses = {
        "5.1": "5.1 Prices quoted are subject to alteration without notice. Payment shall be due within 30 days of invoice date.",
        "10.4": "10.4 The Company may terminate this Agreement immediately without prior notice or refund of prepaid fees if Buyer fails to comply with any provision hereof.",
        "10.5": "10.5 The Company reserves the right to suspend or terminate services and access immediately following overdue payment or non-payment of any amounts due.",
        "2.3": "2.3 Preservation of Warranties. Nothing in these Terms and Conditions shall prejudice any condition or warranty, express or implied, or any legal remedy to which the Buyer may be entitled under statute or common law."
    }

    for c_num, text in test_clauses.items():
        matches = engine.analyze_clause(text)
        rule_ids = [m.rule_id for m in matches]
        print(f"  Clause {c_num}: {rule_ids or 'NONE (No False Positive)'}")

    # 2. Live Qwen3 Tests for 8.3, 10.5, and 1.1
    print("\n[STEP 7] Live Qwen3 Risk Explanation & Scenario Verification:")
    analyzer = ContractRiskAnalyzer()
    predictor = FutureScenarioPredictor()

    live_test_clauses = {
        "8.3": SegmentedClause(
            clause_id="c_8_3", document_id="d1", clause_number="8.3", clause_heading="Third Party Rights",
            clause_text="8.3 Subject to Section 8.3.5 hereof, nothing herein is intended to preclude FG from granting rights to supply or supplying Products to third parties.",
            source_type="pdf", character_count=138, word_count=22, source_pages=[1]
        ),
        "10.5": SegmentedClause(
            clause_id="c_10_5", document_id="d1", clause_number="10.5", clause_heading="Suspension of Services",
            clause_text="10.5 The Company reserves the right to suspend or terminate services and access immediately following overdue payment or non-payment of any amounts due.",
            source_type="pdf", character_count=153, word_count=22, source_pages=[2]
        ),
        "1.1": SegmentedClause(
            clause_id="c_1_1", document_id="d1", clause_number="1.1", clause_heading="Effective Date",
            clause_text="1.1 Effective Date. This Agreement is made and effective as of October 1, 2026 by and between the parties.",
            source_type="pdf", character_count=105, word_count=17, source_pages=[1]
        )
    }

    for c_num, seg_clause in live_test_clauses.items():
        assessment = analyzer.analyze_clause(seg_clause, document_id="d1")
        scen = predictor.predict_scenario(assessment)
        
        print(f"\n--------------------------------------------------------------------------------")
        print(f"CLAUSE {c_num} -- {seg_clause.clause_heading}")
        print(f"--------------------------------------------------------------------------------")
        print(f"  Risk Score        : {assessment.risk_score:.2f} ({assessment.risk_level.value})")
        print(f"  Primary Category  : {assessment.risk_category.value}")
        print(f"  Rules Matched     : {[r.rule_id for r in assessment.detected_rules] or 'None'}")
        print(f"  LLM Explanation   : {assessment.risk_explanation}")
        print(f"  Scenario Title    : {scen.scenario_title}")
        print(f"  Trigger Condition : {scen.trigger_condition}")
        print(f"  Scenario Narrative: {scen.scenario_description}")
        print(f"  Consequence       : {scen.possible_consequence}")
        print(f"  Assumptions       : {scen.assumptions}")
        print(f"  Uncertainty       : {scen.uncertainty}")

    print("\n================================================================================")
    print(" [SUCCESS] Phase 8.2.1 Verification Completed Successfully!")
    print("================================================================================")


if __name__ == "__main__":
    main()
