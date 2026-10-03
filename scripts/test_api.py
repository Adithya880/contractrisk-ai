"""
CLI Verification & Live Smoke Test Script for Phase 8 FastAPI Production API.
Tests GET /api/v1/health, GET /api/v1/models, and POST /api/v1/analyze against real PDF/DOCX contracts.
"""

import sys
import io
import json
from pathlib import Path
from fastapi.testclient import TestClient

from src.api.main import app


def main():
    print("=" * 80)
    print(" CONTRACTRISK AI -- PHASE 8 FASTAPI PRODUCTION API SMOKE TEST")
    print("=" * 80)

    client = TestClient(app)

    # 1. Test GET /api/v1/health
    print("\n[1/3] Testing GET /api/v1/health Endpoint...", flush=True)
    resp_health = client.get("/api/v1/health")
    if resp_health.status_code != 200:
        print(f"[ERROR] Health check failed with HTTP {resp_health.status_code}: {resp_health.text}")
        sys.exit(1)

    health_data = resp_health.json()
    print(f"  Service Status : {health_data.get('status')}")
    print(f"  Service Name   : {health_data.get('service')}")
    print(f"  API Version    : {health_data.get('version')}")
    print("  [OK] Health Check Passed!")

    # 2. Test GET /api/v1/models
    print("\n[2/3] Testing GET /api/v1/models Endpoint...", flush=True)
    resp_models = client.get("/api/v1/models")
    if resp_models.status_code != 200:
        print(f"[ERROR] Models check failed with HTTP {resp_models.status_code}: {resp_models.text}")
        sys.exit(1)

    models_data = resp_models.json()
    print(f"  BERT Classifier: {models_data.get('bert_classifier', {}).get('name')}")
    print(f"  Embedding Model: {models_data.get('embedding_model', {}).get('name')}")
    print(f"  Vector Store   : {models_data.get('vector_store', {}).get('name')}")
    print(f"  Local LLM      : {models_data.get('local_llm', {}).get('name')}")
    print(f"  Predictor      : {models_data.get('scenario_predictor', {}).get('name')}")
    print("  [OK] Models Metadata Check Passed!")

    # 3. Test POST /api/v1/analyze with synthetic test contract PDF
    print("\n[3/3] Testing POST /api/v1/analyze Endpoint with Real Uploaded PDF Contract...", flush=True)

    # Use existing test PDF if available or create valid test PDF
    pdf_path = Path("data/splits/sample_contract.pdf")
    if not pdf_path.exists():
        # Look for any pdf in tests/ or create a valid minimal PDF
        import fitz
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text(
            (50, 100),
            "MASTER SERVICES AGREEMENT\n\n"
            "1.1 Effective Date. This Agreement is effective October 1, 2026.\n\n"
            "14.2 Limitation of Liability. Vendor shall have unlimited liability for gross negligence. "
            "Customer agrees to defend, indemnify and hold harmless Vendor from all claims and damages.\n\n"
            "8.1 Non-Compete. Contractor shall not engage in competing business for 2 years. "
            "This Agreement shall automatically renew."
        )
        pdf_path = Path("scratch/test_contract.pdf")
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        doc.save(str(pdf_path))

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    files = {"file": (pdf_path.name, pdf_bytes, "application/pdf")}

    resp_analyze = client.post("/api/v1/analyze", files=files)
    if resp_analyze.status_code != 200:
        print(f"[ERROR] Contract analysis endpoint failed with HTTP {resp_analyze.status_code}: {resp_analyze.text}")
        sys.exit(1)

    analyze_data = resp_analyze.json()

    doc_meta = analyze_data.get("document", {})
    summary = analyze_data.get("contract_summary", {})
    assessments = analyze_data.get("clause_assessments", [])

    print("\n================================================================================")
    print(f" FASTAPI ANALYSIS RESPONSE: {doc_meta.get('filename')}")
    print("================================================================================")
    print(f"  Document ID           : {doc_meta.get('document_id')}")
    print(f"  Document Format       : {doc_meta.get('document_type')}")
    print(f"  Segmented Clauses     : {doc_meta.get('number_of_clauses')}")
    print(f"  Contract Risk Score   : {summary.get('risk_score'):.2f} / 100.0")
    print(f"  Contract Risk Level   : {summary.get('risk_level')}")
    print(f"  HIGH Risk Clauses     : {summary.get('high_risk_clause_count')}")
    print(f"  MEDIUM Risk Clauses   : {summary.get('medium_risk_clause_count')}")
    print(f"  LOW Risk Clauses      : {summary.get('low_risk_clause_count')}")
    print("================================================================================\n")

    print("--- SAMPLE CLAUSE ASSESSMENT & FUTURE SCENARIO OUTPUT ---\n")
    if assessments:
        top_assess = assessments[0]
        print(f"Clause ID   : {top_assess.get('clause_id')}")
        print(f"Clause Num  : {top_assess.get('clause_number') or 'N/A'}")
        print(f"Heading     : {top_assess.get('clause_heading') or 'Untitled'}")
        print(f"Risk Score  : {top_assess.get('risk_score'):.2f} ({top_assess.get('risk_level')}) | Category: {top_assess.get('risk_category')}")
        print(f"BERT Label  : {top_assess.get('bert_label')} (Conf: {top_assess.get('bert_confidence'):.2f})")
        print(f"Explanation : {top_assess.get('llm_explanation')}")
        
        scen = top_assess.get("future_scenario")
        if scen:
            print("\nFUTURE SCENARIO PREDICTOR OUTPUT:")
            print(f"  Title              : {scen.get('scenario_title')}")
            print(f"  Trigger Condition  : {scen.get('trigger_condition')}")
            print(f"  Scenario Narrative : {scen.get('scenario_description')}")
            print(f"  Possible Impact    : {scen.get('possible_consequence')}")
            print(f"  Assumptions        : {', '.join(scen.get('assumptions', []))}")
            print(f"  Uncertainty        : {scen.get('uncertainty')}")
            print(f"  Fallback Active    : {scen.get('fallback_active')}")
        else:
            print("\nFUTURE SCENARIO PREDICTOR OUTPUT: None")
    else:
        print("[WARNING] No clause assessments returned in response.")

    print("\n================================================================================")
    print(" [SUCCESS] Phase 8 Live FastAPI Smoke Test Completed Successfully!")
    print("================================================================================")


if __name__ == "__main__":
    main()
