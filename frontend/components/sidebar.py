"""
Sidebar Navigation Component for ContractRisk AI — Premium Dark Legal-Tech Dashboard.
Implements minimal 2-item navigation: 'Analyze Contract' and 'Analysis History'.
"""

import streamlit as st
from frontend.utils.formatting import safe_render_html


def render_sidebar():
    """Render the simplified dark sidebar with only core contract review navigation."""
    with st.sidebar:
        # Sidebar Brand Header
        safe_render_html(
            """
            <div style="padding: 8px 4px 14px 4px; display: flex; align-items: center; gap: 10px;">
                <div style="width: 30px; height: 30px; background: #8B5CF6; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #FFFFFF; font-size: 1.1rem; font-weight: 800;">
                    ◈
                </div>
                <div>
                    <div style="font-size: 1.1rem; font-weight: 800; color: #F8FAFC; letter-spacing: -0.01em;">
                        ContractRisk <span style="color: #8B5CF6;">AI</span>
                    </div>
                    <div style="font-size: 0.70rem; color: #A1AFC2; font-weight: 500;">
                        Legal Risk Platform
                    </div>
                </div>
            </div>
            """
        )

        st.markdown("<hr style='border-color: #2D3A50; margin: 4px 0 16px 0;' />", unsafe_allow_html=True)

        # Simplified Navigation (Only 2 Core Actions)
        current_nav = st.session_state.get("nav_selection", "Analyze Contract")

        nav_items = [
            ("Analyze Contract", ":material/description:"),
            ("Analysis History", ":material/history:"),
        ]

        safe_render_html(
            """
            <div style="font-size: 0.68rem; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px; padding-left: 4px;">
                NAVIGATION
            </div>
            """
        )

        for label, icon in nav_items:
            is_active = (current_nav == label)
            btn_type = "primary" if is_active else "secondary"
            if st.button(
                label,
                icon=icon,
                key=f"nav_btn_{label.lower().replace(' ', '_')}",
                type=btn_type,
                width="stretch",
            ):
                st.session_state["nav_selection"] = label
                st.rerun()

        # Spacer to push card to bottom
        st.markdown("<div style='height: 240px;'></div>", unsafe_allow_html=True)

        # Compact Bottom Card
        safe_render_html(
            """
            <div class="sidebar-info-card">
                <div class="sidebar-info-title">
                    <span style="color: #8B5CF6;">◈</span> Contract Risk AI
                </div>
                <div class="sidebar-info-desc">
                    Identify high-risk clauses, unfavorable terms, and conflicting provisions in seconds.
                </div>
            </div>
            """
        )
