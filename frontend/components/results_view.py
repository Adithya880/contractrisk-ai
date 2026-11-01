"""
Results Screen Component for ContractRisk AI — Premium Dark Legal-Tech Dashboard.
Provides a simplified, user-focused contract risk assessment:
1. Overall Risk Summary (Score / 100 with non-overlapping gauge, risk level, and 4 compact KPI cards).
2. Contractual Risk Alerts (compact, one-sentence warnings shown only when genuine conflicts exist).
3. Clause-by-Clause Analysis (Clause cards on left; Original Clause + Plain-English Risk Analysis on right).
4. Future Scenario Prediction (Qwen3 real-world dispute projections with purple accent).
"""

import json
from typing import Dict, Any, List
import streamlit as st
from frontend.utils.formatting import (
    safe_render_html,
    get_risk_badge_html,
    get_circular_score_svg,
    format_score,
    get_risk_color
)


def _get_plain_english_risk_analysis(clause: dict) -> dict:
    """Extract plain-English, user-friendly risk analysis without technical jargon."""
    c_level = (clause.get("risk_level") or "NORMAL").upper()
    c_score = float(clause.get("risk_score", 0.0))
    heading = clause.get("clause_heading") or "General Provision"
    category = clause.get("risk_category") or clause.get("bert_label") or heading
    rules = clause.get("rule_matches") or clause.get("detected_rules") or []
    llm_expl = clause.get("llm_explanation") or clause.get("risk_explanation")
    intra = clause.get("intra_clause_contradictions") or []

    # 1. Main Risk Identified
    if intra:
        ci = intra[0] if isinstance(intra[0], dict) else getattr(intra[0], "__dict__", {})
        main_risk = f"Contradictory terms within this clause: {ci.get('explanation', 'Conflicting obligations detected.')}"
    elif rules:
        first_r = rules[0] if isinstance(rules[0], dict) else getattr(rules[0], "__dict__", {})
        main_risk = first_r.get("description", f"Unfavorable {category.lower()} condition detected.")
    elif c_level == "HIGH":
        main_risk = f"High-exposure {category.lower()} provision with significant one-sided legal burden."
    elif c_level == "MEDIUM":
        main_risk = f"Moderate {category.lower()} risk that warrants legal clarification."
    elif c_level == "LOW":
        main_risk = f"Minor {category.lower()} asymmetry with limited contractual exposure."
    else:
        main_risk = "Standard contractual clause with no significant risk indicators detected."

    # 2. Why It Is Risky
    if llm_expl and not clause.get("llm_inference_status") in ["FAILED", "UNAVAILABLE"]:
        why_risky = llm_expl
    elif intra:
        why_risky = (
            "The clause pairs contradictory stipulations (such as unlimited liability alongside damage waivers, "
            "or mutual notice paired with immediate unilateral stoppage), creating legal ambiguity that can be "
            "weaponized in a dispute."
        )
    elif rules:
        rule_descs = [
            (r.get("description") if isinstance(r, dict) else getattr(r, "description", ""))
            for r in rules
            if (r.get("description") if isinstance(r, dict) else getattr(r, "description", ""))
        ]
        why_risky = " · ".join(rule_descs) if rule_descs else f"Provisions under this {category.lower()} term favor one party disproportionately."
    elif c_level in ["HIGH", "MEDIUM"]:
        why_risky = f"The wording of this {category.lower()} provision deviates from balanced commercial standards, potentially placing unhedged liabilities on the signer."
    else:
        why_risky = "The language appears reciprocal, standard, and consistent with conventional market practices."

    # 3. Potential Impact on the Party
    cat_lower = (category or "").lower()
    head_lower = (heading or "").lower()

    if "liability" in cat_lower or "liab" in head_lower or c_score >= 80:
        potential_impact = "Financial exposure with no monetary ceiling, enabling the counterparty to pursue uncapped damages in the event of a breach or claim."
    elif "termination" in cat_lower or "term" in head_lower:
        potential_impact = "Operational disruption due to sudden cancellation without adequate advance notice or an opportunity to cure defaults."
    elif "indemn" in cat_lower or "indemn" in head_lower:
        potential_impact = "Significant legal and financial obligation to defend and hold harmless the other party from third-party disputes."
    elif "confidential" in cat_lower or "ip" in cat_lower or "intellectual" in head_lower:
        potential_impact = "Possible forfeiture or perpetual restriction on proprietary intellectual property, trade secrets, or work product."
    elif "payment" in cat_lower or "fee" in head_lower or "price" in head_lower:
        potential_impact = "Risk of unexpected price alterations, unilateral fee adjustments, or harsh penalty fees for minor payment delays."
    elif c_level == "NORMAL":
        potential_impact = "Minimal exposure. Standard operational terms with balanced rights and remedies for both parties."
    else:
        potential_impact = "Could create one-sided contractual leverage for the counterparty during a dispute or contract renegotiation."

    # 4. Important Unfavorable Terms
    unfavorable_terms = []
    for r in rules:
        matched = (r.get("matched_text") if isinstance(r, dict) else getattr(r, "matched_text", "")) or ""
        if matched.strip():
            unfavorable_terms.append(f'"{matched.strip()}"')

    if intra:
        for ci in intra:
            ci_d = ci if isinstance(ci, dict) else getattr(ci, "__dict__", {})
            sa = ci_d.get("conflicting_excerpt_a", "")
            sb = ci_d.get("conflicting_excerpt_b", "")
            if sa:
                unfavorable_terms.append(f'"{sa}"')
            if sb:
                unfavorable_terms.append(f'"{sb}"')

    unfavorable_str = ", ".join(list(dict.fromkeys(unfavorable_terms))) if unfavorable_terms else None

    return {
        "main_risk": main_risk,
        "why_risky": why_risky,
        "potential_impact": potential_impact,
        "unfavorable_terms": unfavorable_str
    }


