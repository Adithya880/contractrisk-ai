"""
Evidence Investigation Component for ContractRisk AI.
Provides strict visual separation between verbatim Contract Evidence and AI-generated explanations.
"""

import streamlit as st
from frontend.utils.formatting import safe_render_html


def render_evidence_view(data: dict):
    """Render RAG benchmark evidence and contractual text investigation view."""
    assessments = data.get("clause_assessments", [])
    doc_meta = data.get("document", {})
    source_filename = doc_meta.get("filename", "Contract Document")

    st.markdown("## Evidence Explorer")
    safe_render_html(
        """
        <div class="text-muted" style="margin-bottom: 16px; font-size: 0.88rem;">
            Verbatim contractual text and semantic benchmark retrieval citations vs AI-generated reasoning.
        </div>
        """
    )

    if not assessments:
        st.info("No clause evidence available for the active document.")
        return

    # Filter to only clauses with notable risk or citations to keep it clean
    flagged = [a for a in assessments if a.get("risk_score", 0) > 20 or (a.get("future_scenario") and a.get("future_scenario").get("supporting_evidence"))]
    if not flagged:
        flagged = assessments[:10]

    for a in flagged:
        c_num = a.get("clause_number", "")
        c_head = a.get("clause_heading") or "Untitled Clause"
        c_text = a.get("clause_text", "")
        explanation = a.get("llm_explanation", "No explanation recorded.")
        scen = a.get("future_scenario") or {}
        evidence_list = scen.get("supporting_evidence", [])

        citations_html = ""
        if evidence_list:
            parts = []
            for ev in evidence_list:
                if isinstance(ev, dict):
                    sim = ev.get("similarity_score", 0.75)
                    src_id = ev.get("source_clause_id", "Corpus")
                    parts.append(
                        f"<div style='margin-top: 8px; font-size: 0.78rem; color: #8E9CAE;'>"
                        f"Similarity: <strong style='color: #38BDF8;'>{sim:.2f}</strong> · Precedent: <em>{src_id}</em></div>"
                    )
            citations_html = "".join(parts)

        safe_render_html(
            f"""
            <div class="panel-primary" style="margin-bottom: 18px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <div>
                        <span class="label-caps" style="color: #38BDF8;">CLAUSE {c_num}</span>
                        <strong style="color: #F8FAFC; margin-left: 8px;">{c_head}</strong>
                    </div>
                    <span class="text-muted" style="font-size: 0.8rem;">Source: {source_filename}</span>
                </div>

                <!-- Two-Column Side by Side: Contract Evidence vs AI Explanation -->
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-top: 8px;">
                    <!-- Left: CONTRACT EVIDENCE -->
                    <div style="background: #0A0E17; border: 1px solid #1C2333; border-left: 3px solid #3B82F6; border-radius: 6px; padding: 12px 14px;">
                        <div class="label-caps" style="color: #60A5FA; margin-bottom: 6px;">CONTRACT EVIDENCE</div>
                        <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.84rem; color: #CBD5E1; line-height: 1.5;">
                            "{c_text}"
                        </div>
                        {citations_html}
                    </div>

                    <!-- Right: AI EXPLANATION -->
                    <div style="background: #0A0E17; border: 1px solid #1C2333; border-left: 3px solid #10B981; border-radius: 6px; padding: 12px 14px;">
                        <div class="label-caps" style="color: #34D399; margin-bottom: 6px;">AI EXPLANATION</div>
                        <div style="font-size: 0.86rem; color: #E2E8F0; line-height: 1.5;">
                            {explanation}
                        </div>
                    </div>
                </div>
            </div>
            """
        )
