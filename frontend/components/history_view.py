"""
Analysis History Component for ContractRisk AI.
Provides a clean document workspace listing recent analyses from PostgreSQL.
"""

import streamlit as st
from frontend.api_client import api_client, APIClientError
from frontend.utils.formatting import normalize_analysis_data, get_risk_badge_html, safe_render_html


def render_history_view():
    """Render historical document workspace from GET /api/v1/documents."""
    st.markdown("## Recent Analyses")
    safe_render_html(
        """
        <div class="text-muted" style="margin-bottom: 16px; font-size: 0.88rem;">
            Persisted contract documents and prior risk evaluation runs stored in PostgreSQL.
        </div>
        """
    )

    with st.spinner("Loading document archive..."):
        docs = api_client.get_documents_history(limit=50)

    if not docs:
        safe_render_html(
            """
            <div class="panel-primary" style="text-align: center; padding: 36px 20px;">
                <div style="color: #8E9CAE; font-size: 0.9rem;">
                    No previous analyses found in database.
                </div>
            </div>
            """
        )
        return

    for d in docs:
        doc_id = d.get("document_id")
        fname = d.get("filename", "Contract Document")
        c_cnt = d.get("clause_count", 0)
        uploaded = (d.get("uploaded_at") or "")[:10]

        col_info, col_act = st.columns([4, 1])
        with col_info:
            safe_render_html(
                f"""
                <div class="panel-secondary" style="padding: 12px 16px; margin-bottom: 8px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong style="color: #F8FAFC; font-size: 0.95rem;">{fname}</strong>
                            <div class="text-muted" style="font-size: 0.8rem; margin-top: 2px;">
                                {c_cnt} clauses · {d.get('document_type', 'PDF')} · {uploaded}
                            </div>
                        </div>
                        <span style="font-size: 0.78rem; color: #10B981; font-weight: 600;">● READY</span>
                    </div>
                </div>
                """
            )
        with col_act:
            st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
            if st.button("Open", key=f"open_doc_{doc_id}", width="stretch"):
                try:
                    raw_detail = api_client.get_document_detail(doc_id)
                    normalized = normalize_analysis_data(raw_detail)
                    st.session_state["current_analysis"] = normalized
                    st.session_state["active_tab"] = "Overview"
                    st.rerun()
                except APIClientError as err:
                    st.error(f"Failed to open document: {err}")