def render_results_view(data: dict):
    """Render the simplified dark contract risk dashboard."""
    doc_meta = data.get("document", {})
    summary = data.get("contract_summary", {})
    assessments = data.get("clause_assessments", [])
    conflicts = data.get("cross_clause_conflicts", [])
    intra_conflicts = data.get("intra_clause_contradictions") or summary.get("intra_clause_contradictions", [])
    combined_scenario = data.get("combined_scenario") or summary.get("combined_scenario")

    filename = doc_meta.get("filename", "Contract Document")
    overall_score = float(summary.get("risk_score", 0.0))
    overall_level = (summary.get("risk_level") or "NORMAL").upper()
    total_clauses = len(assessments)

    # Actual counts returned by backend
    norm_count = summary.get("normal_risk_clause_count")
    if norm_count is None:
        norm_count = sum(1 for c in assessments if (c.get("risk_level") or "").upper() == "NORMAL")

    low_count = summary.get("low_risk_clause_count")
    if low_count is None:
        low_count = sum(1 for c in assessments if (c.get("risk_level") or "").upper() == "LOW")

    med_count = summary.get("medium_risk_clause_count")
    if med_count is None:
        med_count = sum(1 for c in assessments if (c.get("risk_level") or "").upper() == "MEDIUM")

    high_count = summary.get("high_risk_clause_count")
    if high_count is None:
        high_count = sum(1 for c in assessments if (c.get("risk_level") or "").upper() == "HIGH")

    # -------------------------------------------------------------
    # 1. TOP BAR: DOCUMENT & ACTIONS
    # -------------------------------------------------------------
    hdr_c1, hdr_c2 = st.columns([7, 3])
    with hdr_c1:
        safe_render_html(
            f"""
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px;">
                <span style="font-size: 1.4rem;">📄</span>
                <div>
                    <h2 style="margin: 0; font-size: 1.25rem; font-weight: 800; color: #F8FAFC; line-height: 1.2;">
                        {filename}
                    </h2>
                    <div style="font-size: 0.80rem; color: #A1AFC2; margin-top: 2px;">
                        {total_clauses} clauses analyzed
                    </div>
                </div>
            </div>
            """
        )
    with hdr_c2:
        btn_act1, btn_act2 = st.columns(2)
        with btn_act1:
            report_data = {
                "document": doc_meta,
                "contract_summary": summary,
                "clause_assessments": assessments,
                "conflicts": conflicts,
                "intra_clause_contradictions": intra_conflicts,
            }
            clean_name = filename.rsplit(".", 1)[0] if "." in filename else filename
            st.download_button(
                label="Download",
                data=json.dumps(report_data, indent=2, default=str),
                file_name=f"{clean_name}_risk_analysis.json",
                mime="application/json",
                icon=":material/download:",
                width="stretch",
                key="btn_download_summary"
            )
        with btn_act2:
            if st.button("New Analysis", icon=":material/add:", type="primary", width="stretch", key="btn_new_run"):
                st.session_state["workflow_state"] = "EMPTY"
                st.session_state["current_analysis"] = None
                st.session_state["current_file_bytes"] = None
                st.session_state["current_filename"] = None
                st.session_state["current_file_hash"] = None
                st.session_state["error_message"] = None
                st.session_state["pending_analysis"] = False
                st.session_state["selected_clause_idx"] = 0
                st.session_state["uploader_key"] = st.session_state.get("uploader_key", 0) + 1
                st.rerun()

    # -------------------------------------------------------------
    # 2. OVERALL RISK SUMMARY & 4 COMPACT CARDS
    # -------------------------------------------------------------
    gauge_col, kpi1, kpi2, kpi3, kpi4 = st.columns([2.6, 1.85, 1.85, 1.85, 1.85], gap="small")

    with gauge_col:
        safe_render_html(
            f"""
            <div style="background: #182235; border: 1px solid #2D3A50; border-radius: 10px; padding: 14px 12px; text-align: center; height: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center;">
                <div style="font-size: 0.72rem; font-weight: 700; color: #A1AFC2; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 2px;">
                    OVERALL CONTRACT RISK
                </div>
                {get_circular_score_svg(overall_score, overall_level, size=110)}
                <div style="margin-top: 6px;">
                    {get_risk_badge_html(overall_level)}
                </div>
            </div>
            """
        )

    with kpi1:
        safe_render_html(
            f"""
            <div style="background: #182235; border: 1px solid #2D3A50; border-top: 3px solid #10B981; border-radius: 10px; padding: 14px 12px; text-align: center; height: 100%; display: flex; flex-direction: column; justify-content: center;">
                <div style="font-size: 0.70rem; font-weight: 700; color: #A1AFC2; text-transform: uppercase;">NORMAL</div>
                <div style="font-size: 1.8rem; font-weight: 800; color: #10B981; margin: 6px 0 2px 0; line-height: 1;">{norm_count}</div>
                <div style="font-size: 0.72rem; color: #64748B;">Standard terms</div>
            </div>
            """
        )

    with kpi2:
        safe_render_html(
            f"""
            <div style="background: #182235; border: 1px solid #2D3A50; border-top: 3px solid #3B82F6; border-radius: 10px; padding: 14px 12px; text-align: center; height: 100%; display: flex; flex-direction: column; justify-content: center;">
                <div style="font-size: 0.70rem; font-weight: 700; color: #A1AFC2; text-transform: uppercase;">LOW RISK</div>
                <div style="font-size: 1.8rem; font-weight: 800; color: #3B82F6; margin: 6px 0 2px 0; line-height: 1;">{low_count}</div>
                <div style="font-size: 0.72rem; color: #64748B;">Minor exposure</div>
            </div>
            """
        )

    with kpi3:
        safe_render_html(
            f"""
            <div style="background: #182235; border: 1px solid #2D3A50; border-top: 3px solid #F59E0B; border-radius: 10px; padding: 14px 12px; text-align: center; height: 100%; display: flex; flex-direction: column; justify-content: center;">
                <div style="font-size: 0.70rem; font-weight: 700; color: #A1AFC2; text-transform: uppercase;">MEDIUM RISK</div>
                <div style="font-size: 1.8rem; font-weight: 800; color: #F59E0B; margin: 6px 0 2px 0; line-height: 1;">{med_count}</div>
                <div style="font-size: 0.72rem; color: #64748B;">Review needed</div>
            </div>
            """
        )

    with kpi4:
        safe_render_html(
            f"""
            <div style="background: #182235; border: 1px solid #2D3A50; border-top: 3px solid #EF4444; border-radius: 10px; padding: 14px 12px; text-align: center; height: 100%; display: flex; flex-direction: column; justify-content: center;">
                <div style="font-size: 0.70rem; font-weight: 700; color: #A1AFC2; text-transform: uppercase;">HIGH RISK</div>
                <div style="font-size: 1.8rem; font-weight: 800; color: #EF4444; margin: 6px 0 2px 0; line-height: 1;">{high_count}</div>
                <div style="font-size: 0.72rem; color: #64748B;">Critical terms</div>
            </div>
            """
        )

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # -------------------------------------------------------------
    # 3. CONTRACTUAL RISK ALERTS (Shown ONLY when actual conflicts exist)
    # -------------------------------------------------------------
    total_conflicts = len(conflicts) + len(intra_conflicts)
    if total_conflicts > 0:
        safe_render_html(
            f"""
            <div style="background: #182235; border: 1px solid #2D3A50; border-left: 4px solid #F59E0B; border-radius: 8px; padding: 12px 16px; margin-bottom: 12px;">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="font-size: 1.1rem; color: #F59E0B;">⚠️</span>
                        <strong style="color: #F8FAFC; font-size: 0.90rem;">Contractual Risk Alerts ({total_conflicts})</strong>
                    </div>
                    <span style="font-size: 0.72rem; color: #A1AFC2;">Inconsistencies detected</span>
                </div>
            </div>
            """
        )

        for cf in conflicts:
            cf_d = cf if isinstance(cf, dict) else getattr(cf, "__dict__", {})
            c_type = cf_d.get("conflict_type", "Cross-Clause Conflict")
            c_nums = ", ".join(cf_d.get("clause_numbers", []))
            c_expl = cf_d.get("explanation", "")
            safe_render_html(
                f"""
                <div style="background: #202D42; border: 1px solid #2D3A50; border-left: 3px solid #EF4444; border-radius: 6px; padding: 10px 14px; margin-bottom: 8px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;">
                        <strong style="color: #F8FAFC; font-size: 0.86rem;">{c_type}</strong>
                        <span style="color: #EF4444; font-size: 0.74rem; font-weight: 700;">Clauses: {c_nums}</span>
                    </div>
                    <div style="color: #A1AFC2; font-size: 0.80rem; line-height: 1.4;">{c_expl}</div>
                </div>
                """
            )

        for ic in intra_conflicts:
            ic_d = ic if isinstance(ic, dict) else getattr(ic, "__dict__", {})
            c_type = ic_d.get("conflict_type", "Internal Contradiction")
            c_nums = ", ".join(ic_d.get("clause_numbers", []))
            c_expl = ic_d.get("explanation", "")
            safe_render_html(
                f"""
                <div style="background: #202D42; border: 1px solid #2D3A50; border-left: 3px solid #F59E0B; border-radius: 6px; padding: 10px 14px; margin-bottom: 8px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;">
                        <strong style="color: #F8FAFC; font-size: 0.86rem;">{c_type}</strong>
                        <span style="color: #F59E0B; font-size: 0.74rem; font-weight: 700;">Within: Clause {c_nums}</span>
                    </div>
                    <div style="color: #A1AFC2; font-size: 0.80rem; line-height: 1.4;">{c_expl}</div>
                </div>
                """
            )

    # -------------------------------------------------------------
    # 4. FUTURE SCENARIO PREDICTION (Prominently Included)
    # -------------------------------------------------------------
    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
    safe_render_html(
        """
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
            <span style="font-size: 1.1rem; color: #8B5CF6;">🔮</span>
            <h3 style="margin: 0; font-size: 1.05rem; font-weight: 700; color: #F8FAFC;">Future Scenario Prediction</h3>
        </div>
        """
    )

    has_real_scenario = False
    if combined_scenario:
        sc_d = combined_scenario if isinstance(combined_scenario, dict) else getattr(combined_scenario, "__dict__", {})
        what_could_happen = sc_d.get("scenario_description")
        possible_consequence = sc_d.get("possible_consequence")
        is_fallback = sc_d.get("fallback_active", False)

        if what_could_happen and not is_fallback:
            has_real_scenario = True
            sc_title = sc_d.get("scenario_title", "Potential Commercial Dispute")
            rel_clause = sc_d.get("clause_number", "Key Elevated Risk Provisions")

            safe_render_html(
                f"""
                <div style="background: #182235; border: 1px solid #8B5CF6; border-left: 4px solid #8B5CF6; border-radius: 8px; padding: 14px 18px; margin-bottom: 14px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <strong style="color: #F8FAFC; font-size: 0.90rem;">{sc_title}</strong>
                        <span style="background: rgba(139, 92, 246, 0.15); color: #8B5CF6; border: 1px solid rgba(139, 92, 246, 0.3); font-size: 0.70rem; font-weight: 700; padding: 2px 8px; border-radius: 9999px;">
                            Relevant: {rel_clause}
                        </span>
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 8px;">
                        <div style="background: #202D42; border: 1px solid #2D3A50; border-radius: 6px; padding: 10px 12px;">
                            <div style="font-size: 0.70rem; font-weight: 700; color: #8B5CF6; text-transform: uppercase; margin-bottom: 2px;">WHAT COULD HAPPEN</div>
                            <div style="font-size: 0.82rem; color: #F8FAFC; line-height: 1.45;">{what_could_happen}</div>
                        </div>
                        <div style="background: #202D42; border: 1px solid #2D3A50; border-radius: 6px; padding: 10px 12px;">
                            <div style="font-size: 0.70rem; font-weight: 700; color: #EF4444; text-transform: uppercase; margin-bottom: 2px;">POSSIBLE CONSEQUENCE</div>
                            <div style="font-size: 0.82rem; color: #F8FAFC; line-height: 1.45;">{possible_consequence}</div>
                        </div>
                    </div>
                    <div style="font-size: 0.70rem; color: #64748B; margin-top: 8px; text-align: right;">
                        *Hypothetical risk projection based on contract terms; not a guaranteed legal outcome.
                    </div>
                </div>
                """
            )

    if not has_real_scenario:
        safe_render_html(
            """
            <div style="background: #182235; border: 1px solid #2D3A50; border-radius: 8px; padding: 12px 16px; margin-bottom: 14px; color: #A1AFC2; font-size: 0.80rem;">
                No future scenarios were generated for this contract. Scenarios represent hypothetical risk projections generated when local AI is active.
            </div>
            """
        )

    # -------------------------------------------------------------
    # 5. CLAUSE-BY-CLAUSE ANALYSIS (Core Section)
    # -------------------------------------------------------------
    st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
    safe_render_html(
        """
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;">
            <h3 style="margin: 0; font-size: 1.15rem; font-weight: 700; color: #F8FAFC;">
                Clause-by-Clause Analysis
            </h3>
            <span style="font-size: 0.78rem; color: #A1AFC2;">
                Select a clause to review its specific risks
            </span>
        </div>
        """
    )

    if not assessments:
        st.info("No clauses detected in this document.")
        return

    # Track selected clause index
    if "selected_clause_idx" not in st.session_state:
        st.session_state["selected_clause_idx"] = 0

    col_list, col_detail = st.columns([3.8, 6.2], gap="medium")

    # LEFT PANEL: CLAUSE CARDS LIST
    with col_list:
        with st.container(height=560):
            for idx, c in enumerate(assessments):
                c_num = c.get("clause_number") or str(idx + 1)
                heading = c.get("clause_heading") or f"Clause {c_num}"
                c_level = (c.get("risk_level") or "NORMAL").upper()
                c_score = float(c.get("risk_score", 0.0))
                is_selected = (st.session_state["selected_clause_idx"] == idx)

                # Card Styling
                border_color = "#8B5CF6" if is_selected else "#2D3A50"
                bg_color = "#202D42" if is_selected else "#182235"
                badge = get_risk_badge_html(c_level)

                safe_render_html(
                    f"""
                    <div style="background: {bg_color}; border: 1px solid {border_color}; border-radius: 8px; padding: 10px 12px; margin-bottom: 6px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;">
                            <span style="font-size: 0.74rem; font-weight: 700; color: #A1AFC2;">Clause {c_num}</span>
                            <div style="display: flex; align-items: center; gap: 6px;">
                                <span style="font-size: 0.78rem; font-weight: 700; color: {get_risk_color(c_level)};">{format_score(c_score)}</span>
                                {badge}
                            </div>
                        </div>
                        <div style="font-size: 0.86rem; font-weight: 600; color: #F8FAFC; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                            {heading}
                        </div>
                    </div>
                    """
                )

                btn_text = f"✓ Viewing Clause {c_num}" if is_selected else f"View Clause {c_num}"
                if st.button(btn_text, key=f"btn_pick_clause_{idx}", width="stretch", type="primary" if is_selected else "secondary"):
                    st.session_state["selected_clause_idx"] = idx
                    st.rerun()

    # RIGHT PANEL: SELECTED CLAUSE DETAILS
    with col_detail:
        sel_idx = st.session_state.get("selected_clause_idx", 0)
        if sel_idx >= len(assessments):
            sel_idx = 0
            st.session_state["selected_clause_idx"] = 0

        clause = assessments[sel_idx]
        c_num = clause.get("clause_number") or str(sel_idx + 1)
        heading = clause.get("clause_heading") or f"Clause {c_num}"
        c_text = clause.get("clause_text", "")
        c_score = float(clause.get("risk_score", 0.0))
        c_level = (clause.get("risk_level") or "NORMAL").upper()

        risk_analysis = _get_plain_english_risk_analysis(clause)

        # Selected Clause Header
        safe_render_html(
            f"""
            <div style="background: #182235; border: 1px solid #2D3A50; border-radius: 10px; padding: 14px 18px; margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-size: 1.05rem; font-weight: 800; color: #F8FAFC;">
                            Clause {c_num}: {heading}
                        </div>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="font-size: 1.1rem; font-weight: 800; color: {get_risk_color(c_level)};">
                            {format_score(c_score)} <span style="font-size: 0.70rem; color: #A1AFC2;">/ 100</span>
                        </span>
                        {get_risk_badge_html(c_level)}
                    </div>
                </div>
            </div>
            """
        )

        # A. ORIGINAL CLAUSE
        safe_render_html(
            f"""
            <div style="background: #182235; border: 1px solid #2D3A50; border-radius: 8px; padding: 14px 16px; margin-bottom: 12px;">
                <div style="font-size: 0.72rem; font-weight: 700; color: #8B5CF6; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px;">
                    ORIGINAL CLAUSE TEXT
                </div>
                <div style="font-family: 'Inter', sans-serif; font-size: 0.86rem; line-height: 1.6; color: #F8FAFC; background: #202D42; border: 1px solid #2D3A50; border-radius: 6px; padding: 12px 14px; white-space: pre-wrap; max-height: 160px; overflow-y: auto;">
{c_text}
                </div>
            </div>
            """
        )

        # B. RISK ANALYSIS (No BERT confidence, No rule IDs, No technical jargon)
        unfavorable_block = ""
        if risk_analysis["unfavorable_terms"]:
            unfavorable_block = f"""
            <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #2D3A50;">
                <div style="font-size: 0.70rem; font-weight: 700; color: #EF4444; text-transform: uppercase; margin-bottom: 4px;">
                    IMPORTANT UNFAVORABLE TERMS
                </div>
                <div style="background: #202D42; border: 1px solid #2D3A50; border-radius: 6px; padding: 8px 10px; font-family: monospace; font-size: 0.78rem; color: #F8FAFC; line-height: 1.4;">
                    {risk_analysis["unfavorable_terms"]}
                </div>
            </div>
            """
        else:
            unfavorable_block = """
            <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #2D3A50;">
                <div style="font-size: 0.70rem; font-weight: 700; color: #A1AFC2; text-transform: uppercase; margin-bottom: 2px;">
                    IMPORTANT UNFAVORABLE TERMS
                </div>
                <div style="font-size: 0.80rem; color: #64748B;">
                    No specific unfavorable or one-sided phrasing detected in this clause.
                </div>
            </div>
            """

        safe_render_html(
            f"""
            <div style="background: #182235; border: 1px solid #2D3A50; border-radius: 8px; padding: 14px 16px;">
                <div style="font-size: 0.72rem; font-weight: 700; color: #8B5CF6; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 10px;">
                    RISK ANALYSIS
                </div>
                
                <!-- Main Risk Identified -->
                <div style="margin-bottom: 10px;">
                    <div style="font-size: 0.70rem; font-weight: 700; color: #A1AFC2; text-transform: uppercase; margin-bottom: 2px;">
                        MAIN RISK IDENTIFIED
                    </div>
                    <div style="font-size: 0.84rem; font-weight: 600; color: #F8FAFC;">
                        {risk_analysis["main_risk"]}
                    </div>
                </div>

                <!-- Why It Is Risky -->
                <div style="margin-bottom: 10px;">
                    <div style="font-size: 0.70rem; font-weight: 700; color: #A1AFC2; text-transform: uppercase; margin-bottom: 2px;">
                        WHY IT IS RISKY
                    </div>
                    <div style="font-size: 0.82rem; color: #F8FAFC; line-height: 1.5;">
                        {risk_analysis["why_risky"]}
                    </div>
                </div>

                <!-- Potential Impact -->
                <div>
                    <div style="font-size: 0.70rem; font-weight: 700; color: #A1AFC2; text-transform: uppercase; margin-bottom: 2px;">
                        POTENTIAL IMPACT ON PARTY
                    </div>
                    <div style="font-size: 0.82rem; color: #A1AFC2; line-height: 1.5;">
                        {risk_analysis["potential_impact"]}
                    </div>
                </div>

                <!-- Unfavorable Terms -->
                {unfavorable_block}
            </div>
            """
        )

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
