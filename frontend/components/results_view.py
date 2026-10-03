"""
Results Screen Component for ContractRisk AI Single-Workflow Application.
Renders one continuous results page including overall metrics, risk distribution,
important risky clauses with future scenarios, contract summary, and reset action.
"""

import streamlit as st
from frontend.utils.formatting import safe_render_html, get_risk_badge_html, format_score, get_risk_color


def render_results_view(data: dict):
    """Render the complete continuous results page."""
    doc_meta = data.get("document", {})
    summary = data.get("contract_summary", {})
    assessments = data.get("clause_assessments", [])

    filename = doc_meta.get("filename", "Contract Document")
    overall_score = summary.get("risk_score", 0.0)
    overall_level = (summary.get("risk_level") or "LOW").upper()
    high_cnt = summary.get("high_risk_clause_count", 0)
    med_cnt = summary.get("medium_risk_clause_count", 0)
    low_cnt = summary.get("low_risk_clause_count", 0)
    total_clauses = doc_meta.get("number_of_clauses", len(assessments))

    total_dist = max(high_cnt + med_cnt + low_cnt, 1)
    pct_high = (high_cnt / total_dist) * 100
    pct_med = (med_cnt / total_dist) * 100
    pct_low = (low_cnt / total_dist) * 100

    # -------------------------------------------------------------
    # 1. TOP HEADER
    # -------------------------------------------------------------
    safe_render_html(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: center; padding-bottom: 14px; margin-bottom: 22px; border-bottom: 1px solid #1E293B;">
            <div>
                <div style="font-size: 1.35rem; font-weight: 800; color: #F8FAFC; letter-spacing: -0.01em;">
                    ◈ CONTRACTRISK <span style="color: #38BDF8;">AI</span>
                </div>
                <div style="font-size: 0.92rem; color: #94A3B8; margin-top: 2px;">
                    {filename}
                </div>
            </div>
            <div style="text-align: right;">
                <span class="badge-done">✓ ANALYSIS COMPLETE</span>
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; color: #10B981; font-weight: 700; margin-top: 4px;">
                    100%
                </div>
            </div>
        </div>
        """
    )

    # -------------------------------------------------------------
    # 2. COMPACT SUMMARY (5 Metrics Row)
    # -------------------------------------------------------------
    col1, col2, col3, col4, col5 = st.columns(5)

    risk_badge = get_risk_badge_html(overall_level)
    with col1:
        safe_render_html(
            f"""
            <div class="metric-box">
                <div class="metric-box-title">OVERALL RISK</div>
                <div style="margin-top: 6px; margin-bottom: 4px;">{risk_badge}</div>
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; color: #8E9CAE;">
                    Score: <strong style="color: #F8FAFC;">{format_score(overall_score)}</strong>/100
                </div>
            </div>
            """
        )

    with col2:
        safe_render_html(
            f"""
            <div class="metric-box">
                <div class="metric-box-title">HIGH RISK CLAUSES</div>
                <div class="metric-box-val" style="color: #EF4444;">{high_cnt}</div>
            </div>
            """
        )

    with col3:
        safe_render_html(
            f"""
            <div class="metric-box">
                <div class="metric-box-title">MEDIUM RISK CLAUSES</div>
                <div class="metric-box-val" style="color: #F59E0B;">{med_cnt}</div>
            </div>
            """
        )

    with col4:
        safe_render_html(
            f"""
            <div class="metric-box">
                <div class="metric-box-title">LOW RISK CLAUSES</div>
                <div class="metric-box-val" style="color: #10B981;">{low_cnt}</div>
            </div>
            """
        )

    with col5:
        safe_render_html(
            f"""
            <div class="metric-box">
                <div class="metric-box-title">TOTAL CLAUSES</div>
                <div class="metric-box-val" style="color: #38BDF8;">{total_clauses}</div>
            </div>
            """
        )

    safe_render_html("<div style='height: 18px;'></div>")

    # -------------------------------------------------------------
    # 3. RISK DISTRIBUTION
    # -------------------------------------------------------------
    safe_render_html(
        f"""
        <div class="panel-primary" style="margin-bottom: 26px;">
            <div class="label-caps" style="margin-bottom: 14px;">RISK DISTRIBUTION</div>

            <!-- High Bar -->
            <div style="margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between; font-size: 0.82rem; margin-bottom: 4px;">
                    <span style="font-weight: 700; color: #EF4444;">HIGH</span>
                    <span style="color: #8E9CAE;"><strong>{high_cnt}</strong> clauses ({pct_high:.1f}%)</span>
                </div>
                <div style="background: #111827; height: 8px; border-radius: 4px; overflow: hidden;">
                    <div style="background: #EF4444; width: {max(pct_high, 2) if high_cnt > 0 else 0}%; height: 100%; border-radius: 4px;"></div>
                </div>
            </div>

            <!-- Medium Bar -->
            <div style="margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between; font-size: 0.82rem; margin-bottom: 4px;">
                    <span style="font-weight: 700; color: #F59E0B;">MEDIUM</span>
                    <span style="color: #8E9CAE;"><strong>{med_cnt}</strong> clauses ({pct_med:.1f}%)</span>
                </div>
                <div style="background: #111827; height: 8px; border-radius: 4px; overflow: hidden;">
                    <div style="background: #F59E0B; width: {max(pct_med, 2) if med_cnt > 0 else 0}%; height: 100%; border-radius: 4px;"></div>
                </div>
            </div>

            <!-- Low Bar -->
            <div>
                <div style="display: flex; justify-content: space-between; font-size: 0.82rem; margin-bottom: 4px;">
                    <span style="font-weight: 700; color: #10B981;">LOW</span>
                    <span style="color: #8E9CAE;"><strong>{low_cnt}</strong> clauses ({pct_low:.1f}%)</span>
                </div>
                <div style="background: #111827; height: 8px; border-radius: 4px; overflow: hidden;">
                    <div style="background: #10B981; width: {max(pct_low, 2) if low_cnt > 0 else 0}%; height: 100%; border-radius: 4px;"></div>
                </div>
            </div>
        </div>
        """
    )

    # -------------------------------------------------------------
    # 4. IMPORTANT RISKY CLAUSES (Sorted by Risk Score Descending)
    # -------------------------------------------------------------
    safe_render_html(
        """
        <div style="margin-bottom: 14px;">
            <h2 style="margin: 0 0 2px 0;">IMPORTANT RISKY CLAUSES</h2>
            <div class="text-muted" style="font-size: 0.88rem;">
                Contractual clauses with detected risks, evidence grounding, and causal future scenario projections.
            </div>
        </div>
        """
    )

    sorted_clauses = sorted(
        assessments,
        key=lambda c: float(c.get("risk_score", 0.0)),
        reverse=True
    )

    risky_clauses = [c for c in sorted_clauses if (c.get("risk_level") or "").upper() in ["HIGH", "MEDIUM"]]
    low_clauses = [c for c in sorted_clauses if (c.get("risk_level") or "").upper() == "LOW"]

    # Display risky clauses or banner if none
    display_clauses = risky_clauses if risky_clauses else sorted_clauses[:5]

    if not display_clauses:
        safe_render_html(
            """
            <div class="panel-primary" style="text-align: center; padding: 28px; margin-bottom: 24px;">
                <div style="color: #10B981; font-size: 0.95rem;">
                    ✓ No high or medium risk clauses detected in the analyzed document.
                </div>
            </div>
            """
        )
    else:
        for idx, clause in enumerate(display_clauses, 1):
            c_num = clause.get("clause_number") or str(idx)
            c_title = clause.get("clause_heading") or f"Clause {c_num}"
            c_cat = clause.get("risk_category", "General Terms")
            c_level = (clause.get("risk_level") or "LOW").upper()
            c_score = clause.get("risk_score", 0.0)
            c_text = clause.get("clause_text", "")
            c_explanation = clause.get("llm_explanation", "No specific risk factors flagged.")
            scen = clause.get("future_scenario") or {}

            # Supporting evidence citations
            evidence_list = scen.get("supporting_evidence", [])
            citations_html = ""
            if evidence_list:
                cit_items = []
                for ev in evidence_list:
                    if isinstance(ev, dict):
                        sim = ev.get("similarity_score", 0.75)
                        src_id = ev.get("source_clause_id", "Precedent")
                        cit_items.append(
                            f"<div style='font-size: 0.8rem; color: #8E9CAE; margin-top: 4px;'>"
                            f"Similarity: <strong style='color: #38BDF8;'>{sim:.2f}</strong> · Precedent Source: <em>{src_id}</em>"
                            f"</div>"
                        )
                if cit_items:
                    citations_html = f"""
                    <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid #1C2333;">
                        <span class="label-caps" style="color: #8B5CF6;">SUPPORTING EVIDENCE / RETRIEVED CLAUSES</span>
                        {"".join(cit_items)}
                    </div>
                    """

            # Future Scenario Section (Novelty)
            scenario_html = ""
            if scen:
                scen_title = scen.get("scenario_title", "Hypothetical Scenario")
                raw_trigger = (scen.get("trigger_condition") or "").strip()
                clean_trigger = raw_trigger[3:].strip() if raw_trigger.lower().startswith("if ") else raw_trigger
                trajectory = scen.get("scenario_description", "")
                consequence = scen.get("possible_consequence", "")
                assumptions = scen.get("assumptions", [])
                uncertainty = scen.get("uncertainty", "")

                assump_text = " · ".join(assumptions) if assumptions else "No secondary assumptions required."

                scenario_html = f"""
                <div class="scenario-card-violet" style="margin-top: 16px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid #231E3D;">
                        <span class="label-caps" style="color: #A78BFA;">FUTURE SCENARIO PREDICTOR</span>
                        <span style="font-size: 0.8rem; color: #8E9CAE;">{scen_title}</span>
                    </div>

                    <!-- Flow Diagram: CLAUSE -> TRIGGER -> SCENARIO -> CONSEQUENCE -->
                    <div style="display: flex; flex-direction: column; gap: 8px;">
                        <!-- 1. Trigger Condition -->
                        <div style="background: #111422; border: 1px solid #282442; border-radius: 6px; padding: 10px 14px;">
                            <div class="label-caps" style="color: #F59E0B; margin-bottom: 4px;">TRIGGER CONDITION</div>
                            <div style="color: #F1F5F9; font-size: 0.88rem;"><em>If</em> {clean_trigger}</div>
                        </div>

                        <div class="flow-arrow">↓</div>

                        <!-- 2. Potential Scenario -->
                        <div style="background: #111422; border: 1px solid #282442; border-radius: 6px; padding: 10px 14px;">
                            <div class="label-caps" style="color: #A78BFA; margin-bottom: 4px;">POTENTIAL SCENARIO</div>
                            <div style="color: #CBD5E1; font-size: 0.88rem; line-height: 1.5;">{trajectory}</div>
                        </div>

                        <div class="flow-arrow">↓</div>

                        <!-- 3. Possible Consequence -->
                        <div style="background: #111422; border: 1px solid #282442; border-radius: 6px; padding: 10px 14px;">
                            <div class="label-caps" style="color: #EF4444; margin-bottom: 4px;">POSSIBLE CONSEQUENCE</div>
                            <div style="color: #F87171; font-size: 0.88rem;">{consequence}</div>
                        </div>
                    </div>

                    <!-- Assumptions and Uncertainty -->
                    <div style="margin-top: 12px; padding-top: 10px; border-top: 1px solid #231E3D; font-size: 0.8rem; color: #8E9CAE;">
                        <div><strong style="color: #A78BFA;">Assumptions:</strong> {assump_text}</div>
                        {f'<div style="margin-top: 4px;"><strong style="color: #A78BFA;">Uncertainty:</strong> {uncertainty}</div>' if uncertainty else ''}
                    </div>
                </div>
                """

            safe_render_html(
                f"""
                <div class="panel-primary" style="margin-bottom: 20px;">
                    <!-- Clause Header -->
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
                        <div>
                            <span class="label-caps" style="color: #38BDF8;">CLAUSE {c_num}</span>
                            <h3 style="margin: 2px 0 2px 0; color: #F8FAFC;">{c_title}</h3>
                            <div class="text-muted" style="font-size: 0.8rem;">Category: {c_cat}</div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-family: 'JetBrains Mono', monospace; font-size: 1.25rem; font-weight: 700; color: #F8FAFC;">
                                {format_score(c_score)} <span style="font-size: 0.8rem; color: #5A677A;">/ 100</span>
                            </div>
                            <div style="margin-top: 4px;">{get_risk_badge_html(c_level)}</div>
                        </div>
                    </div>

                    <!-- Why it is risky -->
                    <div style="margin-bottom: 12px;">
                        <div class="label-caps" style="margin-bottom: 4px;">WHY IT IS RISKY</div>
                        <div style="font-size: 0.88rem; color: #E2E8F0; line-height: 1.5; background: #151B26; border-radius: 6px; padding: 10px 14px;">
                            {c_explanation}
                        </div>
                    </div>

                    <!-- Exact contractual evidence -->
                    <div style="margin-bottom: 12px;">
                        <div class="label-caps" style="margin-bottom: 4px;">EXACT CONTRACTUAL EVIDENCE</div>
                        <div class="contract-text-panel">
                            "{c_text}"
                        </div>
                    </div>

                    {citations_html}
                    {scenario_html}
                </div>
                """
            )

        if low_clauses and risky_clauses:
            with st.expander(f"View Standard & Routine Clauses ({len(low_clauses)} evaluated)"):
                for l_clause in low_clauses:
                    l_num = l_clause.get("clause_number") or ""
                    l_title = l_clause.get("clause_heading") or f"Clause {l_num}"
                    l_score = l_clause.get("risk_score", 0.0)
                    l_text = l_clause.get("clause_text", "")
                    l_cat = l_clause.get("risk_category", "General Terms")
                    st.markdown(
                        f"**{l_num} {l_title}** — Risk Score: `{format_score(l_score)}` ({l_cat})\n\n"
                        f"> *{l_text[:200]}{'...' if len(l_text) > 200 else ''}*\n\n---"
                    )

    safe_render_html("<div style='height: 14px;'></div>")

    # -------------------------------------------------------------
    # 5. CONTRACT SUMMARY (At the bottom)
    # -------------------------------------------------------------
    # Determine key risk areas (categories represented in medium or high clauses)
    risky_categories = list(dict.fromkeys([
        c.get("risk_category", "General") for c in sorted_clauses
        if c.get("risk_level", "").upper() in ["HIGH", "MEDIUM"]
    ]))
    if not risky_categories:
        risky_categories = ["No concentrated risk domains identified."]

    key_areas_str = " · ".join(risky_categories[:5])

    safe_render_html(
        f"""
        <div class="panel-secondary" style="margin-bottom: 30px; border-left: 3px solid #38BDF8;">
            <div class="label-caps" style="color: #38BDF8; margin-bottom: 10px;">CONTRACT SUMMARY</div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; font-size: 0.88rem;">
                <div>
                    <div style="color: #8E9CAE;">Overall Risk Rating:</div>
                    <div style="font-weight: 700; color: {get_risk_color(overall_level)}; font-size: 1rem; margin-top: 2px;">
                        {overall_level} ({format_score(overall_score)} / 100)
                    </div>
                </div>
                <div>
                    <div style="color: #8E9CAE;">Clause Breakdown:</div>
                    <div style="color: #F1F5F9; margin-top: 2px;">
                        {total_clauses} total ({high_cnt} High, {med_cnt} Medium, {low_cnt} Low)
                    </div>
                </div>
            </div>
            <div style="margin-top: 12px; padding-top: 10px; border-top: 1px solid #222B3D;">
                <span style="color: #8E9CAE; font-size: 0.82rem;">Key Risk Areas: </span>
                <strong style="color: #F8FAFC; font-size: 0.85rem;">{key_areas_str}</strong>
            </div>
        </div>
        """
    )

    # -------------------------------------------------------------
    # 6. FINAL ACTION: ANALYZE ANOTHER CONTRACT
    # -------------------------------------------------------------
    act_col1, act_col2, act_col3 = st.columns([1, 2, 1])
    with act_col2:
        if st.button("Analyze Another Contract", type="primary", width="stretch", key="btn_reset_workflow"):
            st.session_state["workflow_state"] = "EMPTY"
            st.session_state["current_analysis"] = None
            st.session_state["current_file_bytes"] = None
            st.session_state["current_filename"] = None
            st.session_state["current_file_hash"] = None
            st.session_state["error_message"] = None
            st.session_state["pending_analysis"] = False
            st.session_state["uploader_key"] = st.session_state.get("uploader_key", 0) + 1
            st.rerun()

    safe_render_html("<div style='height: 40px;'></div>")
