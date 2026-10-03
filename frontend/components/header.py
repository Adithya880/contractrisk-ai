"""
Compact Top Header Component for ContractRisk AI.
"""

import streamlit as st
from frontend.utils.formatting import safe_render_html


def render_header(current_data: dict = None):
    """Render compact top application header and document status pill."""
    if current_data:
        doc = current_data.get("document", {})
        fname = doc.get("filename", "Contract Document")
        c_count = doc.get("number_of_clauses", len(current_data.get("clause_assessments", [])))
        right_html = f"""
        <div style="text-align: right;">
            <div style="font-size: 0.82rem; font-weight: 600; color: #10B981; display: flex; align-items: center; justify-content: flex-end; gap: 6px;">
                <span class="dot-online">●</span> Analysis ready
            </div>
            <div style="font-size: 0.88rem; color: #F1F5F9; font-weight: 500;">
                {fname} <span style="color: #5A677A;">· {c_count} clauses</span>
            </div>
        </div>
        """
    else:
        right_html = """
        <div style="text-align: right;">
            <div style="font-size: 0.82rem; color: #5A677A; display: flex; align-items: center; justify-content: flex-end; gap: 6px;">
                <span style="color: #5A677A;">○</span> No document loaded
            </div>
        </div>
        """

    safe_render_html(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: center; padding-bottom: 12px; margin-bottom: 18px; border-bottom: 1px solid #141A26;">
            <div>
                <div style="font-size: 1.25rem; font-weight: 700; color: #F8FAFC; letter-spacing: -0.01em;">
                    ContractRisk <span style="color: #38BDF8;">AI</span>
                </div>
                <div style="font-size: 0.8rem; color: #8E9CAE; margin-top: 1px;">
                    Contract Intelligence & Risk Analysis
                </div>
            </div>
            {right_html}
        </div>
        """
    )
