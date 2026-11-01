"""
ContractRisk AI — Premium Dark Legal-Tech Dashboard.
Streamlit Frontend Main Application Entry Point with Simplified Navigation:
- Analyze Contract
- Analysis History
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path
root_path = Path(__file__).resolve().parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

import streamlit as st

# Configure Dark Wide Dashboard
st.set_page_config(
    page_title="ContractRisk AI — Contract Risk Analysis",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded"
)

from frontend.utils.formatting import safe_render_html
from frontend.components.header import render_top_header
from frontend.components.sidebar import render_sidebar
from frontend.components.landing_view import render_landing_view
from frontend.components.progress_view import render_progress_view
from frontend.components.results_view import render_results_view
from frontend.components.error_view import render_error_view
from frontend.components.history_view import render_history_view


def load_css():
    """Inject Premium Dark Theme stylesheet."""
    css_path = Path(__file__).parent / "styles" / "theme.css"
    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def init_session_state():
    """Initialize canonical workflow and navigation state variables."""
    if "nav_selection" not in st.session_state:
        st.session_state["nav_selection"] = "Analyze Contract"
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
    if "selected_clause_idx" not in st.session_state:
        st.session_state["selected_clause_idx"] = 0
    if "error_message" not in st.session_state:
        st.session_state["error_message"] = None
    if "pending_analysis" not in st.session_state:
        st.session_state["pending_analysis"] = False


def main():
    load_css()
    init_session_state()

    # Render Persistent Dark Sidebar
    render_sidebar()

    # Render Compact Top App Header
    render_top_header()

    # Main Navigation Router (Only 2 Core Views)
    active_nav = st.session_state.get("nav_selection", "Analyze Contract")

    if active_nav == "Analyze Contract":
        analysis_data = st.session_state.get("current_analysis")
        state = st.session_state.get("workflow_state", "EMPTY")

        if state == "COMPLETE" and analysis_data is not None:
            render_results_view(analysis_data)
        elif state == "ANALYZING":
            render_progress_view()
        elif state == "ERROR":
            render_error_view()
        else:
            render_landing_view()

    elif active_nav == "Analysis History":
        render_history_view()

    else:
        st.session_state["nav_selection"] = "Analyze Contract"
        st.rerun()


if __name__ == "__main__":
    main()
