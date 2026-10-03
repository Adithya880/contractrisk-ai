"""
Live API Smoke Test & Analysis Verification for TermsandConditionsofSale.pdf.
Creates a valid contract PDF with Clauses 2.3, 5.1, 10.4, 10.5, 10.6, and 14.2,
posts it to POST /api/v1/analyze, and reports complete calibration & scenario output.
"""

import sys
from pathlib import Path
import fitz  # PyMuPDF
from fastapi.testclient import TestClient
from src.api.main import app


def create_terms_and_conditions_pdf(pdf_path: Path):
    """Generate sample TermsandConditionsofSale.pdf file."""
    doc = fitz.open()
    
    # Page 1
    page1 = doc.new_page()
    page1.insert_text(
        (50, 80),
        "TERMS AND CONDITIONS OF SALE\n\n"
        "1.1 General Application. These Terms and Conditions apply to all sales of goods and services by the Company.\n\n"
        "2.3 Preservation of Warranties. Nothing in these Terms and Conditions shall prejudice any condition or warranty, "
        "express or implied, or any legal remedy to which the Buyer may be entitled under statute or common law.\n\n"
        "5.1 Prices and Payment. Prices quoted are subject to alteration without notice. "
        "Payment shall be due within 30 days of invoice date.\n\n"
        "8.1 Non-Compete. Contractor shall not engage in competing business during the term hereof."
    )
    
    # Page 2
    page2 = doc.new_page()
    page2.insert_text(
        (50, 80),
        "10.4 Termination without Notice. The Company may terminate this Agreement immediately without prior notice "
        "or refund of prepaid fees if Buyer fails to comply with any provision hereof.\n\n"
        "10.5 Suspension of Services. The Company reserves the right to suspend or terminate services and access "
        "immediately following overdue payment or non-payment of any amounts due.\n\n"
        "10.6 Reinstatement Terms. Reinstatement of suspended services or accounts shall require prior written approval "
        "by the Company and may be subject to new or different administrative fees and updated commercial terms.\n\n"
        "14.2 Limitation of Liability. Vendor shall have unlimited liability for gross negligence."
    )

    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(pdf_path))
    doc.close()


def main():
    print("=" * 80)
    print(" CONTRACTRISK AI -- PHASE 8.1 LIVE TERMS AND CONDITIONS OF SALE ANALYSIS")
    print("=" * 80)

    pdf_path = Path("scratch/TermsandConditionsofSale.pdf")
    create_terms_and_conditions_pdf(pdf_path)

    client = TestClient(app)

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    files = {"file": ("TermsandConditionsofSale.pdf", pdf_bytes, "application/pdf")}

    print("\nExecuting POST /api/v1/analyze against TermsandConditionsofSale.pdf...", flush=True)
    response = client.post("/api/v1/analyze", files=files)

    if response.status_code != 200:
        print(f"[ERROR] API failed with status {response.status_code}: {response.text}")
        sys.exit(1)

    data = response.json()
    doc_meta = data.get("document", {})
    summary = data.get("contract_summary", {})
    assessments = data.get("clause_assessments", [])

    print("\n================================================================================")
    print(f" DOCUMENT ANALYSIS SUMMARY: {doc_meta.get('filename')}")
    print("================================================================================")
    print(f"  Document ID         : {doc_meta.get('document_id')}")
    print(f"  Segmented Clauses   : {doc_meta.get('number_of_clauses')}")
    print(f"  Contract Risk Score : {summary.get('risk_score'):.2f} / 100.0")
    print(f"  Contract Risk Level : {summary.get('risk_level')}")
    print(f"  HIGH Risk Count     : {summary.get('high_risk_clause_count')}")
    print(f"  MEDIUM Risk Count   : {summary.get('medium_risk_clause_count')}")
    print(f"  LOW Risk Count      : {summary.get('low_risk_clause_count')}")
    print("================================================================================\n")

    target_clause_numbers = ["2.3", "5.1", "10.4", "10.5", "10.6"]

    print("--- TARGET CLAUSE ASSESSMENTS & FUTURE SCENARIO OUTPUTS ---\n")
    for a in assessments:
        c_num = a.get("clause_number")
        if c_num in target_clause_numbers or c_num == "14.2":
            print(f"--------------------------------------------------------------------------------")
            print(f"CLAUSE {c_num} -- {a.get('clause_heading') or 'Untitled'}")
            print(f"--------------------------------------------------------------------------------")
            print(f"  Text              : {a.get('clause_text')[:120]}...")
            print(f"  Risk Score        : {a.get('risk_score'):.2f} ({a.get('risk_level')})")
            print(f"  Primary Category  : {a.get('risk_category')}")
            print(f"  BERT Label        : {a.get('bert_label')} (Conf: {a.get('bert_confidence'):.2f})")
            
            rules = a.get("detected_rules", [])
            rule_str = ", ".join([f"{r.get('rule_id')} ({r.get('description')})" for r in rules]) if rules else "NONE (No False Positive)"
            print(f"  Detected Rules    : {rule_str}")
            print(f"  LLM Explanation   : {a.get('llm_explanation')}")

            scen = a.get("future_scenario")
            if scen:
                print("\n  FUTURE SCENARIO PREDICTOR:")
                print(f"    Title             : {scen.get('scenario_title')}")
                print(f"    Trigger Condition : {scen.get('trigger_condition')}")
                print(f"    Narrative         : {scen.get('scenario_description')}")
                print(f"    Consequence       : {scen.get('possible_consequence')}")
                print(f"    Assumptions       : {', '.join(scen.get('assumptions', []))}")
                print(f"    Uncertainty       : {scen.get('uncertainty')}")
                print(f"    Fallback Active   : {scen.get('fallback_active')}")
            print()

    print("================================================================================")
    print(" [SUCCESS] TermsandConditionsofSale.pdf Live API Smoke Test Completed!")
    print("================================================================================")


if __name__ == "__main__":
    main()
