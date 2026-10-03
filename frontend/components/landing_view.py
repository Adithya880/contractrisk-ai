"""
Landing and Upload Screen for ContractRisk AI Single-Workflow Application.
Implements State 1 (EMPTY) and State 2 (UPLOADED) with dynamic widget key reset
and Same Document Protection.
"""

import hashlib
import streamlit as st
from frontend.utils.formatting import safe_render_html


def render_landing_view():
    """Render the landing and upload interface (States 1: EMPTY and 2: UPLOADED)."""

    # Top Brand Header
    safe_render_html(
        """
        <div style="text-align: center; margin-top: 2rem; margin-bottom: 2.2rem;">
            <div style="font-size: 2.8rem; color: #38BDF8; line-height: 1; margin-bottom: 0.75rem;">◈</div>
            <h1 style="font-size: 2.1rem; font-weight: 800; letter-spacing: -0.02em; margin: 0 0 0.4rem 0;">
                CONTRACTRISK <span style="color: #38BDF8;">AI</span>
            </h1>
            <div style="font-size: 1.05rem; font-weight: 600; color: #94A3B8; margin-bottom: 0.9rem;">
                Intelligent Contract Risk Analysis
            </div>
            <p style="font-size: 0.94rem; color: #64748B; max-width: 560px; margin: 0 auto; line-height: 1.6;">
                Analyze contracts for potential risks using NLP, retrieval-augmented generation,
                and a local language model.
            </p>
        </div>
        """
    )

    # Central Upload Area
    upload_col1, upload_col2, upload_col3 = st.columns([1, 6, 1])

    with upload_col2:
        safe_render_html(
            """
            <div style="text-align: center; margin-bottom: 8px;">
                <span class="label-caps">UPLOAD CONTRACT</span>
            </div>
            """
        )

        uploader_key = st.session_state.get("uploader_key", 0)
        uploaded_file = st.file_uploader(
            "Upload Contract",
            type=["pdf", "docx"],
            accept_multiple_files=False,
            label_visibility="collapsed",
            help="PDF or DOCX contract document up to 20 MB.",
            key=f"contract_uploader_{uploader_key}"
        )

        if uploaded_file is not None:
            # -------------------------------------------------------------
            # STATE 2: UPLOADED (Document selected, not yet analyzed)
            # -------------------------------------------------------------
            file_bytes = uploaded_file.getvalue()
            filename = uploaded_file.name
            file_kb = len(file_bytes) / 1024
            file_ext = filename.split(".")[-1].upper() if "." in filename else "PDF"
            file_hash = hashlib.sha256(file_bytes).hexdigest()

            # Record uploaded document in session state
            st.session_state["current_file_bytes"] = file_bytes
            st.session_state["current_filename"] = filename
            st.session_state["current_file_hash"] = file_hash
            st.session_state["workflow_state"] = "UPLOADED"

            # Render document chip
            safe_render_html(
                f"""
                <div style="background: #0F141D; border: 1px solid #1C2333; border-radius: 8px; padding: 12px 16px; margin: 12px 0 16px 0; display: flex; justify-content: space-between; align-items: center;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="font-size: 1.25rem;">📄</span>
                        <div>
                            <strong style="color: #F8FAFC; font-size: 0.92rem;">{filename}</strong>
                            <div style="color: #64748B; font-size: 0.78rem;">{file_ext} Document</div>
                        </div>
                    </div>
                    <span style="color: #38BDF8; font-size: 0.82rem; font-weight: 600;">{file_kb:.1f} KB</span>
                </div>
                """
            )

            # Analyze Contract Button (ENABLED)
            if st.button("Analyze Contract", type="primary", width="stretch", key="btn_start_analysis"):
                if len(file_bytes) > 20 * 1024 * 1024:
                    st.error("File size exceeds 20 MB maximum limit.")
                    return

                # SAME DOCUMENT PROTECTION:
                # If this document was already analyzed in this session, return cached terminal result
                cached_analysis = st.session_state.get("analyzed_cache", {}).get(file_hash)
                if cached_analysis:
                    st.session_state["current_analysis"] = cached_analysis
                    st.session_state["workflow_state"] = "COMPLETE"
                    st.session_state["error_message"] = None
                    st.rerun()
                    return

                # Single execution transition to ANALYZING
                st.session_state["workflow_state"] = "ANALYZING"
                st.session_state["pending_analysis"] = True
                st.session_state["error_message"] = None
                st.rerun()

        else:
            # -------------------------------------------------------------
            # STATE 1: EMPTY (No document uploaded)
            # -------------------------------------------------------------
            st.session_state["current_file_bytes"] = None
            st.session_state["current_filename"] = None
            st.session_state["current_file_hash"] = None
            st.session_state["workflow_state"] = "EMPTY"

            safe_render_html("<div style='height: 8px;'></div>")
            st.button("Analyze Contract", type="primary", width="stretch", disabled=True, key="btn_disabled_analysis")

    safe_render_html("<div style='height: 40px;'></div>")
