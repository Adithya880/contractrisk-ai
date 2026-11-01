"""
Data models for Phase 7.1 Hybrid Risk Detection & Risk Scoring.
Defines enums, rule match structures, score breakdowns, clause assessments,
and contract-level risk summaries.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class RiskCategory(str, Enum):
    """Categories of legal contract risk."""
    TERMINATION = "Termination"
    LIABILITY = "Liability"
    INDEMNIFICATION = "Indemnification"
    PAYMENT_TERMS = "Payment Terms"
    INTELLECTUAL_PROPERTY = "Intellectual Property"
    CONFIDENTIALITY = "Confidentiality"
    RENEWAL = "Renewal"
    MODIFICATION = "Modification"
    GOVERNING_LAW = "Governing Law"
    WARRANTY = "Warranty"
    NON_COMPETE = "Non-Compete"
    AUDIT_RIGHTS = "Audit Rights"
    DATA_PRIVACY = "Data Privacy"
    FORCE_MAJEURE = "Force Majeure"
    DISPUTE_RESOLUTION = "Dispute Resolution"
    OTHER = "Other"


class RiskLevel(str, Enum):
    """Categorical risk severity levels."""
    NORMAL = "NORMAL"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class LLMInferenceStatus(str, Enum):
    """Status of Qwen3 LLM inference for a clause."""
    SUCCESS = "SUCCESS"
    UNAVAILABLE = "UNAVAILABLE"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class RiskRuleMatch(BaseModel):
    """Details of a single pattern match triggered by the Rule Engine."""
    rule_id: str = Field(..., description="Unique rule identifier")
    risk_category: RiskCategory = Field(..., description="Category of risk detected")
    pattern: str = Field(..., description="Regex pattern or keyword matched")
    description: str = Field(..., description="Human-readable description of risk indicator")
    severity_weight: float = Field(..., ge=0.0, le=100.0, description="Rule severity weight (0-100)")
    matched_text: str = Field(..., description="Snippet of clause text that triggered match")


class RiskScoreBreakdown(BaseModel):
    """Breakdown of component contributions to final hybrid risk score."""
    bert_component: float = Field(..., ge=0.0, le=100.0, description="BERT clause type risk component score")
    rule_component: float = Field(..., ge=0.0, le=100.0, description="Regex rule detection component score")
    rag_component: float = Field(..., ge=0.0, le=100.0, description="RAG benchmark retrieval component score")
    llm_component: float = Field(..., ge=0.0, le=100.0, description="LLM risk interpretation component score")
    bert_weight: float = Field(0.30, description="BERT weight contribution (30%)")
    rule_weight: float = Field(0.35, description="Rule weight contribution (35%)")
    rag_weight: float = Field(0.15, description="RAG weight contribution (15%)")
    llm_weight: float = Field(0.20, description="LLM weight contribution (20%)")
    final_score: float = Field(..., ge=0.0, le=100.0, description="Calculated final risk score (0-100)")


class RiskAssessment(BaseModel):
    """Complete hybrid risk assessment for a single contract clause."""
    assessment_id: str = Field(..., description="Unique assessment ID")
    document_id: str = Field(..., description="Parent document identifier")
    clause_id: str = Field(..., description="Segmented clause ID")
    clause_number: Optional[str] = Field(None, description="Clause numbering label")
    clause_heading: Optional[str] = Field(None, description="Clause title or heading")
    clause_text: str = Field(..., description="Original full text of the clause")
    clause_type: str = Field(..., description="Predicted BERT clause category")
    bert_confidence: float = Field(..., ge=0.0, le=1.0, description="BERT softmax prediction confidence")
    is_uncertain_classification: bool = Field(default=False, description="True if BERT confidence is below reliability threshold")
    display_category: str = Field(default="", description="Category for user presentation, marking weak predictions as uncertain")
    risk_category: RiskCategory = Field(..., description="Primary risk domain for this clause")
    risk_score: float = Field(..., ge=0.0, le=100.0, description="Final deterministic risk score")
    risk_level: RiskLevel = Field(..., description="NORMAL, LOW, MEDIUM, or HIGH risk rating")
    score_breakdown: RiskScoreBreakdown = Field(..., description="Mathematical score component breakdown")
    detected_rules: List[RiskRuleMatch] = Field(default_factory=list, description="Rule matches triggered")
    intra_clause_contradictions: List[Any] = Field(default_factory=list, description="Internal contradictions or asymmetries inside this clause")
    risk_explanation: Optional[str] = Field(default=None, description="Grounded Qwen3 LLM explanation of risk factors, if executed")
    llm_inference_status: LLMInferenceStatus = Field(default=LLMInferenceStatus.SKIPPED, description="Status of Qwen3 inference (SUCCESS, UNAVAILABLE, FAILED, SKIPPED)")
    evidence_summary: str = Field(..., description="Summary of retrieval evidence or benchmark matches")
    key_risk_factors: List[str] = Field(default_factory=list, description="Extracted key risk points")
    evidence: List[Dict[str, Any]] = Field(default_factory=list, description="Retrieved benchmark evidence clauses")
    source_pages: List[int] = Field(default_factory=list, description="Page provenance numbers")
    uncertainty: str = Field(..., description="Statement of analysis uncertainty or assumptions")
    future_scenario: Optional[Any] = Field(default=None, description="Pre-computed FutureScenario if deep analysis was performed")
    disclaimer: str = Field(
        default="This risk score is a heuristic decision-support signal and does NOT constitute formal legal advice.",
        description="Standard legal disclaimer"
    )


class CrossClauseConflict(BaseModel):
    """Details of a contradiction or dependency identified across or within contract clauses."""
    conflict_id: str = Field(..., description="Unique conflict identifier")
    conflict_type: str = Field(..., description="Classification of contradiction or dependency")
    severity: RiskLevel = Field(RiskLevel.HIGH, description="Risk severity rating")
    clause_ids: List[str] = Field(default_factory=list, description="IDs of involved clauses")
    clause_numbers: List[str] = Field(default_factory=list, description="Section numbers of involved clauses")
    explanation: str = Field(..., description="Concise explanation of the contradiction or dependency")
    conflicting_excerpt_a: str = Field("", description="Key excerpt from first provision")
    conflicting_excerpt_b: str = Field("", description="Key excerpt from second provision")


class ContractRiskSummary(BaseModel):
    """Aggregate risk profile for an entire contract document."""
    document_id: str = Field(..., description="Document identifier")
    source_filename: str = Field(..., description="Original filename of contract document")
    contract_risk_score: float = Field(..., ge=0.0, le=100.0, description="Aggregated overall document risk score")
    contract_risk_level: RiskLevel = Field(..., description="Overall contract risk level (LOW/MEDIUM/HIGH)")
    analyzed_clauses_count: int = Field(..., ge=0, description="Total clauses evaluated")
    normal_risk_clauses_count: int = Field(default=0, ge=0, description="Count of NORMAL risk clauses")
    high_risk_clauses_count: int = Field(..., ge=0, description="Count of HIGH risk clauses")
    medium_risk_clauses_count: int = Field(..., ge=0, description="Count of MEDIUM risk clauses")
    low_risk_clauses_count: int = Field(..., ge=0, description="Count of LOW risk clauses")
    highest_risk_assessments: List[RiskAssessment] = Field(
        default_factory=list,
        description="Top highest-risk clause assessments sorted descending by score"
    )
    all_assessments: List[RiskAssessment] = Field(
        default_factory=list,
        description="All analyzed clause risk assessments"
    )
    combined_scenario: Optional[Any] = Field(
        default=None,
        description="Combined Future Scenario across contract risks"
    )
    cross_clause_conflicts: List[CrossClauseConflict] = Field(
        default_factory=list,
        description="Detected cross-clause contradictions and conflicts"
    )
    intra_clause_contradictions: List[CrossClauseConflict] = Field(
        default_factory=list,
        description="Detected intra-clause inconsistencies and unilateral asymmetries"
    )
    pipeline_timings: Dict[str, float] = Field(
        default_factory=dict,
        description="Execution timings in seconds per pipeline stage"
    )
    disclaimer: str = Field(
        default="Contract risk scores are automated decision-support signals and do NOT constitute formal legal advice.",
        description="Standard legal disclaimer"
    )
