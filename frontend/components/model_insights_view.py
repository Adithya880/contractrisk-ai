"""
Model Insights Component for ContractRisk AI — Concept 1: Modern Professional Light Theme.
Provides comprehensive architecture documentation, model specs, and live subsystem health.
"""

import streamlit as st
from frontend.api_client import api_client
from frontend.utils.formatting import safe_render_html


def render_model_insights_view():
    """Render Model Insights and technical telemetry in Modern Professional Light Theme."""
    safe_render_html(
        """
        <div style="margin-bottom: 20px;">
            <div style="font-size: 0.76rem; font-weight: 700; color: #6842F5; text-transform: uppercase; letter-spacing: 0.06em;">PIPELINE TRANSPARENCY & TELEMETRY</div>
            <h2 style="font-size: 1.4rem; font-weight: 800; color: #17182B; margin: 2px 0 4px 0;">Model Insights</h2>
            <div style="font-size: 0.85rem; color: #6B7280;">
                Technical specifications, model parameters, and real-time connectivity status of all underlying NLP components.
            </div>
        </div>
        """
    )

    # ---------------------------------------------------------
    # 1. LIVE SUBSYSTEM STATUS ROW
    # ---------------------------------------------------------
    health = api_client.check_health()
    h_status = health.get("status", "offline").lower()
    db_status = health.get("database", {}).get("status", "unknown").upper()
    lm_status = health.get("lm_studio", {}).get("status", "unknown").upper()

    col1, col2, col3, col4 = st.columns(4)

    is_api_ok = h_status in ["healthy", "ok"]
    is_db_ok = db_status == "CONNECTED"
    is_lm_ok = lm_status == "CONNECTED"

    with col1:
        safe_render_html(
            f"""
            <div style="background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 10px; padding: 14px 16px; box-shadow: 0 1px 2px rgba(0,0,0,0.02); text-align: center;">
                <div style="font-size: 0.72rem; font-weight: 700; color: #6B7280; text-transform: uppercase; letter-spacing: 0.05em;">FASTAPI BACKEND</div>
                <div style="font-size: 0.95rem; font-weight: 700; color: {'#10B981' if is_api_ok else '#EF4444'}; margin: 4px 0 2px 0;">
                    {'● ONLINE' if is_api_ok else '○ OFFLINE'}
                </div>
                <div style="font-size: 0.72rem; color: #9CA3AF;">Port 8000</div>
            </div>
            """
        )

    with col2:
        safe_render_html(
            f"""
            <div style="background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 10px; padding: 14px 16px; box-shadow: 0 1px 2px rgba(0,0,0,0.02); text-align: center;">
                <div style="font-size: 0.72rem; font-weight: 700; color: #6B7280; text-transform: uppercase; letter-spacing: 0.05em;">POSTGRESQL DB</div>
                <div style="font-size: 0.95rem; font-weight: 700; color: {'#10B981' if is_db_ok else '#F59E0B'}; margin: 4px 0 2px 0;">
                    {'● CONNECTED' if is_db_ok else '○ UNAVAILABLE'}
                </div>
                <div style="font-size: 0.72rem; color: #9CA3AF;">Port 5432</div>
            </div>
            """
        )

    with col3:
        safe_render_html(
            f"""
            <div style="background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 10px; padding: 14px 16px; box-shadow: 0 1px 2px rgba(0,0,0,0.02); text-align: center;">
                <div style="font-size: 0.72rem; font-weight: 700; color: #6B7280; text-transform: uppercase; letter-spacing: 0.05em;">QWEN3 / LM STUDIO</div>
                <div style="font-size: 0.95rem; font-weight: 700; color: {'#10B981' if is_lm_ok else '#6B7280'}; margin: 4px 0 2px 0;">
                    {'● ACTIVE' if is_lm_ok else '○ STANDBY'}
                </div>
                <div style="font-size: 0.72rem; color: #9CA3AF;">Port 1234 (Local)</div>
            </div>
            """
        )

    with col4:
        safe_render_html(
            """
            <div style="background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 10px; padding: 14px 16px; box-shadow: 0 1px 2px rgba(0,0,0,0.02); text-align: center;">
                <div style="font-size: 0.72rem; font-weight: 700; color: #6B7280; text-transform: uppercase; letter-spacing: 0.05em;">FAISS VECTOR INDEX</div>
                <div style="font-size: 0.95rem; font-weight: 700; color: #10B981; margin: 4px 0 2px 0;">
                    ● 9,447 VECTORS
                </div>
                <div style="font-size: 0.72rem; color: #9CA3AF;">384 Dimensions</div>
            </div>
            """
        )

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # 2. FOUR SPECIFICATION CARDS
    # ---------------------------------------------------------
    c_left, c_right = st.columns(2)

    with c_left:
        # Card 1: Fine-Tuned Legal BERT
        safe_render_html(
            """
            <div style="background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 10px; padding: 18px 20px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                    <div style="width: 32px; height: 32px; background: #FAF9FF; border: 1px solid #DDD6FE; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #6842F5; font-size: 1.1rem; font-weight: 800;">
                        ◈
                    </div>
                    <div>
                        <strong style="color: #17182B; font-size: 0.96rem;">Fine-Tuned Legal BERT Classifier</strong>
                        <div style="font-size: 0.74rem; color: #6B7280;">41 CUAD Contract Categories</div>
                    </div>
                </div>
                <div style="font-size: 0.82rem; color: #4B5563; line-height: 1.5; margin-bottom: 12px;">
                    Pre-trained on legal corpora and fine-tuned on the Contract Understanding Atticus Dataset (CUAD) to classify provisions into 41 standardized legal categories.
                </div>
                <div style="background: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 6px; padding: 10px 12px; font-size: 0.78rem;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                        <span style="color: #6B7280;">Architecture:</span>
                        <strong style="color: #17182B;">BERT Base (110M params)</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                        <span style="color: #6B7280;">Sequence Length:</span>
                        <strong style="color: #17182B;">512 Tokens</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: #6B7280;">Uncertainty Threshold:</span>
                        <strong style="color: #6842F5;">70.0% Confidence Cutoff</strong>
                    </div>
                </div>
            </div>
            """
        )

        # Card 2: Deterministic Rule Engine
        safe_render_html(
            """
            <div style="background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 10px; padding: 18px 20px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                    <div style="width: 32px; height: 32px; background: #FFFBEB; border: 1px solid #FDE68A; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #D97706; font-size: 1.1rem; font-weight: 800;">
                        ⚡
                    </div>
                    <div>
                        <strong style="color: #17182B; font-size: 0.96rem;">Deterministic Legal Rule Engine</strong>
                        <div style="font-size: 0.74rem; color: #6B7280;">39 Rules Across 13 Domains</div>
                    </div>
                </div>
                <div style="font-size: 0.82rem; color: #4B5563; line-height: 1.5; margin-bottom: 12px;">
                    Executes deterministic regex heuristics to detect asymmetric liability, uncapped indemnity, hidden auto-renewals, unilateral rights, and internal contradictions.
                </div>
                <div style="background: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 6px; padding: 10px 12px; font-size: 0.78rem;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                        <span style="color: #6B7280;">Compiled Rules:</span>
                        <strong style="color: #17182B;">39 Heuristics</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                        <span style="color: #6B7280;">Risk Domains:</span>
                        <strong style="color: #17182B;">13 Legal Categories</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: #6B7280;">Contradiction Scanner:</span>
                        <strong style="color: #10B981;">Intra- & Cross-Clause Active</strong>
                    </div>
                </div>
            </div>
            """
        )

    with c_right:
        # Card 3: FAISS Vector Index
        safe_render_html(
            """
            <div style="background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 10px; padding: 18px 20px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                    <div style="width: 32px; height: 32px; background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #2563EB; font-size: 1.1rem; font-weight: 800;">
                        🔍
                    </div>
                    <div>
                        <strong style="color: #17182B; font-size: 0.96rem;">FAISS Vector Index & Embeddings</strong>
                        <div style="font-size: 0.74rem; color: #6B7280;">Empirical Benchmark Retrieval</div>
                    </div>
                </div>
                <div style="font-size: 0.82rem; color: #4B5563; line-height: 1.5; margin-bottom: 12px;">
                    Stores 9,447 market contract provisions indexed via FAISS IndexFlatIP. Retrieves top-k semantically relevant precedents for benchmark comparison.
                </div>
                <div style="background: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 6px; padding: 10px 12px; font-size: 0.78rem;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                        <span style="color: #6B7280;">Embedding Model:</span>
                        <strong style="color: #17182B;">all-MiniLM-L6-v2 (384-d)</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                        <span style="color: #6B7280;">Total Precedent Vectors:</span>
                        <strong style="color: #17182B;">9,447 Indexed Clauses</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: #6B7280;">Metric:</span>
                        <strong style="color: #2563EB;">Normalized Inner Product</strong>
                    </div>
                </div>
            </div>
            """
        )

        # Card 4: Local Qwen3 LLM
        safe_render_html(
            """
            <div style="background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 10px; padding: 18px 20px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                    <div style="width: 32px; height: 32px; background: #ECFDF5; border: 1px solid #A7F3D0; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #059669; font-size: 1.1rem; font-weight: 800;">
                        🔒
                    </div>
                    <div>
                        <strong style="color: #17182B; font-size: 0.96rem;">Local Qwen3 LLM Integration</strong>
                        <div style="font-size: 0.74rem; color: #6B7280;">Zero-Leakage Local Inference</div>
                    </div>
                </div>
                <div style="font-size: 0.82rem; color: #4B5563; line-height: 1.5; margin-bottom: 12px;">
                    Integrates via local LM Studio OpenAI-compatible endpoint. Generates risk explanations and future scenarios entirely on-device without exposing confidential clauses.
                </div>
                <div style="background: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 6px; padding: 10px 12px; font-size: 0.78rem;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                        <span style="color: #6B7280;">Endpoint:</span>
                        <strong style="color: #17182B;">http://127.0.0.1:1234/v1</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                        <span style="color: #6B7280;">Model Family:</span>
                        <strong style="color: #17182B;">Qwen3-Instruct (32B / 7B)</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: #6B7280;">Cloud Telemetry:</span>
                        <strong style="color: #10B981;">0% (Fully Offline)</strong>
                    </div>
                </div>
            </div>
            """
        )

    # ---------------------------------------------------------
    # 3. PIPELINE ARCHITECTURE FLOW
    # ---------------------------------------------------------
    safe_render_html(
        """
        <div style="background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px; padding: 18px 22px; margin-top: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
            <div style="font-size: 0.74rem; font-weight: 700; color: #6842F5; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px;">
                END-TO-END PIPELINE ARCHITECTURE
            </div>
            <div style="font-size: 0.84rem; color: #4B5563; line-height: 1.5; margin-bottom: 14px;">
                The platform executes an 8-stage hybrid NLP pipeline combining statistical classifiers, deterministic rules, vector retrieval, and generative reasoning:
            </div>
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; font-size: 0.78rem;">
                <div style="background: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 6px; padding: 8px 10px;">
                    <strong style="color: #6842F5;">1. Extraction</strong>
                    <div style="color: #6B7280; font-size: 0.72rem; margin-top: 2px;">PDF/DOCX text & layout</div>
                </div>
                <div style="background: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 6px; padding: 8px 10px;">
                    <strong style="color: #6842F5;">2. Segmentation</strong>
                    <div style="color: #6B7280; font-size: 0.72rem; margin-top: 2px;">Clause boundary detection</div>
                </div>
                <div style="background: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 6px; padding: 8px 10px;">
                    <strong style="color: #6842F5;">3. Classification</strong>
                    <div style="color: #6B7280; font-size: 0.72rem; margin-top: 2px;">41 CUAD BERT classes</div>
                </div>
                <div style="background: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 6px; padding: 8px 10px;">
                    <strong style="color: #6842F5;">4. Rule Detection</strong>
                    <div style="color: #6B7280; font-size: 0.72rem; margin-top: 2px;">39 deterministic heuristics</div>
                </div>
                <div style="background: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 6px; padding: 8px 10px;">
                    <strong style="color: #6842F5;">5. Evidence (FAISS)</strong>
                    <div style="color: #6B7280; font-size: 0.72rem; margin-top: 2px;">9,447 market benchmarks</div>
                </div>
                <div style="background: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 6px; padding: 8px 10px;">
                    <strong style="color: #6842F5;">6. Qwen3 Reasoning</strong>
                    <div style="color: #6B7280; font-size: 0.72rem; margin-top: 2px;">Grounded risk explanation</div>
                </div>
                <div style="background: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 6px; padding: 8px 10px;">
                    <strong style="color: #6842F5;">7. Inconsistencies</strong>
                    <div style="color: #6B7280; font-size: 0.72rem; margin-top: 2px;">Intra & cross-clause scan</div>
                </div>
                <div style="background: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 6px; padding: 8px 10px;">
                    <strong style="color: #6842F5;">8. Scoring & Aggregation</strong>
                    <div style="color: #6B7280; font-size: 0.72rem; margin-top: 2px;">Calibrated /100 score</div>
                </div>
            </div>
        </div>
        <div style="height: 24px;"></div>
        """
    )

