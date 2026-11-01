"""
FastAPI Request and Response Pydantic Schemas for ContractRisk AI.
Defines explicit, stable API response structures for health, models, and risk analysis endpoints.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Response model for GET /api/v1/health."""
    status: str = Field("healthy", description="Health status string.")
    service: str = Field("ContractRisk AI", description="Name of the service.")
    version: str = Field("1.0.0", description="API version string.")


class ComponentMetadataSchema(BaseModel):
    """Component configuration details."""
    name: str = Field(..., description="Name of component or model.")
    status: str = Field(..., description="Active or loaded status.")
    details: Dict[str, Any] = Field(default_factory=dict, description="Non-sensitive configuration parameters.")


class ModelInfoResponse(BaseModel):
    """Response model for GET /api/v1/models."""
    bert_classifier: ComponentMetadataSchema = Field(..., description="BERT clause classification model info.")
    embedding_model: ComponentMetadataSchema = Field(..., description="Sentence transformer embedding model info.")
    vector_store: ComponentMetadataSchema = Field(..., description="FAISS vector similarity index info.")
    local_llm: ComponentMetadataSchema = Field(..., description="Local Qwen3 / LM Studio inference info.")
    scenario_predictor: ComponentMetadataSchema = Field(..., description="Future Scenario Predictor info.")


class DocumentMetadataSchema(BaseModel):
    """Processed document metadata."""
    document_id: str = Field(..., description="Unique document ID.")
    filename: str = Field(..., description="Original uploaded filename.")
    document_type: str = Field(..., description="PDF or DOCX source format.")
    number_of_clauses: int = Field(..., description="Total clauses segmented.")


class FutureScenarioSchema(BaseModel):
    """Generated future risk scenario model for API clients."""
    scenario_id: str = Field(..., description="Scenario unique ID.")
    clause_id: str = Field(..., description="Target clause ID.")
    clause_number: Optional[str] = Field(None, description="Clause numbering label.")
    scenario_title: str = Field(..., description="Title of hypothetical scenario.")
    trigger_condition: str = Field(..., description="Conditional event triggering scenario.")
    scenario_description: str = Field(..., description="Grounded narrative describing scenario trajectory.")
    possible_consequence: str = Field(..., description="Potential legal or financial impact.")
    supporting_evidence: List[Dict[str, Any]] = Field(default_factory=list, description="Citations supporting scenario.")
    assumptions: List[str] = Field(default_factory=list, description="Explicit analytical premises.")
    uncertainty: str = Field(..., description="Statement of analytical uncertainty.")
    fallback_active: bool = Field(False, description="True if generated in fallback mode.")
    disclaimer: str = Field(..., description="Legal disclaimer.")


class CrossClauseConflictSchema(BaseModel):
    """Details of a contradiction or dependency identified across clauses."""
    conflict_id: str = Field(..., description="Unique conflict identifier.")
    conflict_type: str = Field(..., description="Classification of contradiction or dependency.")
    severity: str = Field(..., description="Risk severity level (HIGH or MEDIUM).")
    clause_ids: List[str] = Field(default_factory=list, description="IDs of clauses involved.")
    clause_numbers: List[str] = Field(default_factory=list, description="Section numbers of clauses involved.")
    explanation: str = Field(..., description="Concise explanation of contradiction or dependency.")
    conflicting_excerpt_a: str = Field("", description="Key excerpt from first provision.")
    conflicting_excerpt_b: str = Field("", description="Key excerpt from second provision.")


class ContractSummarySchema(BaseModel):
    """Document-level risk score summary."""
    risk_score: float = Field(..., description="Aggregated contract risk score (0-100).")
    risk_level: str = Field(..., description="NORMAL, LOW, MEDIUM, or HIGH contract risk rating.")
    normal_risk_clause_count: int = Field(0, description="Number of NORMAL risk clauses.")
    high_risk_clause_count: int = Field(..., description="Number of HIGH risk clauses.")
    medium_risk_clause_count: int = Field(..., description="Number of MEDIUM risk clauses.")
    low_risk_clause_count: int = Field(..., description="Number of LOW risk clauses.")
    combined_scenario: Optional[FutureScenarioSchema] = Field(None, description="Combined Future Scenario across contract risks.")
    cross_clause_conflicts: List[CrossClauseConflictSchema] = Field(default_factory=list, description="Detected cross-clause conflicts.")
    intra_clause_contradictions: List[CrossClauseConflictSchema] = Field(default_factory=list, description="Detected intra-clause inconsistencies and unilateral asymmetries.")
    pipeline_timings: Dict[str, float] = Field(default_factory=dict, description="Stage timings in seconds.")


