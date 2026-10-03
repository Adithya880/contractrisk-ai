"""
Contract Analysis & Upload Workspace Component for ContractRisk AI.
"""

import streamlit as st
from frontend.api_client import api_client, APIClientError
from frontend.utils.formatting import normalize_analysis_data, safe_render_html


def render_contract_uploader():
    """Render compact, professional upload workspace and pipeline execution."""
    st.markdown("## Analyze Contract")
    safe_render_html(
        """
        <div class="text-muted" style="margin-bottom: 18px; font-size: 0.88rem;">
            Upload a PDF or DOCX contract to identify:
            <span style="color: #F1F5F9;">Risky clauses</span> · 
            <span style="color: #F1F5F9;">Supporting evidence</span> · 
            <span style="color: #F1F5F9;">Potential future scenarios</span>
        </div>
        """
    )

    uploaded_file = st.file_uploader(
        "Upload Contract Document",
        type=["pdf", "docx"],
        accept_multiple_files=False,
        label_visibility="collapsed",
        help="Upload PDF or DOCX contract up to 20 MB."
    )

    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        filename = uploaded_file.name
        file_size_kb = len(file_bytes) / 1024
        file_ext = filename.split(".")[-1].upper() if "." in filename else "PDF"

        # Compact File Metadata Row
        col_meta, col_btn = st.columns([3, 1])
        with col_meta:
            safe_render_html(
                f"""
                <div style="background: #0A0E17; border: 1px solid #1C2333; border-radius: 6px; padding: 10px 14px; font-size: 0.85rem;">
                    <span style="color: #8E9CAE; margin-right: 6px;">FILE:</span>
                    <strong style="color: #F8FAFC;">{filename}</strong>
                    <span style="color: #5A677A; margin-left: 8px;">({file_ext} · {file_size_kb:.1f} KB)</span>
                </div>
                """
            )

        with col_btn:
            analyze_clicked = st.button("Analyze Contract", type="primary", width="stretch")

        if analyze_clicked:
            if len(file_bytes) > 20 * 1024 * 1024:
                st.error("File size exceeds 20 MB limit.")
                return

            with st.status("Analyzing contract...", expanded=True) as status_box:
                st.write("1. Reading and parsing document layout...")
                st.write("2. Segmenting contractual clauses with boundary heuristics...")
                st.write("3. Evaluating BERT classification and 23 risk rules...")
                st.write("4. Retrieving benchmark RAG precedent evidence...")
                st.write("5. Projecting evidence-grounded future scenarios...")
                st.write("6. Committing transactional records to PostgreSQL...")

                try:
                    result = api_client.analyze_contract(file_bytes, filename)
                    normalized = normalize_analysis_data(result)
                    st.session_state["current_analysis"] = normalized
                    status_box.update(label="Analysis complete", state="complete", expanded=False)
                    st.success(f"✓ Analysis complete for {filename}.")
                except APIClientError as err:
                    status_box.update(label="Analysis failed", state="error", expanded=True)
                    st.error(f"Analysis failed: {err}")
                    return
                except Exception as ex:
                    status_box.update(label="Unexpected error", state="error", expanded=True)
                    st.error(f"Error during analysis: {ex}")
                    return

    # Post-Analysis Quick Actions
    current_data = st.session_state.get("current_analysis")
    if current_data:
        doc = current_data.get("document", {})
        fname = doc.get("filename", "Current Contract")
        summary = current_data.get("contract_summary", {})
        score = summary.get("risk_score", 0.0)
        level = summary.get("risk_level", "LOW")

        safe_render_html("<div style='height: 16px;'></div>")
        safe_render_html(
            f"""
            <div class="panel-primary" style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div class="label-caps">Active Analysis</div>
                    <div style="font-size: 1rem; font-weight: 600; color: #F8FAFC; margin-top: 2px;">{fname}</div>
                </div>
                <div style="text-align: right;">
                    <span style="font-size: 1.25rem; font-weight: 700; color: #F8FAFC;">{score:.2f} / 100</span>
                    <span style="margin-left: 8px; font-weight: 600; font-size: 0.82rem; color: #8E9CAE;">[{level}]</span>
                </div>
            </div>
            """
        )

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Explore Clauses →", width="stretch"):
                st.session_state["active_tab"] = "Clauses"
                st.rerun()
        with col_b:
            if st.button("View Future Scenarios →", width="stretch"):
                st.session_state["active_tab"] = "Scenarios"
                st.rerun()
