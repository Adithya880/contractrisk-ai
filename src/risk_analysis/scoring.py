"""
Hybrid Scorer and Contract Aggregator for Phase 7.1.
Calculates deterministic hybrid risk scores using exact weights (30% BERT, 35% Rules, 15% RAG, 20% LLM),
applies strict thresholds (<35 LOW, 35-69 MEDIUM, >=70 HIGH),
and aggregates contract-level risk using 0.6 * max + 0.4 * mean.
"""

import math
from typing import List, Sequence
from src.risk_analysis.models import (
    RiskLevel,
    RiskRuleMatch,
    RiskScoreBreakdown,
    RiskAssessment,
    ContractRiskSummary
)

BERT_WEIGHT = 0.30
RULE_WEIGHT = 0.35
RAG_WEIGHT = 0.15
LLM_WEIGHT = 0.20

LOW_THRESHOLD = 35.0
HIGH_THRESHOLD = 70.0


class HybridScorer:
    """Calculates deterministic hybrid risk scores and contract-level aggregations."""

    def __init__(
        self,
        bert_weight: float = BERT_WEIGHT,
        rule_weight: float = RULE_WEIGHT,
        rag_weight: float = RAG_WEIGHT,
        llm_weight: float = LLM_WEIGHT,
    ):
        self.bert_weight = bert_weight
        self.rule_weight = rule_weight
        self.rag_weight = rag_weight
        self.llm_weight = llm_weight

    def calculate_rule_component_score(self, rule_matches: Sequence[RiskRuleMatch]) -> float:
        """
        Calculate rule component score using asymptotic aggregation:
        S_rule = min(100.0, 100.0 * (1.0 - prod(1.0 - w_i / 100.0)))
        """
        if not rule_matches:
            return 0.0

        prod_remaining = 1.0
        for match in rule_matches:
            w = max(0.0, min(100.0, float(match.severity_weight)))
            prod_remaining *= (1.0 - w / 100.0)

        score = 100.0 * (1.0 - prod_remaining)
        return round(max(0.0, min(100.0, score)), 2)

    def determine_risk_level(self, score: float) -> RiskLevel:
        """
        Map numerical score (0-100) to RiskLevel:
        - LOW: score < 35
        - MEDIUM: 35 <= score < 70
        - HIGH: score >= 70
        """
        clamped_score = max(0.0, min(100.0, float(score)))
        if clamped_score < LOW_THRESHOLD:
            return RiskLevel.LOW
        elif clamped_score < HIGH_THRESHOLD:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.HIGH

    def compute_hybrid_score(
        self,
        bert_score: float,
        rule_score: float,
        rag_score: float,
        llm_score: float,
    ) -> RiskScoreBreakdown:
        """
        Compute deterministic hybrid risk score:
        Final = 0.30 * BERT + 0.35 * Rule + 0.15 * RAG + 0.20 * LLM
        When BERT score is 0.0 (category 'Other'), active non-BERT component weights
        are re-scaled so that real Rule and LLM risk signals are not suppressed.
        """
        c_bert = max(0.0, min(100.0, float(bert_score)))
        c_rule = max(0.0, min(100.0, float(rule_score)))
        c_rag = max(0.0, min(100.0, float(rag_score)))
        c_llm = max(0.0, min(100.0, float(llm_score)))

        if c_bert == 0.0:
            if c_rule > 0 or c_rag > 0:
                w_bert = 0.0
                w_rule = round(self.rule_weight / 0.70, 4)
                w_rag = round(self.rag_weight / 0.70, 4)
                w_llm = round(self.llm_weight / 0.70, 4)
                raw_final = w_rule * c_rule + w_rag * c_rag + w_llm * c_llm
            elif c_llm >= 50.0:
                w_bert = 0.0
                w_rule = 0.0
                w_rag = 0.0
                w_llm = 0.70
                raw_final = w_llm * c_llm
            else:
                w_bert = self.bert_weight
                w_rule = self.rule_weight
                w_rag = self.rag_weight
                w_llm = self.llm_weight
                raw_final = (
                    w_bert * c_bert +
                    w_rule * c_rule +
                    w_rag * c_rag +
                    w_llm * c_llm
                )
        else:
            w_bert = self.bert_weight
            w_rule = self.rule_weight
            w_rag = self.rag_weight
            w_llm = self.llm_weight
            raw_final = (
                w_bert * c_bert +
                w_rule * c_rule +
                w_rag * c_rag +
                w_llm * c_llm
            )

        final_score = round(max(0.0, min(100.0, raw_final)), 2)

        return RiskScoreBreakdown(
            bert_component=round(c_bert, 2),
            rule_component=round(c_rule, 2),
            rag_component=round(c_rag, 2),
            llm_component=round(c_llm, 2),
            bert_weight=round(w_bert, 4),
            rule_weight=round(w_rule, 4),
            rag_weight=round(w_rag, 4),
            llm_weight=round(w_llm, 4),
            final_score=final_score
        )

    def aggregate_contract_risk(
        self,
        document_id: str,
        source_filename: str,
        assessments: List[RiskAssessment]
    ) -> ContractRiskSummary:
        """
        Aggregate clause assessments into a ContractRiskSummary:
        Contract Risk Score = 0.6 * max(Clause Scores) + 0.4 * mean(Clause Scores)
        """
        if not assessments:
            return ContractRiskSummary(
                document_id=document_id,
                source_filename=source_filename,
                contract_risk_score=0.0,
                contract_risk_level=RiskLevel.LOW,
                analyzed_clauses_count=0,
                high_risk_clauses_count=0,
                medium_risk_clauses_count=0,
                low_risk_clauses_count=0,
                highest_risk_assessments=[],
                all_assessments=[]
            )

        scores = [a.risk_score for a in assessments]
        max_score = max(scores)
        mean_score = sum(scores) / len(scores)

        raw_contract_score = 0.6 * max_score + 0.4 * mean_score
        contract_score = round(max(0.0, min(100.0, raw_contract_score)), 2)
        contract_level = self.determine_risk_level(contract_score)

        high_count = sum(1 for a in assessments if a.risk_level == RiskLevel.HIGH)
        med_count = sum(1 for a in assessments if a.risk_level == RiskLevel.MEDIUM)
        low_count = sum(1 for a in assessments if a.risk_level == RiskLevel.LOW)

        # Sort assessments descending by risk_score
        sorted_assessments = sorted(assessments, key=lambda a: a.risk_score, reverse=True)

        return ContractRiskSummary(
            document_id=document_id,
            source_filename=source_filename,
            contract_risk_score=contract_score,
            contract_risk_level=contract_level,
            analyzed_clauses_count=len(assessments),
            high_risk_clauses_count=high_count,
            medium_risk_clauses_count=med_count,
            low_risk_clauses_count=low_count,
            highest_risk_assessments=sorted_assessments[:5],  # Top 5 highest risk
            all_assessments=sorted_assessments  # Complete set of all analyzed clauses
        )
