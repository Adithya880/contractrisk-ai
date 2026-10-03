"""
Clause Explorer Component for ContractRisk AI.
Provides two-panel investigative interface with compact clause index on the left
and detailed risk signals, LLM rationale, rules, and contractual text on the right.
"""

import streamlit as st
from frontend.utils.formatting import get_risk_badge_html, get_risk_color, format_score, safe_render_html


def render_clause_explorer(data: dict):
    """Render master-detail clause investigation workspace."""
    assessments = data.get("clause_assessments", [])

    if not assessments:
        st.info("No clause assessments available in the current contract.")
        return

    # Filter Controls Row
    filter_col, search_col = st.columns([1, 2])
    with filter_col:
        filter_level = st.selectbox(
            "Filter Risk",
            ["ALL", "HIGH", "MEDIUM", "LOW"],
            label_visibility="collapsed",
            key="clause_filter_select"
        )
    with search_col:
        search_query = st.text_input(
            "Search clauses",
            placeholder="Search clause title or section number...",
            label_visibility="collapsed",
            key="clause_search_input"
        )

    # Filter Clauses
    filtered = assessments
    if filter_level != "ALL":
        filtered = [a for a in filtered if a.get("risk_level", "").upper() == filter_level]
    if search_query.strip():
        q = search_query.strip().lower()
        filtered = [
            a for a in filtered
            if q in (a.get("clause_heading") or "").lower()
            or q in (a.get("clause_number") or "").lower()
            or q in (a.get("clause_text") or "").lower()
        ]

    if not filtered:
        st.warning(f"No clauses found matching filter criteria.")
        return

    # Two-Panel Layout: Left ~35%, Right ~65%
    col_left, col_right = st.columns([7, 13])

    with col_left:
        safe_render_html(
            f"""
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span class="label-caps">CLAUSE LIST</span>
                <span class="text-muted" style="font-size: 0.78rem;">{len(filtered)} clauses</span>
            </div>
            """
        )

        def make_clause_label(idx):
            a = filtered[idx]
            c_num = a.get("clause_number") or f"{idx+1:02d}"
            c_head = (a.get("clause_heading") or "General Terms").strip()
            if len(c_head) > 28:
                c_head = c_head[:26] + "..."
            c_lvl = a.get("risk_level", "LOW")
            c_sc = a.get("risk_score", 0.0)
            return f"{c_num:>2}  {c_head}  ·  {c_lvl} {c_sc:.1f}"

        selected_idx = st.radio(
            "Select Clause",
            range(len(filtered)),
            format_func=make_clause_label,
            label_visibility="collapsed",
            key="clause_list_radio"
        )

    selected = filtered[selected_idx]

    with col_right:
        c_num = selected.get("clause_number") or ""
        c_head = selected.get("clause_heading") or "Untitled Clause"
        c_score = selected.get("risk_score", 0.0)
        c_level = selected.get("risk_level", "LOW")
        c_text = selected.get("clause_text", "")
        c_cat = selected.get("risk_category", "General Terms")
        sb = selected.get("component_score_breakdown", {})
        explanation = selected.get("llm_explanation", "No risk explanation available.")
        rules = selected.get("rule_matches", [])

        # Header for Selected Clause
        safe_render_html(
            f"""
            <div class="panel-primary" style="margin-bottom: 14px;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div>
                        <div class="label-caps" style="color: #38BDF8;">CLAUSE {c_num}</div>
                        <h2 style="margin: 2px 0 4px 0; color: #F8FAFC;">{c_head}</h2>
                        <div class="text-muted" style="font-size: 0.82rem;">Category: {c_cat}</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 1.8rem; font-weight: 800; color: #F8FAFC; line-height: 1;">
                            {format_score(c_score)} <span style="font-size: 0.95rem; color: #5A677A;">/ 100</span>
                        </div>
                        <div style="margin-top: 6px;">
                            {get_risk_badge_html(c_level)}
                        </div>
                    </div>
                </div>
            </div>
            """
        )

        # 1. WHY THIS MATTERS (LLM Explanation)
        safe_render_html("<div class='label-caps' style='margin-bottom: 6px;'>WHY THIS MATTERS</div>")
        safe_render_html(
            f"""
            <div class="panel-secondary" style="margin-bottom: 14px; font-size: 0.9rem; line-height: 1.6; color: #E2E8F0;">
                {explanation}
            </div>
            """
        )

        # 2. RISK SIGNALS (Compact Signal Bars)
        safe_render_html("<div class='label-caps' style='margin-bottom: 6px;'>RISK SIGNALS</div>")
        c_bert = sb.get("bert_component", 0.0)
        c_rule = sb.get("rule_component", 0.0)
        c_rag = sb.get("rag_component", 0.0)
        c_llm = sb.get("llm_component", 0.0)

        safe_render_html(
            f"""
            <div class="panel-secondary" style="margin-bottom: 14px; padding: 12px 16px;">
                <!-- BERT Signal -->
                <div style="display: grid; grid-template-columns: 50px 1fr 50px; align-items: center; gap: 12px; margin-bottom: 8px;">
                    <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; color: #8E9CAE;">BERT</span>
                    <div style="background: #0A0E17; height: 6px; border-radius: 3px; overflow: hidden;">
                        <div style="background: #3B82F6; width: {min(c_bert, 100.0)}%; height: 100%; border-radius: 3px;"></div>
                    </div>
                    <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; text-align: right; color: #CBD5E1;">{c_bert:.2f}</span>
                </div>

                <!-- RULE Signal -->
                <div style="display: grid; grid-template-columns: 50px 1fr 50px; align-items: center; gap: 12px; margin-bottom: 8px;">
                    <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; color: #8E9CAE;">RULE</span>
                    <div style="background: #0A0E17; height: 6px; border-radius: 3px; overflow: hidden;">
                        <div style="background: #F59E0B; width: {min(c_rule, 100.0)}%; height: 100%; border-radius: 3px;"></div>
                    </div>
                    <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; text-align: right; color: #CBD5E1;">{c_rule:.2f}</span>
                </div>

                <!-- RAG Signal -->
                <div style="display: grid; grid-template-columns: 50px 1fr 50px; align-items: center; gap: 12px; margin-bottom: 8px;">
                    <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; color: #8E9CAE;">RAG</span>
                    <div style="background: #0A0E17; height: 6px; border-radius: 3px; overflow: hidden;">
                        <div style="background: #8B5CF6; width: {min(c_rag, 100.0)}%; height: 100%; border-radius: 3px;"></div>
                    </div>
                    <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; text-align: right; color: #CBD5E1;">{c_rag:.2f}</span>
                </div>

                <!-- LLM Signal -->
                <div style="display: grid; grid-template-columns: 50px 1fr 50px; align-items: center; gap: 12px;">
                    <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; color: #8E9CAE;">LLM</span>
                    <div style="background: #0A0E17; height: 6px; border-radius: 3px; overflow: hidden;">
                        <div style="background: #10B981; width: {min(c_llm, 100.0)}%; height: 100%; border-radius: 3px;"></div>
                    </div>
                    <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; text-align: right; color: #CBD5E1;">{c_llm:.2f}</span>
                </div>
            </div>
            """
        )

        # 3. DETECTED RULES
        safe_render_html("<div class='label-caps' style='margin-bottom: 6px;'>DETECTED RULES</div>")
        if rules:
            rule_html_list = []
            for r in rules:
                rid = r.get("rule_id", "RULE")
                desc = r.get("description", "")
                sev = r.get("severity_weight", 0.0)
                txt = r.get("matched_text", "")
                rule_html_list.append(
                    f"""
                    <div style="background: #151B26; border: 1px solid #222B3D; border-radius: 6px; padding: 10px 12px; margin-bottom: 8px; font-size: 0.85rem;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                            <strong style="color: #EF4444; font-family: 'JetBrains Mono', monospace;">{rid}</strong>
                            <span style="color: #8E9CAE; font-size: 0.75rem;">Weight: {sev:.1f}</span>
                        </div>
                        <div style="color: #CBD5E1; margin-bottom: 4px;">{desc}</div>
                        <div style="color: #8E9CAE; font-size: 0.8rem;">Matched: <code style="color: #F87171;">"{txt}"</code></div>
                    </div>
                    """
                )
            safe_render_html("".join(rule_html_list))
        else:
            safe_render_html(
                """
                <div class="panel-secondary" style="margin-bottom: 14px; font-size: 0.85rem; color: #10B981;">
                    ✓ No deterministic high-hazard rule patterns matched.
                </div>
                """
            )

        # 4. CONTRACTUAL TEXT
        safe_render_html("<div class='label-caps' style='margin-bottom: 6px;'>CONTRACTUAL TEXT</div>")
        safe_render_html(
            f"""
            <div class="contract-text-panel">
                {c_text}
            </div>
            """
        )
