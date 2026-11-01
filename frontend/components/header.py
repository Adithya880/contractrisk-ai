"""
Top Header Component for ContractRisk AI — Premium Dark Legal-Tech Dashboard.
Renders compact brand mark, application name, subtitle, and functional Help dialog.
"""

import streamlit as st
from frontend.utils.formatting import safe_render_html


def render_top_header():
    """Render the compact top header."""
    col_brand, col_help = st.columns([8.5, 1.5])

    with col_brand:
        safe_render_html(
            """
            <div style="display: flex; align-items: center; gap: 10px; padding: 2px 0;">
                <div style="width: 32px; height: 32px; background: #8B5CF6; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #FFFFFF; font-size: 1.2rem; font-weight: 800; box-shadow: 0 2px 8px rgba(139, 92, 246, 0.3);">
                    ◈
                </div>
                <div>
                    <div style="font-size: 1.15rem; font-weight: 800; color: #F8FAFC; letter-spacing: -0.015em; line-height: 1.2;">
                        ContractRisk <span style="color: #8B5CF6;">AI</span>
                    </div>
                    <div style="font-size: 0.76rem; color: #A1AFC2; font-weight: 500;">
                        Contract Risk Analysis
                    </div>
                </div>
            </div>
            """
        )

    with col_help:
        if st.button("Help", icon=":material/help:", key="hdr_help_btn", width="stretch"):
            st.session_state["show_help_dialog"] = True

    # Render Help dialog if triggered
    if st.session_state.get("show_help_dialog", False):
        @st.dialog("ContractRisk AI — User Guide")
        def show_help():
            st.markdown(
                """
                ### About ContractRisk AI
                ContractRisk AI helps you understand contractual risks, unfavorable terms, and potential legal exposure.
                
                #### How to Use:
                1. **Upload Contract**: Upload any PDF or DOCX agreement (up to 20 MB).
                2. **Review Overall Risk**: View the overall contract risk score (/100) and risk level breakdown.
                3. **Examine Risk Alerts**: Review critical inconsistencies or conflicting provisions detected across clauses.
                4. **Clause-by-Clause Inspection**: Select individual clauses to read why they are risky and see specific unfavorable terms.
                5. **Future Scenarios**: See potential real-world dispute projections generated when local AI is active.
                
                *Disclaimer: ContractRisk AI is an automated decision-support tool and does not constitute formal legal advice.*
                """
            )
            if st.button("Close", key="close_help_dlg", type="primary"):
                st.session_state["show_help_dialog"] = False
                st.rerun()

        show_help()

    # Subtle separator line
    st.markdown("<hr style='border: none; border-top: 1px solid #2D3A50; margin: 8px 0 16px 0;'/>", unsafe_allow_html=True)
