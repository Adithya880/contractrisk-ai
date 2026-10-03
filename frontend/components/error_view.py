"""
Error Screen Component for ContractRisk AI Single-Workflow Application.
Displays explicit error details when backend analysis fails or is unreachable,
offering single-click retry or full reset to State 1 (EMPTY).
"""

import streamlit as st
from frontend.utils.formatting import safe_render_html


def render_error_view():
    """Render dedicated error state screen."""
    error_msg = st.session_state.get("error_message", "An unexpected error occurred during contract analysis.")
    filename = st.session_state.get("current_filename", "Contract Document")

    # Centered Header
    safe_render_html(
        f"""
        <div style="text-align: center; margin-top: 2rem; margin-bottom: 2rem;">
            <div style="font-size: 2.5rem; color: #EF4444; line-height: 1; margin-bottom: 0.5rem;">◈</div>
            <h1 style="font-size: 1.85rem; font-weight: 800; letter-spacing: -0.02em; margin: 0 0 0.3rem 0;">
                CONTRACTRISK <span style="color: #38BDF8;">AI</span>
            </h1>
            <div style="font-size: 0.95rem; font-weight: 600; color: #94A3B8;">
                Document: <strong style="color: #F8FAFC;">{filename}</strong>
            </div>
        </div>
        """
    )

    # Centered Error Card
    err_col1, err_col2, err_col3 = st.columns([1, 6, 1])
    with err_col2:
        safe_render_html(
            f"""
            <div style="background: #10141E; border: 1px solid #2B1E22; border-left: 4px solid #EF4444; border-radius: 8px; padding: 20px 24px; margin-bottom: 24px;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;">
                    <span class="label-caps" style="color: #EF4444; font-weight: 700;">ANALYSIS ERROR</span>
                    <span style="font-size: 0.8rem; color: #64748B;">API Service / Execution Failure</span>
                </div>
                <div style="color: #F8FAFC; font-size: 0.95rem; font-weight: 600; line-height: 1.5; margin-bottom: 8px;">
                    {error_msg}
                </div>
                <div style="color: #8E9CAE; font-size: 0.84rem; line-height: 1.5;">
                    Please ensure the FastAPI service is running (<code>http://127.0.0.1:8000</code>) and the local LLM runtime is available, then click <strong>Try Again</strong>.
                </div>
            </div>
            """
        )

        # Action Buttons: [ Try Again ] and [ Analyze Another Contract ]
        btn_col1, btn_col2 = st.columns(2)

        with btn_col1:
            if st.button("Try Again", type="primary", width="stretch", key="btn_try_again"):
                st.session_state["workflow_state"] = "ANALYZING"
                st.session_state["pending_analysis"] = True
                st.session_state["error_message"] = None
                st.rerun()

        with btn_col2:
            if st.button("Analyze Another Contract", type="secondary", width="stretch", key="btn_error_reset"):
                st.session_state["workflow_state"] = "EMPTY"
                st.session_state["current_analysis"] = None
                st.session_state["current_file_bytes"] = None
                st.session_state["current_filename"] = None
                st.session_state["current_file_hash"] = None
                st.session_state["error_message"] = None
                st.session_state["pending_analysis"] = False
                st.session_state["uploader_key"] = st.session_state.get("uploader_key", 0) + 1
                st.rerun()

    safe_render_html("<div style='height: 40px;'></div>")
