"""
Analysis History Component for ContractRisk AI — Premium Dark Legal-Tech Dashboard.
Provides a clean document workspace listing recent analyses from PostgreSQL.
"""

import streamlit as st
from frontend.api_client import api_client, APIClientError
from frontend.utils.formatting import (
    normalize_analysis_data,
    safe_render_html
)


def render_history_view():
    """Render historical document workspace in dark legal-tech style."""
    safe_render_html(
        """
        <div style="margin-bottom: 20px;">
            <div style="font-size: 0.72rem; font-weight: 700; color: #8B5CF6; text-transform: uppercase; letter-spacing: 0.06em;">DOCUMENT ARCHIVE</div>
            <h2 style="font-size: 1.4rem; font-weight: 800; color: #F8FAFC; margin: 2px 0 4px 0;">Analysis History</h2>
            <div style="font-size: 0.85rem; color: #A1AFC2;">
                Previously analyzed contracts stored in the database.
            </div>
        </div>
        """
    )

    with st.spinner("Loading contract history..."):
        docs = api_client.get_documents_history(limit=50)

    if not docs:
        safe_render_html(
            """
            <div style="background: #182235; border: 1px solid #2D3A50; border-radius: 10px; padding: 36px 20px; text-align: center;">
                <div style="font-size: 2rem; margin-bottom: 6px;">📁</div>
                <div style="font-size: 1.0rem; font-weight: 700; color: #F8FAFC;">No Previous Analyses Found</div>
                <div style="color: #A1AFC2; font-size: 0.82rem; margin-top: 4px;">
                    Upload a contract in the Analyze Contract view to run an assessment.
                </div>
            </div>
            """
        )
        return

    # Search filter
    search_q = st.text_input(
        "Search History",
        placeholder="Search by contract name...",
        key="history_search_input",
        label_visibility="collapsed"
    )

    filtered_docs = docs
    if search_q.strip():
        q = search_q.strip().lower()
        filtered_docs = [
            d for d in docs
            if q in (d.get("filename") or "").lower()
            or q in str(d.get("document_id", "")).lower()
        ]

    st.caption(f"Showing {len(filtered_docs)} contract(s)")

    for d in filtered_docs:
        doc_id = d.get("document_id")
        fname = d.get("filename", "Contract Document")
        c_cnt = d.get("clause_count", 0)
        uploaded = (d.get("uploaded_at") or "")[:10]
        dtype = d.get("document_type", "PDF")

        col_info, col_act = st.columns([5, 1.2])

        with col_info:
            safe_render_html(
                f"""
                <div style="background: #182235; border: 1px solid #2D3A50; border-radius: 8px; padding: 12px 16px; margin-bottom: 8px; display: flex; align-items: center; justify-content: space-between;">
                    <div style="display: flex; align-items: center; gap: 12px;">
                        <span style="font-size: 1.3rem;">📄</span>
                        <div>
                            <strong style="color: #F8FAFC; font-size: 0.92rem;">{fname}</strong>
                            <div style="font-size: 0.76rem; color: #A1AFC2; margin-top: 2px;">
                                {c_cnt} clauses · {dtype} · Analyzed: {uploaded}
                            </div>
                        </div>
                    </div>
                    <span style="background: rgba(16, 185, 129, 0.12); color: #10B981; border: 1px solid rgba(16, 185, 129, 0.3); font-size: 0.70rem; font-weight: 700; padding: 2px 8px; border-radius: 9999px;">
                        READY
                    </span>
                </div>
                """
            )

        with col_act:
            st.markdown("<div style='height: 3px;'></div>", unsafe_allow_html=True)
            if st.button("Open Analysis", key=f"open_doc_{doc_id}", width="stretch", icon=":material/visibility:", type="primary"):
                try:
                    with st.spinner("Loading analysis..."):
                        raw_detail = api_client.get_document_detail(doc_id)
                        normalized = normalize_analysis_data(raw_detail)
                        st.session_state["current_analysis"] = normalized
                        st.session_state["workflow_state"] = "COMPLETE"
                        st.session_state["nav_selection"] = "Analyze Contract"
                        st.session_state["selected_clause_idx"] = 0
                        st.rerun()
                except APIClientError as err:
                    st.error(f"Failed to open document: {err}")

    safe_render_html("<div style='height: 20px;'></div>")
