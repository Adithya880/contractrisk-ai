"""
Data models for Phase 7.2 Future Scenario Predictor.
Defines Pydantic v2 data models for evidence-grounded hypothetical future risk scenarios.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from src.rag.models import Citation


class FutureScenario(BaseModel):
    """
    Represents an evidence-grounded hypothetical future risk scenario
    generated for a specific contractual clause or risk assessment.
    """
    model_config = ConfigDict(frozen=True)

    scenario_id: str = Field(description="Unique scenario identifier (scen_{uuid}).")
    clause_id: str = Field(description="Identifier of the target contract clause.")
    clause_number: Optional[str] = Field(default=None, description="Section or clause numbering label.")
    scenario_title: str = Field(description="Concise descriptive title of the hypothetical scenario.")
    trigger_condition: str = Field(description="Plausible event or condition that could trigger the scenario.")
    scenario_description: str = Field(description="Narrative description of what could happen if the risk is triggered.")
    possible_consequence: str = Field(description="Potential legal, operational, or financial consequences.")
    supporting_evidence: List[Citation] = Field(default_factory=list, description="Contractual citations supporting the scenario.")
    assumptions: List[str] = Field(default_factory=list, description="Explicit assumptions required for scenario realization.")
    uncertainty: str = Field(description="Statement of analytical uncertainty, assumptions, or evidence limitations.")
    fallback_active: bool = Field(default=False, description="True if scenario was generated using fallback mode.")
    disclaimer: str = Field(
        default="Future scenarios represent hypothetical decision-support possibilities and are NOT guaranteed predictions or formal legal advice.",
        description="Standard legal disclaimer for predictive scenarios."
    )