class RuleMatchSchema(BaseModel):
    """Rule match details for API clients."""
    rule_id: str = Field(..., description="Rule ID matched.")
    risk_category: str = Field(..., description="Category of rule.")
    description: str = Field(..., description="Human-readable rule description.")
    severity_weight: float = Field(..., description="Rule severity weight.")
    matched_text: str = Field(..., description="Matched text snippet.")


class ComponentBreakdownSchema(BaseModel):
    """Score component breakdown for API clients."""
    bert_component: float = Field(..., description="BERT score contribution (30%).")
    rule_component: float = Field(..., description="Rule score contribution (35%).")
    rag_component: float = Field(..., description="RAG score contribution (15%).")
    llm_component: float = Field(..., description="LLM score contribution (20%).")
    final_score: float = Field(..., description="Calculated final risk score.")


class ClauseAssessmentSchema(BaseModel):
    """Clause-level risk assessment for API clients."""
    clause_id: str = Field(..., description="Clause ID.")
    clause_number: Optional[str] = Field(None, description="Clause section number.")
    clause_heading: Optional[str] = Field(None, description="Clause title.")
    clause_text: str = Field(..., description="Full text of clause.")
    risk_score: float = Field(..., description="Deterministic hybrid risk score.")
    risk_level: str = Field(..., description="NORMAL, LOW, MEDIUM, or HIGH.")
    risk_category: str = Field(..., description="Primary risk domain.")
    bert_label: str = Field(..., description="Predicted BERT clause category.")
    bert_confidence: float = Field(..., description="BERT softmax prediction confidence.")
    is_uncertain_classification: bool = Field(False, description="True if BERT confidence is below reliability threshold.")
    display_category: Optional[str] = Field(None, description="Category for user presentation, marking weak predictions as uncertain.")
    rule_matches: List[RuleMatchSchema] = Field(default_factory=list, description="Rule matches triggered.")
    intra_clause_contradictions: List[CrossClauseConflictSchema] = Field(default_factory=list, description="Intra-clause inconsistencies and asymmetries in this clause.")
    component_score_breakdown: ComponentBreakdownSchema = Field(..., description="Breakdown of score components.")
    llm_explanation: Optional[str] = Field(None, description="Grounded Qwen3 LLM explanation, if successfully executed.")
    llm_inference_status: str = Field("SKIPPED", description="Status of Qwen3 LLM inference: SUCCESS, UNAVAILABLE, FAILED, or SKIPPED.")
    key_risk_factors: List[str] = Field(default_factory=list, description="Extracted key risk points.")
    uncertainty: str = Field(..., description="Statement of analytical uncertainty.")
    evidence: List[Dict[str, Any]] = Field(default_factory=list, description="Benchmark precedent evidence clauses retrieved via RAG.")
    future_scenario: Optional[FutureScenarioSchema] = Field(None, description="Future Scenario Predictor output if generated.")


class AnalysisResponse(BaseModel):
    """Complete response structure for POST /api/v1/analyze."""
    document: DocumentMetadataSchema = Field(..., description="Document metadata.")
    contract_summary: ContractSummarySchema = Field(..., description="Contract-level risk summary.")
    clause_assessments: List[ClauseAssessmentSchema] = Field(default_factory=list, description="Clause-level risk assessments.")
    combined_scenario: Optional[FutureScenarioSchema] = Field(None, description="Combined Future Scenario across contract risks.")
    cross_clause_conflicts: List[CrossClauseConflictSchema] = Field(default_factory=list, description="Detected cross-clause conflicts.")
    intra_clause_contradictions: List[CrossClauseConflictSchema] = Field(default_factory=list, description="Detected intra-clause inconsistencies and unilateral asymmetries.")
    pipeline_timings: Dict[str, float] = Field(default_factory=dict, description="Stage timings in seconds.")
    disclaimer: str = Field(
        "Contract risk scores and scenarios are decision-support signals and do NOT constitute formal legal advice.",
        description="Legal disclaimer."
    )
