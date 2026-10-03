"""
Overview Dashboard Component for ContractRisk AI.
Follows compact, professional legal-tech intelligence UI principles.
"""

import streamlit as st
from frontend.utils.formatting import get_risk_badge_html, format_score, get_risk_color, safe_render_html


def render_dashboard(current_data: dict = None):
    """Render the primary ContractRisk AI executive overview."""

    # Top Header & Primary Action
    head_col, act_col = st.columns([3, 1])
    with head_col:
        safe_render_html(
            """
            <div style="margin-bottom: 14px;">
                <h2 style="margin: 0 0 2px 0;">CONTRACT RISK OVERVIEW</h2>
                <div class="text-muted" style="font-size: 0.88rem;">
                    Identified risk signals, severity distribution, and clause breakdown.
                </div>
            </div>
            """
        )

    with act_col:
        safe_render_html("<div style='height: 4px;'></div>")
        if st.button("+ Analyze New Contract", type="primary", width="stretch"):
            st.session_state["active_tab"] = "Analyze"
            st.rerun()

    # Empty State Check
    if not current_data:
        safe_render_html(
            """
            <div class="panel-primary" style="text-align: center; padding: 48px 24px; margin-top: 12px;">
                <div style="font-size: 1.8rem; margin-bottom: 8px; color: #5A677A;">📄</div>
                <h3 style="margin: 0 0 6px 0; color: #F1F5F9;">No contract loaded</h3>
                <p class="text-muted" style="margin: 0 0 16px 0; max-width: 420px; margin-left: auto; margin-right: auto; font-size: 0.88rem;">
                    Upload a contract document or select a historical analysis from the archive to inspect risks.
                </p>
            </div>
            """
        )
        return

    # Extract Backend Summary Values
    summary = current_data.get("contract_summary", {})
    doc_meta = current_data.get("document", {})

    score = summary.get("risk_score", 0.0)
    level = summary.get("risk_level", "LOW")
    high_cnt = summary.get("high_risk_clause_count", 0)
    med_cnt = summary.get("medium_risk_clause_count", 0)
    low_cnt = summary.get("low_risk_clause_count", 0)
    total_clauses = doc_meta.get("number_of_clauses", len(current_data.get("clause_assessments", [])))
    doc_name = doc_meta.get("filename", "Contract Document")
    doc_type = doc_meta.get("document_type", "PDF")

    total_dist = max(high_cnt + med_cnt + low_cnt, 1)
    pct_high = (high_cnt / total_dist) * 100
    pct_med = (med_cnt / total_dist) * 100
    pct_low = (low_cnt / total_dist) * 100

    # 1. Complete Risk Distribution Metric Row (4 columns)
    m1, m2, m3, m4 = st.columns(4)

    with m1:
        safe_render_html(
            f"""
            <div class="metric-box">
                <div class="metric-box-title">High Risk</div>
                <div class="metric-box-val" style="color: #EF4444;">{high_cnt}</div>
            </div>
            """
        )

    with m2:
        safe_render_html(
            f"""
            <div class="metric-box">
                <div class="metric-box-title">Medium Risk</div>
                <div class="metric-box-val" style="color: #F59E0B;">{med_cnt}</div>
            </div>
            """
        )

    with m3:
        safe_render_html(
            f"""
            <div class="metric-box">
                <div class="metric-box-title">Low Risk</div>
                <div class="metric-box-val" style="color: #10B981;">{low_cnt}</div>
            </div>
            """
        )

    with m4:
        safe_render_html(
            f"""
            <div class="metric-box">
                <div class="metric-box-title">Total Clauses</div>
                <div class="metric-box-val" style="color: #38BDF8;">{total_clauses}</div>
            </div>
            """
        )

    safe_render_html("<div style='height: 12px;'></div>")

    # 2. Risk Profile (~65%) and Contract Risk Score (~35%)
    col_profile, col_score = st.columns([13, 7])

    with col_profile:
        safe_render_html(
            f"""
            <div class="panel-primary" style="height: 100%;">
                <div class="label-caps" style="margin-bottom: 14px;">Risk Profile</div>
                
                <div style="margin-bottom: 14px;">
                    <div style="display: flex; justify-content: space-between; font-size: 0.82rem; margin-bottom: 4px;">
                        <span style="font-weight: 600; color: #EF4444;">HIGH</span>
                        <span style="color: #8E9CAE;"><strong>{high_cnt}</strong> clauses · {pct_high:.1f}%</span>
                    </div>
                    <div style="background: #1C2333; height: 8px; border-radius: 4px; overflow: hidden;">
                        <div style="background: #EF4444; width: {max(pct_high, 2) if high_cnt > 0 else 0}%; height: 100%; border-radius: 4px;"></div>
                    </div>
                </div>

                <div style="margin-bottom: 14px;">
                    <div style="display: flex; justify-content: space-between; font-size: 0.82rem; margin-bottom: 4px;">
                        <span style="font-weight: 600; color: #F59E0B;">MEDIUM</span>
                        <span style="color: #8E9CAE;"><strong>{med_cnt}</strong> clauses · {pct_med:.1f}%</span>
                    </div>
                    <div style="background: #1C2333; height: 8px; border-radius: 4px; overflow: hidden;">
                        <div style="background: #F59E0B; width: {max(pct_med, 2) if med_cnt > 0 else 0}%; height: 100%; border-radius: 4px;"></div>
                    </div>
                </div>

                <div style="margin-bottom: 6px;">
                    <div style="display: flex; justify-content: space-between; font-size: 0.82rem; margin-bottom: 4px;">
                        <span style="font-weight: 600; color: #10B981;">LOW</span>
                        <span style="color: #8E9CAE;"><strong>{low_cnt}</strong> clauses · {pct_low:.1f}%</span>
                    </div>
                    <div style="background: #1C2333; height: 8px; border-radius: 4px; overflow: hidden;">
                        <div style="background: #10B981; width: {max(pct_low, 2) if low_cnt > 0 else 0}%; height: 100%; border-radius: 4px;"></div>
                    </div>
                </div>
            </div>
            """
        )

    with col_score:
        score_val = float(score)
        gauge_pct = min(max(score_val, 0.0), 100.0)
        risk_c = get_risk_color(level)
        safe_render_html(
            f"""
            <div class="panel-primary" style="height: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center;">
                <div class="label-caps" style="margin-bottom: 8px;">Contract Risk Score</div>
                <div style="font-size: 3rem; font-weight: 800; color: #F8FAFC; line-height: 1;">
                    {format_score(score)} <span style="font-size: 1.1rem; color: #5A677A; font-weight: 500;">/ 100</span>
                </div>
                <div style="margin-top: 8px;">
                    {get_risk_badge_html(level)}
                </div>
                <div style="width: 80%; background: #1C2333; height: 6px; border-radius: 3px; margin-top: 16px; overflow: hidden;">
                    <div style="background: {risk_c}; width: {gauge_pct}%; height: 100%; border-radius: 3px;"></div>
                </div>
            </div>
            """
        )

    # 3. Document Context Row
    safe_render_html("<div style='height: 12px;'></div>")
    safe_render_html(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 14px; background: #0A0E17; border: 1px solid #141A26; border-radius: 6px; font-size: 0.85rem;">
            <div style="color: #8E9CAE;">
                <span class="label-caps" style="margin-right: 6px;">DOCUMENT:</span>
                <strong style="color: #F1F5F9;">{doc_name}</strong>
            </div>
            <div style="color: #5A677A;">
                <span>{total_clauses} clauses</span> · <span>{doc_type}</span> · <span style="color: #10B981;">● Analyzed</span>
            </div>
        </div>
        """
    )
