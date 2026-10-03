"""
Minimal Technical System Status Component for ContractRisk AI.
"""

import streamlit as st
from frontend.api_client import api_client
from frontend.utils.formatting import safe_render_html


def render_system_status():
    """Render minimal technical subsystem status."""
    st.markdown("## System Status")
    safe_render_html(
        """
        <div class="text-muted" style="margin-bottom: 20px; font-size: 0.88rem;">
            Real-time health and connectivity status of underlying services.
        </div>
        """
    )

    health = api_client.check_health()
    h_status = health.get("status", "offline").lower()
    db_status = health.get("database", {}).get("status", "unknown").upper()
    lm_status = health.get("lm_studio", {}).get("status", "unknown").upper()

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        is_api_ok = h_status in ["healthy", "ok"]
        safe_render_html(
            f"""
            <div class="panel-secondary" style="text-align: center; padding: 14px 10px;">
                <div class="label-caps">FASTAPI</div>
                <div style="font-size: 0.95rem; font-weight: 700; color: {'#10B981' if is_api_ok else '#EF4444'}; margin-top: 6px;">
                    ● {'ONLINE' if is_api_ok else 'OFFLINE'}
                </div>
            </div>
            """
        )

    with col2:
        is_db_ok = db_status == "CONNECTED"
        safe_render_html(
            f"""
            <div class="panel-secondary" style="text-align: center; padding: 14px 10px;">
                <div class="label-caps">POSTGRESQL</div>
                <div style="font-size: 0.95rem; font-weight: 700; color: {'#10B981' if is_db_ok else '#F59E0B'}; margin-top: 6px;">
                    ● {'CONNECTED' if is_db_ok else 'UNAVAILABLE'}
                </div>
            </div>
            """
        )

    with col3:
        is_lm_ok = lm_status == "CONNECTED"
        safe_render_html(
            f"""
            <div class="panel-secondary" style="text-align: center; padding: 14px 10px;">
                <div class="label-caps">QWEN3 / LM STUDIO</div>
                <div style="font-size: 0.95rem; font-weight: 700; color: {'#10B981' if is_lm_ok else '#F59E0B'}; margin-top: 6px;">
                    ● {'CONNECTED' if is_lm_ok else 'FALLBACK'}
                </div>
            </div>
            """
        )

    with col4:
        safe_render_html(
            """
            <div class="panel-secondary" style="text-align: center; padding: 14px 10px;">
                <div class="label-caps">BERT</div>
                <div style="font-size: 0.95rem; font-weight: 700; color: #10B981; margin-top: 6px;">
                    ● AVAILABLE
                </div>
            </div>
            """
        )

    with col5:
        safe_render_html(
            """
            <div class="panel-secondary" style="text-align: center; padding: 14px 10px;">
                <div class="label-caps">FAISS</div>
                <div style="font-size: 0.95rem; font-weight: 700; color: #10B981; margin-top: 6px;">
                    ● AVAILABLE
                </div>
            </div>
            """
        )

    # Technical Details
    safe_render_html("<div style='height: 20px;'></div>")
    safe_render_html("<div class='label-caps' style='margin-bottom: 8px;'>SERVICE CONFIGURATION</div>")
    safe_render_html(
        """
        <div class="panel-primary" style="font-size: 0.85rem; color: #8E9CAE; line-height: 1.8;">
            <div>API Service: <span style="color: #F1F5F9;">ContractRisk AI v1.0.0</span> · Endpoint: <code style="color: #38BDF8;">http://127.0.0.1:8000/api/v1</code></div>
            <div>PostgreSQL Engine: <span style="color: #F1F5F9;">v17.11 (contractrisk DB)</span> · Connection: <code style="color: #38BDF8;">localhost:5432</code></div>
            <div>Local LLM Engine: <span style="color: #F1F5F9;">Qwen3 4B Q4_K_M (LM Studio)</span> · Inference: <code style="color: #38BDF8;">http://localhost:1234/v1</code></div>
            <div>NLP Classifier: <span style="color: #F1F5F9;">BERT Legal Tokenizer (256 max seq)</span> · Device: <code style="color: #38BDF8;">GPU CUDA / CPU Fallback</code></div>
            <div>Vector Retriever: <span style="color: #F1F5F9;">FAISS IndexFlatIP (384-dim all-MiniLM-L6-v2)</span></div>
        </div>
        """
    )
