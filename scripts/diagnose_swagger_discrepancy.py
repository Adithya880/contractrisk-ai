"""
Diagnostic Investigation Script for FastAPI Swagger Discrepancy.
Traces FastAPI route execution, dependency injection, RuleEngine instance inspection,
and compares direct RuleEngine vs API RuleEngine behavior for Clauses 10.4, 5.1, 10.5, 2.3.
"""

import sys
import inspect
from pathlib import Path
import fitz  # PyMuPDF
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.dependencies import get_risk_analyzer, get_clause_segmenter, get_document_loader
from src.risk_analysis.rule_engine import RuleEngine
from src.risk_analysis.rules import RISK_RULES
from src.risk_analysis.analyzer import ContractRiskAnalyzer


def main():
    print("=" * 80)
    print(" DIAGNOSTIC INVESTIGATION: FASTAPI SWAGGER DISCREPANCY")
    print("=" * 80)

    # --- STEP 1 & 8 & 9: Dependency Injection & Analyzer Construction ---
    print("\n--- STEP 1, 8, 9: Dependency Injection & Analyzer Inspection ---")
    analyzer_from_dep = get_risk_analyzer()
    print(f"Analyzer Type from get_risk_analyzer(): {type(analyzer_from_dep)}")
    print(f"RuleEngine Instance inside Analyzer   : {analyzer_from_dep.rule_engine}")
    print(f"RuleEngine Type                        : {type(analyzer_from_dep.rule_engine)}")

    # --- STEP 3 & 4: Loaded Rules Inspection ---
    print("\n--- STEP 3 & 4: Loaded Rules in RuleEngine Instance ---")
    loaded_rules = getattr(analyzer_from_dep.rule_engine, "rules", None)
    if loaded_rules is None and hasattr(analyzer_from_dep.rule_engine, "rules_list"):
        loaded_rules = analyzer_from_dep.rule_engine.rules_list
    elif loaded_rules is None and hasattr(analyzer_from_dep.rule_engine, "risk_rules"):
        loaded_rules = analyzer_from_dep.rule_engine.risk_rules

    print(f"Loaded Rules Attribute Name: {[attr for attr in dir(analyzer_from_dep.rule_engine) if 'rule' in attr.lower()]}")
    print(f"Total Rules in Instance    : {len(RISK_RULES)}")

    target_rule_ids = ["RULE_MOD_UNILATERAL", "RULE_TERM_NO_NOTICE", "RULE_SUSPENSION_LATE_PAYMENT", "RULE_PRICE_UNILATERAL_ALTERATION", "RULE_WARRANTY_DISCLAIMER"]
    rule_dict = {r["rule_id"]: r for r in RISK_RULES}
    for rid in target_rule_ids:
        r = rule_dict.get(rid)
        print(f"  [{rid}]: Severity {r['severity_weight']} | Pattern: {r['pattern']}")

    # --- STEP 2, 5, 6, 10: Process PDFs via FastAPI TestClient & Compare Direct RuleEngine ---
    print("\n--- STEP 2, 5, 6, 10: Analyzing via FastAPI TestClient & Comparing Direct RuleEngine ---")
    
    # PDF 1: Standard 7-clause document
    pdf_path_7 = Path("scratch/TermsandConditionsofSale.pdf")
    if not pdf_path_7.exists():
        from scripts.verify_final_terms import build_final_terms_and_conditions_pdf
        build_final_terms_and_conditions_pdf(pdf_path_7)

    client = TestClient(app)

    with open(pdf_path_7, "rb") as f:
        pdf_bytes = f.read()

    files = {"file": ("TermsandConditionsofSale.pdf", pdf_bytes, "application/pdf")}
    print("\nSending POST /api/v1/analyze for TermsandConditionsofSale.pdf...")
    res = client.post("/api/v1/analyze", files=files)
    
    if res.status_code != 200:
        print(f"API Error {res.status_code}: {res.text}")
        return

    data = res.json()
    doc_meta = data.get("document", {})
    summary = data.get("contract_summary", {})
    clause_assessments = data.get("clause_assessments", [])

    print(f"Document ID        : {doc_meta.get('document_id')}")
    print(f"Number of Clauses  : {doc_meta.get('number_of_clauses')}")
    print(f"Assessments Return : {len(clause_assessments)} (top highest risk returned in JSON payload)")
    print(f"Contract Risk Score: {summary.get('risk_score'):.2f} ({summary.get('risk_level')})")

    standalone_engine = RuleEngine()

    print("\n--- CLAUSE-BY-CLAUSE API VS DIRECT RULEENGINE COMPARISON ---")
    for a in clause_assessments:
        c_num = a.get("clause_number", "")
        c_text = a.get("clause_text", "")
        c_score = a.get("risk_score")
        c_level = a.get("risk_level")
        api_rules = [r.get("rule_id") for r in a.get("rule_matches", [])]
        sb = a.get("component_score_breakdown", {})

        # Direct RuleEngine on exact clause text from API response
        direct_matches = standalone_engine.analyze_clause(c_text)
        direct_rule_ids = [m.rule_id for m in direct_matches]

        print(f"\n[Clause {c_num}] '{c_text[:80]}...'")
        print(f"  API Final Score        : {c_score} ({c_level})")
        print(f"  API Score Breakdown    : BERT={sb.get('bert_component')}, Rule={sb.get('rule_component')}, RAG={sb.get('rag_component')}, LLM={sb.get('llm_component')}")
        print(f"  API Rule Matches       : {api_rules}")
        print(f"  Direct Rule Engine Match: {direct_rule_ids}")
        print(f"  MATCHES EQUAL?         : {api_rules == direct_rule_ids}")

    print("\n================================================================================")
    print(" DIAGNOSTIC COMPLETED")
    print("================================================================================")


if __name__ == "__main__":
    main()
