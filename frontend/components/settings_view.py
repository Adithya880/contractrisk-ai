"""
Settings Component for ContractRisk AI — Concept 1: Modern Professional Light Theme.
Provides interactive configuration of endpoints, scoring thresholds, and runtime diagnostics.
"""

import sys
import streamlit as st
from frontend.config import API_BASE_URL, CONFIDENCE_THRESHOLD
from frontend.api_client import api_client
from frontend.utils.formatting import safe_render_html


def render_settings_view():
    """Render Platform Settings & Configuration in Modern Professional Light Theme."""
    safe_render_html(
        """
        <div style="margin-bottom: 20px;">
            <div style="font-size: 0.76rem; font-weight: 700; color: #6842F5; text-transform: uppercase; letter-spacing: 0.06em;">ENVIRONMENT & PARAMETERS</div>
            <h2 style="font-size: 1.4rem; font-weight: 800; color: #17182B; margin: 2px 0 4px 0;">Platform Settings</h2>
            <div style="font-size: 0.85rem; color: #6B7280;">
                Configure API endpoints, classification confidence cutoffs, and decision risk scoring thresholds.
            </div>
        </div>
        """
    )

    col_left, col_right = st.columns(2, gap="large")

    # ---------------------------------------------------------
    # LEFT COLUMN: ENDPOINTS & CONNECTIVITY
    # ---------------------------------------------------------
    with col_left:
        safe_render_html(
            """
            <div style="background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.03); margin-bottom: 16px;">
                <div style="font-size: 0.95rem; font-weight: 700; color: #17182B; margin-bottom: 14px; display: flex; align-items: center; gap: 8px;">
                    <span style="color: #6842F5;">🌐</span> Service Endpoints
                </div>
            """
        )

        api_url = st.text_input(
            "FastAPI Backend URL",
            value=API_BASE_URL,
            key="cfg_api_url",
            help="Base URL of the ContractRisk AI FastAPI backend service."
        )

        lm_url = st.text_input(
            "LM Studio Local Server URL",
            value="http://127.0.0.1:1234/v1",
            key="cfg_lm_url",
            help="Local OpenAI-compatible endpoint hosting Qwen3."
        )

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

        if st.button("Test Subsystem Connectivity", icon=":material/network_check:", width="stretch", type="primary", key="btn_test_conn"):
            with st.spinner("Pinging services..."):
                health = api_client.check_health()
                h_status = health.get("status", "offline")
                db_status = health.get("database", {}).get("status", "unknown")
                lm_status = health.get("lm_studio", {}).get("status", "unknown")

                if h_status in ["healthy", "ok"]:
                    st.success("✓ FastAPI Backend is online and responsive.")
                else:
                    st.error(f"✗ FastAPI Backend unreachable: {health.get('detail', 'Connection refused')}")

                if db_status == "CONNECTED":
                    st.success("✓ PostgreSQL database connection active.")
                else:
                    st.warning("○ PostgreSQL database offline or in SQLite fallback mode.")

                if lm_status == "CONNECTED":
                    st.success("✓ LM Studio Qwen3 local server active.")
                else:
                    st.info("○ LM Studio local server offline (Qwen3 inference will be skipped).")

        safe_render_html("</div>")

    # ---------------------------------------------------------
    # RIGHT COLUMN: SCORING & CLASSIFICATION THRESHOLDS
    # ---------------------------------------------------------
    with col_right:
        safe_render_html(
            """
            <div style="background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.03); margin-bottom: 16px;">
                <div style="font-size: 0.95rem; font-weight: 700; color: #17182B; margin-bottom: 14px; display: flex; align-items: center; gap: 8px;">
                    <span style="color: #6842F5;">⚖️</span> Decision Thresholds
                </div>
            """
        )

        conf_thresh = st.slider(
            "BERT Classification Confidence Cutoff",
            min_value=0.50,
            max_value=0.95,
            value=float(st.session_state.get("conf_threshold", CONFIDENCE_THRESHOLD)),
            step=0.05,
            format="%.2f",
            help="Provisions with confidence below this threshold are flagged as uncertain for legal review.",
            key="slider_conf_threshold"
        )
        st.session_state["conf_threshold"] = conf_thresh

        high_thresh = st.slider(
            "High Risk Score Threshold",
            min_value=60,
            max_value=90,
            value=70,
            step=5,
            help="Clauses with calculated risk score at or above this value trigger HIGH RISK classification.",
            key="slider_high_risk_thresh"
        )

        med_thresh = st.slider(
            "Medium Risk Score Threshold",
            min_value=25,
            max_value=55,
            value=40,
            step=5,
            help="Clauses with risk score at or above this value trigger MEDIUM RISK classification.",
            key="slider_med_risk_thresh"
        )

        st.caption(f"Risk Buckets: Normal [0-{med_thresh}) · Medium [{med_thresh}-{high_thresh}) · High [{high_thresh}-100]")
        safe_render_html("</div>")

    # ---------------------------------------------------------
    # RUNTIME ENVIRONMENT METRICS
    # ---------------------------------------------------------
    safe_render_html(
        f"""
        <div style="background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px; padding: 18px 22px; box-shadow: 0 1px 3px rgba(0,0,0,0.03); margin-top: 10px;">
            <div style="font-size: 0.74rem; font-weight: 700; color: #6842F5; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px;">
                RUNTIME ENVIRONMENT
            </div>
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; font-size: 0.80rem;">
                <div>
                    <div style="color: #6B7280;">Python Version</div>
                    <strong style="color: #17182B;">{sys.version.split()[0]}</strong>
                </div>
                <div>
                    <div style="color: #6B7280;">Streamlit Version</div>
                    <strong style="color: #17182B;">{st.__version__}</strong>
                </div>
                <div>
                    <div style="color: #6B7280;">UI Theme</div>
                    <strong style="color: #6842F5;">Concept 1: Modern Pro Light</strong>
                </div>
                <div>
                    <div style="color: #6B7280;">Platform Mode</div>
                    <strong style="color: #10B981;">Hybrid Local + PyTorch</strong>
                </div>
            </div>
        </div>
        <div style="height: 24px;"></div>
        """
    )

