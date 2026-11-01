"""
Error Screen Component for ContractRisk AI — Premium Dark Legal-Tech Dashboard.
Displays explicit error details when backend analysis fails or is unreachable,
offering single-click retry or full reset.
"""

import streamlit as st
from frontend.utils.formatting import safe_render_html


def render_error_view():
    """Render dedicated error state screen in dark theme."""
    error_msg = st.session_state.get("error_message", "An unexpected error occurred during contract analysis.")
    filename = st.session_state.get("current_filename", "Contract Document")

    # Centered Header
    safe_render_html(
        f"""
        <div style="text-align: center; margin-top: 1.5rem; margin-bottom: 1.5rem;">
            <div style="width: 42px; height: 42px; background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 10px; display: inline-flex; align-items: center; justify-content: center; color: #EF4444; font-size: 1.4rem; font-weight: 800; margin-bottom: 8px;">
                ⚠️
            </div>
            <h2 style="font-size: 1.4rem; font-weight: 800; color: #F8FAFC; letter-spacing: -0.015em; margin: 0 0 4px 0;">
                Analysis Error Encountered
            </h2>
            <div style="font-size: 0.86rem; color: #A1AFC2;">
                Document: <strong style="color: #F8FAFC;">{filename}</strong>
            </div>
        </div>
        """
    )

    # Centered Error Card
    err_col1, err_col2, err_col3 = st.columns([1, 4, 1])
    with err_col2:
        safe_render_html(
            f"""
            <div style="background: #182235; border: 1px solid #2D3A50; border-left: 4px solid #EF4444; border-radius: 10px; padding: 18px 22px; margin-bottom: 18px;">
                <div style="font-size: 0.74rem; font-weight: 700; color: #EF4444; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px;">
                    EXECUTION EXCEPTION
                </div>
                <div style="color: #F8FAFC; font-size: 0.90rem; font-weight: 600; line-height: 1.5; margin-bottom: 8px;">
                    {error_msg}
                </div>
                <div style="color: #A1AFC2; font-size: 0.80rem; line-height: 1.45;">
                    Please check that the backend service is running, then click <strong>Try Again</strong>.
                </div>
            </div>
            """
        )

        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("Try Again", type="primary", width="stretch", key="btn_try_again", icon=":material/refresh:"):
                st.session_state["workflow_state"] = "ANALYZING"
                st.session_state["pending_analysis"] = True
                st.session_state["error_message"] = None
                st.rerun()

        with btn_col2:
            if st.button("Analyze Another Contract", type="secondary", width="stretch", key="btn_error_reset", icon=":material/add:"):
                st.session_state["workflow_state"] = "EMPTY"
                st.session_state["current_analysis"] = None
                st.session_state["current_file_bytes"] = None
                st.session_state["current_filename"] = None
                st.session_state["current_file_hash"] = None
                st.session_state["error_message"] = None
                st.session_state["pending_analysis"] = False
                st.session_state["uploader_key"] = st.session_state.get("uploader_key", 0) + 1
                st.rerun()

    safe_render_html("<div style='height: 30px;'></div>")
