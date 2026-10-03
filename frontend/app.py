"""
ContractRisk AI — Streamlit Frontend Main Application Entry Point.
Implements the 5-state terminal workflow state machine:
1. EMPTY       → Upload Contract, [ Analyze Contract ] (disabled)
2. UPLOADED    → Document chip, [ Analyze Contract ] (enabled)
3. ANALYZING   → Centered 8-stage progress screen (NO Analyze button)
4. COMPLETE    → Terminal analysis results, [ Analyze Another Contract ] (NO Analyze button)
5. ERROR       → Explicit error card, [ Try Again ], [ Analyze Another Contract ]
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path
root_path = Path(__file__).resolve().parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

import streamlit as st

# Configure Page: Centered single-column layout, sidebar collapsed
st.set_page_config(
    page_title="ContractRisk AI — Intelligent Contract Risk Analysis",
    page_icon="◈",
    layout="centered",
    initial_sidebar_state="collapsed"
)

from frontend.utils.formatting import safe_render_html
from frontend.components.landing_view import render_landing_view
from frontend.components.progress_view import render_progress_view
from frontend.components.results_view import render_results_view
from frontend.components.error_view import render_error_view


def load_css():
    """Inject custom dark legal-tech CSS stylesheet."""
    css_path = Path(__file__).parent / "styles" / "theme.css"
    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def init_session_state():
    """Initialize canonical workflow state variables."""
    if "workflow_state" not in st.session_state:
        st.session_state["workflow_state"] = "EMPTY"
    if "uploader_key" not in st.session_state:
        st.session_state["uploader_key"] = 0
    if "current_file_bytes" not in st.session_state:
        st.session_state["current_file_bytes"] = None
    if "current_filename" not in st.session_state:
        st.session_state["current_filename"] = None
    if "current_file_hash" not in st.session_state:
        st.session_state["current_file_hash"] = None
    if "current_analysis" not in st.session_state:
        st.session_state["current_analysis"] = None
    if "error_message" not in st.session_state:
        st.session_state["error_message"] = None
    if "analyzed_cache" not in st.session_state:
        st.session_state["analyzed_cache"] = {}
    if "pending_analysis" not in st.session_state:
        st.session_state["pending_analysis"] = False


def main():
    load_css()
    init_session_state()

    # -------------------------------------------------------------
    # TERMINAL STATE GUARD: State 4 (COMPLETE)
    # If an analysis result is present, the page must show ONLY results
    # and [ Analyze Another Contract ]. Never show "Analyze Contract".
    # -------------------------------------------------------------
    analysis_data = st.session_state.get("current_analysis")
    if analysis_data is not None:
        st.session_state["workflow_state"] = "COMPLETE"
        render_results_view(analysis_data)
        return

    # -------------------------------------------------------------
    # WORKFLOW STATE ROUTER
    # -------------------------------------------------------------
    state = st.session_state.get("workflow_state", "EMPTY")

    if state == "ANALYZING":
        render_progress_view()
    elif state == "ERROR":
        render_error_view()
    elif state in ("EMPTY", "UPLOADED"):
        render_landing_view()
    else:
        st.session_state["workflow_state"] = "EMPTY"
        render_landing_view()


if __name__ == "__main__":
    main()
