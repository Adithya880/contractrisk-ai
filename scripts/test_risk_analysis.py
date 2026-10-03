"""
CLI Verification & Live Smoke Test Script for Phase 7.1 Contract Risk Analysis.
Performs complete hybrid risk analysis on synthetic test contract clauses using live Qwen3 via LM Studio.
"""

import sys
import json
from src.clause_segmentation.models import SegmentedClause, SegmentationResult
from src.document_processing.models import SourceType
from src.risk_analysis.analyzer import ContractRiskAnalyzer


def main():
    print("=" * 80)
    print(" CONTRACTRISK AI -- PHASE 7.1 HYBRID RISK ANALYSIS SMOKE TEST")
    print("=" * 80)

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

    clauses = [
        SegmentedClause(
            clause_id="clause_001",
            document_id="doc_smoke_71",
            clause_number="14.2",
            clause_heading="Limitation of Liability & Indemnification",
            clause_text=c1_text,
            source_type=SourceType.PDF,
            source_pages=[5],
            character_count=len(c1_text),
            word_count=len(c1_text.split())
        ),
        SegmentedClause(
            clause_id="clause_002",
            document_id="doc_smoke_71",
            clause_number="8.1",
            clause_heading="Non-Compete & Renewal",
            clause_text=c2_text,
            source_type=SourceType.PDF,
            source_pages=[3],
            character_count=len(c2_text),
            word_count=len(c2_text.split())
        ),
        SegmentedClause(
            clause_id="clause_003",
            document_id="doc_smoke_71",
            clause_number="1.1",
            clause_heading="Effective Date & Governing Law",
            clause_text=c3_text,
            source_type=SourceType.PDF,
            source_pages=[1],
            character_count=len(c3_text),
            word_count=len(c3_text.split())
        )
    ]

    total_chars = sum(c.character_count for c in clauses)

    seg_result = SegmentationResult(
        document_id="doc_smoke_71",
        source_filename="synthetic_master_agreement.pdf",
        clauses=clauses,
        total_clauses=len(clauses),
        source_character_count=total_chars,
        segmented_character_count=total_chars,
        text_coverage_ratio=1.0
    )

    # Mock BERT predictions for synthetic clauses
    bert_predictions = {
        "clause_001": ("Uncapped Liability", 0.94),
        "clause_002": ("Non-Compete", 0.88),
        "clause_003": ("Effective Date", 0.96),
    }

    # Instantiate ContractRiskAnalyzer
    analyzer = ContractRiskAnalyzer()

    print("\n[INFO] Executing Hybrid Contract Risk Analysis...", flush=True)
    summary = analyzer.analyze_document(
        segmentation_result=seg_result,
        predicted_clause_types=bert_predictions
    )

    print("\n================================================================================")
    print(f" CONTRACT RISK PROFILE SUMMARY: {summary.source_filename}")
    print("================================================================================")
    print(f"  Document ID           : {summary.document_id}")
    print(f"  Contract Risk Score   : {summary.contract_risk_score:.2f} / 100.0")
    print(f"  Contract Risk Rating  : {summary.contract_risk_level.value}")
    print(f"  Total Clauses Analyzed: {summary.analyzed_clauses_count}")
    print(f"  HIGH Risk Clauses     : {summary.high_risk_clauses_count}")
    print(f"  MEDIUM Risk Clauses   : {summary.medium_risk_clauses_count}")
    print(f"  LOW Risk Clauses      : {summary.low_risk_clauses_count}")
    print("================================================================================\n")

    print("--- CLAUSE-LEVEL ASSESSMENT BREAKDOWN ---\n")
    for i, assess in enumerate(summary.highest_risk_assessments, 1):
        print(f"[{i}] Clause {assess.clause_number or ''} — {assess.clause_heading or 'Untitled'}")
        print(f"    Risk Score: {assess.risk_score:.2f} ({assess.risk_level.value}) | Category: {assess.risk_category.value}")
        print(f"    BERT Label: {assess.clause_type} (Conf: {assess.bert_confidence:.2f})")
        print(f"    Component Score Breakdown:")
        sb = assess.score_breakdown
        print(f"      - BERT (30%) : {sb.bert_component:.2f}  [Contrib: {sb.bert_component * 0.30:.2f}]")
        print(f"      - Rules (35%): {sb.rule_component:.2f}  [Contrib: {sb.rule_component * 0.35:.2f}]")
        print(f"      - RAG (15%)  : {sb.rag_component:.2f}  [Contrib: {sb.rag_component * 0.15:.2f}]")
        print(f"      - LLM (20%)  : {sb.llm_component:.2f}  [Contrib: {sb.llm_component * 0.20:.2f}]")
        print(f"    Detected Rules ({len(assess.detected_rules)}):")
        for r in assess.detected_rules:
            print(f"      * [{r.rule_id}] {r.description} (Sev: {r.severity_weight:.1f})")
        print(f"    LLM Explanation : {assess.risk_explanation}")
        print(f"    Key Risk Factors: {', '.join(assess.key_risk_factors) if assess.key_risk_factors else 'None'}")
        print(f"    Uncertainty     : {assess.uncertainty}")
        print("-" * 80)

    print("\n[SUCCESS] Phase 7.1 Live Risk Analysis Smoke Test Completed Successfully!")


if __name__ == "__main__":
    main()
