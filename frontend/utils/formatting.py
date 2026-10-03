"""
Formatting Helpers, Normalization, and Safe HTML Rendering Utilities for ContractRisk AI.
"""

import textwrap
from typing import Dict, Any, Optional
import streamlit as st
from frontend.config import RISK_LEVEL_COLORS, COLOR_LOW_RISK, COLOR_MEDIUM_RISK, COLOR_HIGH_RISK


def get_risk_color(level: str) -> str:
    """Return Hex color code for given risk level."""
    return RISK_LEVEL_COLORS.get((level or "").upper(), "#8E9CAE")


def get_risk_badge_html(level: str) -> str:
    """Return clean HTML pill badge element for given risk level."""
    lvl = (level or "LOW").upper()
    if lvl == "HIGH":
        return '<span class="badge-high">HIGH</span>'
    elif lvl == "MEDIUM":
        return '<span class="badge-med">MEDIUM</span>'
    else:
        return '<span class="badge-low">LOW</span>'


def format_score(score: Any) -> str:
    """Format risk score to 2 decimal places."""
    try:
        return f"{float(score):.2f}"
    except (ValueError, TypeError):
        return "0.00"


def safe_render_html(html_str: str):
    """
    Safely render HTML without markdown parser turning indented blocks into <pre><code>.
    Uses st.html if supported, falling back to dedented st.markdown.
    """
    cleaned = textwrap.dedent(html_str).strip()
    if hasattr(st, "html"):
        st.html(cleaned)
    else:
        st.markdown(cleaned, unsafe_allow_html=True)


def normalize_analysis_data(data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Ensure uniform data structure whether data comes from fresh POST /analyze
    or historical GET /documents/{id}.
    """
    if not data:
        return None

    # If already in AnalysisResponse format
    if "clause_assessments" in data and "contract_summary" in data:
        return data

    # If from GET /documents/{id}
    summaries = data.get("summaries", [])
    s0 = summaries[0] if summaries else {}

    doc_meta = {
        "document_id": data.get("document_id", ""),
        "filename": data.get("filename", "Contract Document"),
        "document_type": data.get("document_type", "PDF"),
        "number_of_clauses": data.get("clause_count", len(data.get("clauses", [])))
    }

    contract_summary = {
        "risk_score": s0.get("risk_score", 0.0),
        "risk_level": s0.get("risk_level", "LOW"),
        "high_risk_clause_count": s0.get("high_risk_count", 0),
        "medium_risk_clause_count": s0.get("medium_risk_count", 0),
        "low_risk_clause_count": s0.get("low_risk_count", 0)
    }

    clause_assessments = []
    for idx, c in enumerate(data.get("clauses", [])):
        ra = c.get("risk_assessment") or {}
        rms = []
        for rm in ra.get("rule_matches", []):
            rms.append({
                "rule_id": rm.get("rule_id", "RULE"),
                "risk_category": ra.get("risk_category", "General"),
                "description": f"Triggered pattern {rm.get('rule_id')}",
                "severity_weight": rm.get("severity", 0.0),
                "matched_text": rm.get("matched_text", "")
            })

        final_sc = ra.get("final_score", 0.0)
        c_num = c.get("clause_number") or str(idx + 1)
        c_head = c.get("clause_title") or f"Clause {c_num}"

        clause_assessments.append({
            "clause_id": c.get("clause_id", f"cls_{idx}"),
            "clause_number": c_num,
            "clause_heading": c_head,
            "clause_text": c.get("clause_text", ""),
            "risk_score": final_sc,
            "risk_level": ra.get("risk_level", "LOW"),
            "risk_category": ra.get("risk_category", "General Terms"),
            "bert_label": ra.get("risk_category", "General"),
            "bert_confidence": 1.0,
            "rule_matches": rms,
            "component_score_breakdown": {
                "bert_component": 0.0,
                "rule_component": 0.0,
                "rag_component": 0.0,
                "llm_component": 0.0,
                "final_score": final_sc
            },
            "llm_explanation": ra.get("risk_explanation", "No explanation recorded."),
            "key_risk_factors": [],
            "uncertainty": "",
            "future_scenario": None
        })

    return {
        "document": doc_meta,
        "contract_summary": contract_summary,
        "clause_assessments": clause_assessments,
        "disclaimer": "Historical contract record retrieved from PostgreSQL repository."
    }
