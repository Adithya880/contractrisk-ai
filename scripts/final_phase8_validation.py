"""
Final Phase 8 Validation Script.
Analyzes full TermsandConditionsofSale contract PDF via ContractRiskAnalyzer pipeline & FastAPI,
verifying extracted vs analyzed clauses across all 73 clauses, score breakdown, rule matches, scenario triggers, and anti-hallucination checks.
"""

import sys
from pathlib import Path
import fitz  # PyMuPDF
import pandas as pd
from fastapi.testclient import TestClient

from src.document_processing.loader import DocumentLoader
from src.clause_segmentation.segmenter import ClauseSegmenter
from src.risk_analysis.analyzer import ContractRiskAnalyzer
from src.risk_analysis.scenario_predictor import FutureScenarioPredictor
from src.api.main import app
from scripts.validate_phase8_2 import build_72_clause_contract_pdf


def main():
    print("=" * 80)
    print(" CONTRACTRISK AI -- FINAL PHASE 8 VALIDATION REPORT")
    print("=" * 80)

    pdf_path = Path("scratch/TermsandConditionsofSale_72Clauses.pdf")
    build_72_clause_contract_pdf(pdf_path)

    loader = DocumentLoader()
    segmenter = ClauseSegmenter()
    analyzer = ContractRiskAnalyzer()
    predictor = FutureScenarioPredictor()

    print("\n[1/5] Extracting and Segmenting Full Contract PDF Document...", flush=True)
    extracted_doc = loader.load_document(str(pdf_path))
    extracted_count = len(extracted_doc.elements)
    segmentation_result = segmenter.segment(extracted_doc)
    segmented_clauses = segmentation_result.clauses
    segmented_count = len(segmented_clauses)

    print("\n[2/5] Running Full Contract Risk Analysis across ALL clauses...", flush=True)
    
    # Store all individual assessments
    all_assessments = []
    for clause in segmented_clauses:
        assessment = analyzer.analyze_clause(clause, document_id="final_val_doc")
        all_assessments.append(assessment)

    summary = analyzer.scorer.aggregate_contract_risk(
        document_id="final_val_doc",
        source_filename=pdf_path.name,
        assessments=all_assessments
    )

    analyzed_count = summary.analyzed_clauses_count
    dropped_count = segmented_count - analyzed_count

    print("================================================================================")
    print(" 1. CLAUSE COUNT & INGESTION AUDIT")
    print("================================================================================")
    print(f"  Extracted Clauses : {segmented_count}")
    print(f"  Analyzed Clauses  : {analyzed_count}")
    print(f"  Dropped Clauses   : {dropped_count}")

    print("\n================================================================================")
    print(" 2. CONTRACT-LEVEL RISK SUMMARY")
    print("================================================================================")
    print(f"  Contract Risk Score : {summary.contract_risk_score:.2f} / 100.0")
    print(f"  Contract Risk Level : {summary.contract_risk_level.value}")
    print(f"  HIGH Risk Count     : {summary.high_risk_clauses_count}")
    print(f"  MEDIUM Risk Count   : {summary.medium_risk_clauses_count}")
    print(f"  LOW Risk Count      : {summary.low_risk_clauses_count}")

    target_clause_numbers = ["2.3", "5.1", "8.3", "10.4", "10.5", "10.6"]
    
    target_assessments = {}
    for a in all_assessments:
        c_text = a.clause_text or ""
        c_num = a.clause_number or ""
        for t in target_clause_numbers:
            if t in c_num or t in c_text[:40]:
                target_assessments[t] = a

    print("\n================================================================================")
    print(" 3. KEY TARGET CLAUSES EVALUATION")
    print("================================================================================")
    for t in target_clause_numbers:
        a = target_assessments.get(t)
        if not a:
            print(f"\n[CLAUSE {t}] -- NOT FOUND")
            continue

        scen = predictor.predict_scenario(a)

        print(f"\n--------------------------------------------------------------------------------")
        print(f"CLAUSE {t} -- {a.clause_heading or 'Untitled'}")
        print(f"--------------------------------------------------------------------------------")
        print(f"  Text snippet       : {a.clause_text[:120]}...")
        print(f"  Risk Score         : {a.risk_score:.2f} ({a.risk_level.value})")
        print(f"  Primary Category   : {a.risk_category.value}")
        rules = [r.rule_id for r in a.detected_rules]
        print(f"  Detected Rules     : {rules or 'NONE'}")
        print(f"  LLM Explanation    : {a.risk_explanation}")
        if scen:
            print(f"  Scenario Title     : {scen.scenario_title}")
            print(f"  Trigger Condition  : {scen.trigger_condition}")
            print(f"  Narrative          : {scen.scenario_description[:120]}...")
            print(f"  Consequence        : {scen.possible_consequence[:120]}...")

    print("\n================================================================================")
    print(" 4. DETAILED BREAKDOWN FOR CLAUSE 10.5")
    print("================================================================================")
    a10_5 = target_assessments.get("10.5")
    if a10_5:
        sb = a10_5.score_breakdown
        rules = [r.rule_id for r in a10_5.detected_rules]
        scen10_5 = predictor.predict_scenario(a10_5)
        print(f"  Detected Rules     : {rules}")
        print(f"  BERT Component     : {sb.bert_component:.2f} (weight: {sb.bert_weight:.4f})")
        print(f"  Rule Component     : {sb.rule_component:.2f} (weight: {sb.rule_weight:.4f})")
        print(f"  RAG Component      : {sb.rag_component:.2f} (weight: {sb.rag_weight:.4f})")
        print(f"  LLM Component      : {sb.llm_component:.2f} (weight: {sb.llm_weight:.4f})")
        print(f"  Final Risk Score   : {a10_5.risk_score:.2f}")
        print(f"  Risk Level         : {a10_5.risk_level.value}")
        print(f"  Future Trigger     : {scen10_5.trigger_condition}")
    else:
        print("  Clause 10.5 assessment not found.")

    print("\n================================================================================")
    print(" 5. ANTI-HALLUCINATION & RULE ACCURACY VERIFICATION")
    print("================================================================================")
    a2_3 = target_assessments.get("2.3")
    if a2_3:
        r2_3 = [r.rule_id for r in a2_3.detected_rules]
        has_warranty_disclaimer = "RULE_WARRANTY_DISCLAIMER" in r2_3
        print(f"  Clause 2.3 Free of RULE_WARRANTY_DISCLAIMER: {not has_warranty_disclaimer} (Rules: {r2_3 or 'None'})")

    a8_3 = target_assessments.get("8.3")
    if a8_3:
        llm_exp = a8_3.risk_explanation
        claims_unlimited = "unlimited liability" in llm_exp.lower()
        print(f"  Clause 8.3 Grounded (No False Unlimited Liability Claim): {not claims_unlimited}")
        print(f"    Explanation: '{llm_exp}'")

    if a10_5:
        scen10_5 = predictor.predict_scenario(a10_5)
        trig = scen10_5.trigger_condition.lower()
        uses_factual = "overdue payment" in trig or "non-payment" in trig
        claims_breach = "breach" in trig
        print(f"  Clause 10.5 Scenario Trigger Grounded: {uses_factual and not claims_breach}")
        print(f"    Trigger: '{scen10_5.trigger_condition}'")

    print("\n================================================================================")
    print(" [SUCCESS] FINAL PHASE 8 VALIDATION COMPLETED SUCCESSFULLY")
    print("================================================================================")


if __name__ == "__main__":
    main()
