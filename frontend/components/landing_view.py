"""
Contract Upload Screen for ContractRisk AI — Premium Dark Legal-Tech Dashboard.
Single, minimal upload interface directly below subtitle (States 1: EMPTY and 2: UPLOADED).
"""

import hashlib
import streamlit as st
from frontend.utils.formatting import safe_render_html


def render_landing_view():
    """Render minimal upload interface directly below page subtitle."""

    # 1. Page logo, title, and subtitle
    safe_render_html(
        """
        <div style="text-align: center; margin-top: 1.5rem; margin-bottom: 1.8rem;">
            <div style="width: 40px; height: 40px; background: #182235; border: 1px solid #2D3A50; border-radius: 10px; display: inline-flex; align-items: center; justify-content: center; color: #8B5CF6; font-size: 1.4rem; font-weight: 800; box-shadow: 0 4px 12px rgba(139, 92, 246, 0.15); margin-bottom: 0.75rem;">
                ◈
            </div>
            <h1 style="font-size: 2.0rem; font-weight: 800; color: #F8FAFC; letter-spacing: -0.02em; margin: 0 0 0.35rem 0;">
                Analyse Your Contract
            </h1>
            <p style="font-size: 0.92rem; color: #A1AFC2; max-width: 500px; margin: 0 auto; line-height: 1.5;">
                Upload a contract to identify potential risks and unfavorable terms.
            </p>
        </div>
        """
    )

    # 2. Centered Upload Area directly below subtitle
    upload_col1, upload_col2, upload_col3 = st.columns([1.5, 5, 1.5])

    with upload_col2:
        uploader_key = st.session_state.get("uploader_key", 0)
        uploaded_file = st.file_uploader(
            "Upload Contract",
            type=["pdf", "docx"],
            accept_multiple_files=False,
            label_visibility="collapsed",
            help="PDF or DOCX contract document up to 20 MB.",
            key=f"contract_uploader_{uploader_key}"
        )

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        if uploaded_file is not None:
            # -------------------------------------------------------------
            # STATE 2: UPLOADED (File selected, ready to analyze)
            # -------------------------------------------------------------
            file_bytes = uploaded_file.getvalue()
            filename = uploaded_file.name
            file_hash = hashlib.sha256(file_bytes).hexdigest()

            # Record uploaded document in session state
            st.session_state["current_file_bytes"] = file_bytes
            st.session_state["current_filename"] = filename
            st.session_state["current_file_hash"] = file_hash
            st.session_state["workflow_state"] = "UPLOADED"

            # Analyze Contract Button (ENABLED)
            if st.button("Analyze Contract", type="primary", width="stretch", key="btn_start_analysis", icon=":material/analytics:"):
                if len(file_bytes) > 20 * 1024 * 1024:
                    st.error("File size exceeds 20 MB maximum limit.")
                    return

                st.session_state["workflow_state"] = "ANALYZING"
                st.session_state["pending_analysis"] = True
                st.session_state["current_analysis"] = None
                st.session_state["error_message"] = None
                st.rerun()

        else:
            # -------------------------------------------------------------
            # STATE 1: EMPTY (No file selected)
            # -------------------------------------------------------------
            st.session_state["current_file_bytes"] = None
            st.session_state["current_filename"] = None
            st.session_state["current_file_hash"] = None
            st.session_state["workflow_state"] = "EMPTY"

            # Analyze Contract Button (DISABLED)
            st.button("Analyze Contract", type="primary", width="stretch", disabled=True, key="btn_disabled_analysis", icon=":material/analytics:")

    safe_render_html("<div style='height: 30px;'></div>")
