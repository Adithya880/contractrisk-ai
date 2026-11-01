"""
Analysis and Progress Screen for ContractRisk AI — Premium Dark Legal-Tech Dashboard.
Displays focused pipeline progress reflecting the 8 real pipeline stages during analysis.
"""

import time
import textwrap
import concurrent.futures
import streamlit as st
from frontend.api_client import api_client, APIClientError
from frontend.utils.formatting import safe_render_html, normalize_analysis_data

PIPELINE_STAGES = [
    "Extracting document text",
    "Segmenting contract clauses",
    "Classifying clause types",
    "Scanning for risk indicators",
    "Retrieving precedent benchmarks",
    "Generating risk explanations",
    "Predicting future dispute scenarios",
    "Finalizing contract risk profile",
]


def render_progress_view():
    """Render analysis progress screen in dark legal-tech style."""
    file_bytes = st.session_state.get("current_file_bytes")
    filename = st.session_state.get("current_filename", "Contract Document")

    if not file_bytes:
        st.session_state["workflow_state"] = "EMPTY"
        st.rerun()
        return

    # If current_analysis is already populated, route to COMPLETE
    if st.session_state.get("current_analysis") is not None:
        st.session_state["workflow_state"] = "COMPLETE"
        st.rerun()
        return

    # Single-run execution guard
    st.session_state["pending_analysis"] = False

    # Container for the progress card
    progress_card = st.empty()

    def build_screen_html(active_idx: int, pct: int, is_complete: bool = False) -> str:
        stage_rows = []
        for idx, stage_name in enumerate(PIPELINE_STAGES):
            if is_complete or idx < active_idx:
                status_icon = '<span style="color: #10B981; font-weight: 700; margin-right: 10px; font-size: 0.95rem;">✓</span>'
                status_label = '<span style="background: rgba(16, 185, 129, 0.12); color: #10B981; border: 1px solid rgba(16, 185, 129, 0.3); font-size: 0.70rem; font-weight: 700; padding: 2px 8px; border-radius: 9999px;">DONE</span>'
                row_bg = "background: #111827; border: 1px solid #2D3A50;"
                text_color = "#F8FAFC"
            elif idx == active_idx and not is_complete:
                status_icon = '<span style="color: #8B5CF6; font-weight: 700; margin-right: 10px; font-size: 0.95rem;">●</span>'
                status_label = '<span style="background: rgba(139, 92, 246, 0.15); color: #8B5CF6; border: 1px solid rgba(139, 92, 246, 0.3); font-size: 0.70rem; font-weight: 700; padding: 2px 8px; border-radius: 9999px;">RUNNING</span>'
                row_bg = "background: #202D42; border: 1px solid #8B5CF6;"
                text_color = "#FFFFFF; font-weight: 600;"
            else:
                status_icon = '<span style="color: #4B5563; font-weight: 700; margin-right: 10px; font-size: 0.95rem;">○</span>'
                status_label = '<span style="color: #64748B; font-size: 0.70rem;">PENDING</span>'
                row_bg = "background: transparent; border: 1px solid transparent;"
                text_color = "#64748B"

            stage_rows.append(
                f"""
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 7px 12px; margin-bottom: 4px; border-radius: 6px; {row_bg}">
                    <div style="display: flex; align-items: center;">
                        {status_icon}
                        <span style="font-size: 0.84rem; color: {text_color};">{stage_name}</span>
                    </div>
                    {status_label}
                </div>
                """
            )

        stages_content = "".join(stage_rows)

        html_raw = f"""
        <div style="max-width: 620px; margin: 2rem auto; padding: 0 1rem;">
            <!-- Header -->
            <div style="text-align: center; margin-bottom: 16px;">
                <div style="width: 38px; height: 38px; background: #182235; border: 1px solid #2D3A50; border-radius: 10px; display: inline-flex; align-items: center; justify-content: center; color: #8B5CF6; font-size: 1.3rem; font-weight: 800; box-shadow: 0 4px 10px rgba(139, 92, 246, 0.2); margin-bottom: 6px;">
                    ◈
                </div>
                <h2 style="font-size: 1.35rem; font-weight: 800; color: #F8FAFC; letter-spacing: -0.015em; margin: 0 0 3px 0;">
                    Analyzing Contract
                </h2>
                <div style="font-size: 0.86rem; color: #A1AFC2;">
                    Document: <strong style="color: #F8FAFC;">{filename}</strong>
                </div>
            </div>

            <!-- Progress Card -->
            <div style="background: #182235; border: 1px solid #2D3A50; border-radius: 12px; padding: 20px 22px; box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);">
                <!-- Progress Bar Header -->
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="font-size: 0.74rem; font-weight: 700; color: #8B5CF6; text-transform: uppercase; letter-spacing: 0.06em;">PROCESSING PROGRESS</span>
                    <span style="font-family: 'JetBrains Mono', monospace; font-size: 1.05rem; font-weight: 800; color: #F8FAFC;">{pct}%</span>
                </div>

                <!-- Progress Bar -->
                <div style="background: #111827; height: 6px; border-radius: 3px; overflow: hidden; margin-bottom: 14px;">
                    <div style="background: {'#10B981' if is_complete else '#8B5CF6'}; width: {pct}%; height: 100%; border-radius: 3px; transition: width 0.3s ease;"></div>
                </div>

                <!-- Stages -->
                <div>
                    {stages_content}
                </div>
            </div>
        </div>
        """
        return textwrap.dedent(html_raw).strip()

    import uuid

    task_id = str(uuid.uuid4())
    progress_card.html(build_screen_html(0, 0, False))

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(api_client.analyze_contract, file_bytes, filename, task_id)

        curr_stage = 0
        curr_pct = 0

        while not future.done():
            progress_info = api_client.get_analysis_progress(task_id)
            server_stage = progress_info.get("stage", 0)
            server_pct = progress_info.get("pct", 0)

            curr_stage = max(curr_stage, min(int(server_stage), 7))
            curr_pct = max(curr_pct, min(int(server_pct), 95))

            progress_card.html(build_screen_html(curr_stage, curr_pct, False))
            time.sleep(0.15)

        try:
            raw_res = future.result()
            normalized = normalize_analysis_data(raw_res)

            progress_card.html(build_screen_html(7, 100, True))
            time.sleep(0.2)

            st.session_state["current_analysis"] = normalized
            st.session_state["workflow_state"] = "COMPLETE"
            st.rerun()

        except APIClientError as api_err:
            st.session_state["error_message"] = str(api_err)
            st.session_state["workflow_state"] = "ERROR"
            st.rerun()
        except Exception as e:
            st.session_state["error_message"] = f"Analysis pipeline failed: {str(e)}"
            st.session_state["workflow_state"] = "ERROR"
            st.rerun()
