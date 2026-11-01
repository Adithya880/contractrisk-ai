"""
Formatting Helpers, Normalization, SVG Gauges, and Safe HTML Rendering Utilities
for ContractRisk AI — Premium Dark Legal-Tech Dashboard Theme.
"""

import textwrap
from typing import Dict, Any, Optional
import streamlit as st
from frontend.config import (
    RISK_LEVEL_COLORS,
    COLOR_LOW_RISK,
    COLOR_MEDIUM_RISK,
    COLOR_HIGH_RISK,
    COLOR_NORMAL_RISK,
    COLOR_PRIMARY
)


def get_risk_color(level: str) -> str:
    """Return Hex color code for given risk level."""
    return RISK_LEVEL_COLORS.get((level or "").upper(), "#A1AFC2")


def get_risk_badge_html(level: str) -> str:
    """Return clean HTML pill badge element for given risk level in dark theme."""
    lvl = (level or "NORMAL").upper()
    if lvl == "HIGH":
        return '<span class="badge-high">HIGH RISK</span>'
    elif lvl == "MEDIUM":
        return '<span class="badge-med">MEDIUM RISK</span>'
    elif lvl == "LOW":
        return '<span class="badge-low">LOW RISK</span>'
    else:
        return '<span class="badge-normal">NORMAL</span>'


def get_circular_score_svg(score: float, level: str, size: int = 120) -> str:
    """
    Generate crisp, responsive SVG circular gauge meter displaying risk score out of 100.
    All text elements are rendered natively inside the SVG coordinate system at fixed positions,
    guaranteeing that the score and denominator (/ 100) never overlap across any viewport or zoom.
    """
    try:
        val = max(0.0, min(100.0, float(score)))
    except (ValueError, TypeError):
        val = 0.0

    color = get_risk_color(level)
    radius = 46
    circumference = 2 * 3.1415926535 * radius  # ~289.03
    offset = circumference * (1.0 - (val / 100.0))

    return f"""
    <div style="display: flex; justify-content: center; align-items: center; margin: 4px 0;">
        <svg width="{size}" height="{size}" viewBox="0 0 120 120" style="display: block;">
            <!-- Background Track -->
            <circle cx="60" cy="60" r="{radius}" fill="none" stroke="#2D3A50" stroke-width="8" />
            <!-- Active Progress Arc (Rotated around SVG center 60,60) -->
            <circle cx="60" cy="60" r="{radius}" fill="none" stroke="{color}" stroke-width="8"
                    stroke-dasharray="{circumference:.2f}" stroke-dashoffset="{offset:.2f}"
                    stroke-linecap="round" transform="rotate(-90 60 60)" style="transition: stroke-dashoffset 0.5s ease;" />
            <!-- Centered Score Value (Upper Center) -->
            <text x="60" y="53" text-anchor="middle" dominant-baseline="middle"
                  font-family="'Inter', -apple-system, sans-serif" font-size="22" font-weight="800" fill="#F8FAFC">
                {val:.1f}
            </text>
            <!-- Denominator Label (Lower Center, spaced by 20 units) -->
            <text x="60" y="73" text-anchor="middle" dominant-baseline="middle"
                  font-family="'Inter', -apple-system, sans-serif" font-size="10" font-weight="600" fill="#A1AFC2">
                / 100
            </text>
        </svg>
    </div>
    """


def format_score(score: Any) -> str:
    """Format risk score to 1 decimal place."""
    try:
        return f"{float(score):.1f}"
    except (ValueError, TypeError):
        return "0.0"


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
        "risk_level": s0.get("risk_level", "NORMAL"),
        "normal_risk_clause_count": s0.get("normal_risk_count", 0),
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
                "description": rm.get("description", "Contractual risk condition"),
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
            "risk_level": ra.get("risk_level", "NORMAL"),
            "risk_category": ra.get("risk_category", "General Terms"),
            "rule_matches": rms,
            "evidence": [],
            "llm_explanation": c.get("risk_explanation") or ra.get("risk_explanation"),
            "llm_inference_status": "SKIPPED"
        })

    return {
        "document": doc_meta,
        "contract_summary": contract_summary,
        "clause_assessments": clause_assessments,
        "cross_clause_conflicts": [],
        "intra_clause_contradictions": []
    }
