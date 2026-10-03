"""
Diagnostic Investigation Script for Phase 8.2 Discrepancies.
Executes investigations A through F without modifying any source code.
"""

import sys
import os
import re
import importlib
from pathlib import Path

from src.risk_analysis.rules import RISK_RULES
from src.risk_analysis.rule_engine import RuleEngine
from src.risk_analysis.bert_risk_mapper import BERTRiskMapper
from src.risk_analysis.scoring import HybridScorer
from src.risk_analysis.analyzer import ContractRiskAnalyzer
from src.clause_segmentation.models import SegmentedClause, SegmentationResult
from src.document_processing.loader import DocumentLoader
from src.clause_segmentation.segmenter import ClauseSegmenter


def main():
    print("=" * 80)
    print(" PHASE 8.2 DIAGNOSTIC INVESTIGATION REPORT")
    print("=" * 80)

    # --- INVESTIGATION A: Inspect Loaded Rule Patterns ---
    print("\n--- INVESTIGATION A: Exact Rule Patterns in RISK_RULES ---")
    target_rule_ids = [
        "RULE_PRICE_UNILATERAL_ALTERATION",
        "RULE_MOD_UNILATERAL",
        "RULE_TERM_NO_NOTICE",
        "RULE_SUSPENSION_LATE_PAYMENT",
        "RULE_WARRANTY_DISCLAIMER"
    ]
    rule_dict = {r["rule_id"]: r for r in RISK_RULES}
    for rid in target_rule_ids:
        r = rule_dict.get(rid)
        if r:
            print(f"[{rid}]")
            print(f"  Severity Weight : {r['severity_weight']}")
            print(f"  Pattern Regex   : {r['pattern']}")
            print(f"  Description     : {r['description']}")
        else:
            print(f"[{rid}] MISSING FROM RISK_RULES!")

    # --- INVESTIGATION B & C: Direct RuleEngine Run on Clause Texts ---
    print("\n--- INVESTIGATION B & C: Direct RuleEngine Matching ---")
    test_clauses = {
        "Clause 5.1": "5.1 Prices quoted are subject to alteration without notice. Payment shall be due within 30 days of invoice date.",
        "Clause 10.4": "10.4 The Company may terminate this Agreement immediately without prior notice or refund of prepaid fees if Buyer fails to comply with any provision hereof.",
        "Clause 10.5": "10.5 The Company reserves the right to suspend or terminate services and access immediately following overdue payment or non-payment of any amounts due.",
        "Clause 2.3": "2.3 Preservation of Warranties. Nothing in these Terms and Conditions shall prejudice any condition or warranty, express or implied, or any legal remedy to which the Buyer may be entitled under statute or common law."
    }

    engine = RuleEngine()
    for name, text in test_clauses.items():
        matches = engine.analyze_clause(text)
        print(f"\nText [{name}]: {text}")
        if matches:
            for m in matches:
                print(f"  -> MATCHED: {m.rule_id} | Severity: {m.severity_weight} | Text: '{m.matched_text}'")
        else:
            print("  -> NO RULES MATCHED (0 matches)")

    # --- INVESTIGATION D: ContractRiskAnalyzer RuleEngine Invocation ---
    print("\n--- INVESTIGATION D: ContractRiskAnalyzer Invocation & Score Trace ---")
    analyzer = ContractRiskAnalyzer(rule_engine=engine)
    
    for name, text in test_clauses.items():
        seg_clause = SegmentedClause(
            clause_id=f"diag:{name}",
            document_id="diag_doc",
            clause_number=name.split()[1],
            clause_heading=name,
            clause_text=text,
            source_type="pdf",
            character_count=len(text),
            word_count=len(text.split()),
            source_pages=[1]
        )
        assessment = analyzer.analyze_clause(seg_clause, document_id="diag_doc")
        print(f"\nAssessment for [{name}]:")
        print(f"  Final Risk Score  : {assessment.risk_score:.2f} ({assessment.risk_level.value})")
        print(f"  BERT Component    : {assessment.score_breakdown.bert_component} (Weight: {assessment.score_breakdown.bert_weight})")
        print(f"  Rule Component    : {assessment.score_breakdown.rule_component} (Weight: {assessment.score_breakdown.rule_weight})")
        print(f"  RAG Component     : {assessment.score_breakdown.rag_component} (Weight: {assessment.score_breakdown.rag_weight})")
        print(f"  LLM Component     : {assessment.score_breakdown.llm_component} (Weight: {assessment.score_breakdown.llm_weight})")
        print(f"  Detected Rules    : {[r.rule_id for r in assessment.detected_rules]}")

    # --- INVESTIGATION E: Check PDF Document Ingestion in validate_phase8_2.py ---
    print("\n--- INVESTIGATION E: Ingestion & Segmentation Check of PDF File ---")
    pdf_path = Path("scratch/TermsandConditionsofSale_72Clauses.pdf")
    if pdf_path.exists():
        loader = DocumentLoader()
        segmenter = ClauseSegmenter()
        doc = loader.load_document(str(pdf_path))
        seg_res = segmenter.segment(doc)
        print(f"PDF File Path          : {pdf_path}")
        print(f"Segmented Clauses Count: {len(seg_res.clauses)}")
        
        # Check specific clauses extracted from PDF
        print("\nChecking extracted clauses from PDF file:")
        for c in seg_res.clauses:
            if any(num in c.clause_text for num in ["5.1", "10.4", "10.5", "2.3", "8.3"]):
                m = engine.analyze_clause(c.clause_text)
                print(f"  Clause ID: {c.clause_id} | Num: {c.clause_number} | Text snippet: '{c.clause_text[:70]}...'")
                print(f"    Direct Rule Engine Matches: {[match.rule_id for match in m]}")
    else:
        print(f"PDF File {pdf_path} not found.")

    print("\n================================================================================")
    print(" DIAGNOSTIC INVESTIGATION COMPLETE")
    print("================================================================================")


if __name__ == "__main__":
    main()
