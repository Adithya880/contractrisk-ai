"""
Rule Library Component for ContractRisk AI — Concept 1: Modern Professional Light Theme.
Displays the 39 deterministic heuristic rules across 13 legal risk domains.
"""

from typing import List, Dict, Any
import streamlit as st
from frontend.api_client import api_client
from frontend.utils.formatting import safe_render_html


def render_rule_library_view():
    """Render comprehensive Rule Library catalog with search and domain filtering."""
    safe_render_html(
        """
        <div style="margin-bottom: 20px;">
            <div style="font-size: 0.76rem; font-weight: 700; color: #6842F5; text-transform: uppercase; letter-spacing: 0.06em;">HEURISTIC KNOWLEDGE BASE</div>
            <h2 style="font-size: 1.4rem; font-weight: 800; color: #17182B; margin: 2px 0 4px 0;">Rule Library</h2>
            <div style="font-size: 0.85rem; color: #6B7280;">
                Deterministic legal heuristics detecting one-sided terms, liability contradictions, and compliance pitfalls.
            </div>
        </div>
        """
    )

    with st.spinner("Loading rule definitions..."):
        rules: List[Dict[str, Any]] = api_client.get_rules()

    if not rules:
        st.warning("No rules currently available.")
        return

    # Extract domains
    domains = sorted(list(set(r.get("risk_category", "General") for r in rules)))
    filter_domains = ["ALL"] + domains

    # Filter Bar
    col_domain, col_search = st.columns([1.5, 2.5])
    with col_domain:
        selected_domain = st.selectbox(
            "Filter Domain",
            filter_domains,
            key="rule_lib_domain_sel",
            label_visibility="collapsed"
        )
    with col_search:
        search_kw = st.text_input(
            "Search Rules",
            placeholder="Search by rule ID, description, or keyword...",
            key="rule_lib_search_kw",
            label_visibility="collapsed"
        )

    # Filter rules
    filtered_rules = rules
    if selected_domain != "ALL":
        filtered_rules = [r for r in filtered_rules if r.get("risk_category") == selected_domain]

    if search_kw.strip():
        kw = search_kw.strip().lower()
        filtered_rules = [
            r for r in filtered_rules
            if kw in r.get("rule_id", "").lower()
            or kw in r.get("description", "").lower()
            or kw in r.get("risk_category", "").lower()
        ]

    st.caption(f"Displaying {len(filtered_rules)} of {len(rules)} compiled rules")

    # Render Rule Cards in a 2-column responsive layout
    r_col1, r_col2 = st.columns(2)

    for idx, r in enumerate(filtered_rules):
        target_col = r_col1 if idx % 2 == 0 else r_col2
        r_id = r.get("rule_id", "RULE")
        cat = r.get("risk_category", "General")
        desc = r.get("description", "")
        sev = float(r.get("severity_weight", 0.0))

        # Color-code by severity
        if sev >= 75.0:
            border_color = "#EF4444"
            sev_badge_bg = "#FEF2F2"
            sev_badge_text = "#DC2626"
            sev_border = "#FECACA"
        elif sev >= 50.0:
            border_color = "#F59E0B"
            sev_badge_bg = "#FFFBEB"
            sev_badge_text = "#D97706"
            sev_border = "#FDE68A"
        else:
            border_color = "#3B82F6"
            sev_badge_bg = "#EFF6FF"
            sev_badge_text = "#2563EB"
            sev_border = "#BFDBFE"

        with target_col:
            safe_render_html(
                f"""
                <div style="background: #FFFFFF; border: 1px solid #E5E7EB; border-left: 4px solid {border_color}; border-radius: 10px; padding: 14px 16px; margin-bottom: 12px; box-shadow: 0 1px 2px rgba(0,0,0,0.02); height: calc(100% - 12px); display: flex; flex-direction: column; justify-content: space-between;">
                    <div>
                        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px;">
                            <strong style="color: #17182B; font-size: 0.90rem; font-family: 'JetBrains Mono', monospace;">
                                {r_id}
                            </strong>
                            <span style="background: {sev_badge_bg}; color: {sev_badge_text}; border: 1px solid {sev_border}; font-size: 0.70rem; font-weight: 700; padding: 2px 8px; border-radius: 9999px;">
                                Weight: {sev:.0f}
                            </span>
                        </div>
                        <div style="font-size: 0.82rem; color: #4B5563; line-height: 1.45; margin-bottom: 8px;">
                            {desc}
                        </div>
                    </div>
                    <div style="display: flex; align-items: center; justify-content: space-between; font-size: 0.74rem; color: #6B7280; border-top: 1px solid #F3F4F6; padding-top: 6px; margin-top: 4px;">
                        <span>Category: <strong style="color: #6842F5;">{cat}</strong></span>
                        <span>Deterministic Regex</span>
                    </div>
                </div>
                """
            )

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

