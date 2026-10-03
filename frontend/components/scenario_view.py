"""
Future Scenario Predictor Component for ContractRisk AI.
Primary novelty module visualizing causal trajectory:
Trigger Condition → Potential Scenario → Possible Consequence.
"""

import streamlit as st
from frontend.utils.formatting import get_risk_badge_html, safe_render_html


def render_scenario_view(data: dict):
    """Render structured causal Future Scenario cards."""
    assessments = data.get("clause_assessments", [])

    st.markdown("## Future Scenario Predictor")
    safe_render_html(
        """
        <div class="text-muted" style="margin-bottom: 16px; font-size: 0.88rem;">
            Evidence-grounded potential outcomes if a contractual condition is triggered.
        </div>
        """
    )

    scenarios_found = []
    for a in assessments:
        scen = a.get("future_scenario")
        if scen:
            scenarios_found.append((a, scen))

    if not scenarios_found:
        safe_render_html(
            """
            <div class="panel-primary" style="text-align: center; padding: 36px 20px;">
                <div style="color: #8E9CAE; font-size: 0.9rem;">
                    No future risk scenarios generated for the loaded contract.
                </div>
            </div>
            """
        )
        return

    # Non-Guarantee Analytical Notice
    safe_render_html(
        """
        <div style="background: rgba(139, 92, 246, 0.08); border: 1px solid #3B2D6B; border-radius: 6px; padding: 10px 14px; margin-bottom: 20px; font-size: 0.82rem; color: #CBD5E1;">
            <strong style="color: #A78BFA;">POTENTIAL SCENARIOS:</strong>
            These trajectories model conditional contractual triggers and hypothetical downstream operational impacts. They represent analytical risk projections, not guaranteed legal predictions.
        </div>
        """
    )

    for idx, (assess, scen) in enumerate(scenarios_found, 1):
        c_num = assess.get("clause_number", "")
        c_head = assess.get("clause_heading") or "Untitled Clause"
        c_score = assess.get("risk_score", 0.0)
        c_level = assess.get("risk_level", "LOW")

        title = scen.get("scenario_title", f"Scenario {idx}")
        trigger = scen.get("trigger_condition", "")
        narrative = scen.get("scenario_description", "")
        consequence = scen.get("possible_consequence", "")
        evidence = scen.get("supporting_evidence", [])
        assumptions = scen.get("assumptions", [])
        uncertainty = scen.get("uncertainty", "")

        safe_render_html(
            f"""
            <div class="scenario-card-violet">
                <!-- Card Header -->
                <div style="display: flex; justify-content: space-between; align-items: center; padding-bottom: 10px; margin-bottom: 14px; border-bottom: 1px solid #1F1C38;">
                    <div>
                        <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; font-weight: 700; color: #8B5CF6;">SCENARIO {idx:02d}</span>
                        <h3 style="margin: 2px 0 0 0; color: #F8FAFC;">{title}</h3>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="font-size: 0.82rem; color: #8E9CAE;">Clause {c_num} ({c_score:.1f})</span>
                        {get_risk_badge_html(c_level)}
                    </div>
                </div>

                <!-- Causal Trajectory Flow -->
                
                <!-- 1. TRIGGER -->
                <div style="background: #111422; border: 1px solid #232238; border-radius: 6px; padding: 12px 14px;">
                    <div class="label-caps" style="color: #F59E0B; margin-bottom: 4px;">TRIGGER CONDITION</div>
                    <div style="color: #F1F5F9; font-size: 0.88rem;">{trigger}</div>
                </div>

                <div class="flow-arrow">↓</div>

                <!-- 2. POTENTIAL SCENARIO -->
                <div style="background: #111422; border: 1px solid #232238; border-radius: 6px; padding: 12px 14px;">
                    <div class="label-caps" style="color: #A78BFA; margin-bottom: 4px;">POTENTIAL SCENARIO</div>
                    <div style="color: #CBD5E1; font-size: 0.88rem; line-height: 1.5;">{narrative}</div>
                </div>

                <div class="flow-arrow">↓</div>

                <!-- 3. POSSIBLE CONSEQUENCE -->
                <div style="background: #111422; border: 1px solid #232238; border-radius: 6px; padding: 12px 14px;">
                    <div class="label-caps" style="color: #EF4444; margin-bottom: 4px;">POSSIBLE CONSEQUENCE</div>
                    <div style="color: #F87171; font-size: 0.88rem;">{consequence}</div>
                </div>

                <!-- Supporting Context Sub-Panels -->
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 14px;">
                    <div style="background: #0A0C16; border: 1px solid #1C1B2E; border-radius: 6px; padding: 10px 12px;">
                        <div class="label-caps" style="margin-bottom: 4px;">SUPPORTING EVIDENCE</div>
                        <div style="color: #8E9CAE; font-size: 0.8rem; font-style: italic;">
                            "{evidence[0].get('source_text') if evidence and isinstance(evidence[0], dict) else (evidence[0] if evidence else 'Derived from clause text')}"
                        </div>
                    </div>

                    <div style="background: #0A0C16; border: 1px solid #1C1B2E; border-radius: 6px; padding: 10px 12px;">
                        <div class="label-caps" style="margin-bottom: 4px;">ASSUMPTIONS</div>
                        <div style="color: #8E9CAE; font-size: 0.8rem;">
                            {" · ".join(assumptions) if assumptions else 'No secondary assumptions required.'}
                        </div>
                    </div>
                </div>

                <!-- Uncertainty Statement -->
                <div style="margin-top: 10px; font-size: 0.78rem; color: #5A677A;">
                    <strong style="color: #8E9CAE;">UNCERTAINTY:</strong> {uncertainty}
                </div>
            </div>
            """
        )
