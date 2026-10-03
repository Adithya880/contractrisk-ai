"""
Contract Risk Analyzer Facade for Phase 7.1.
Orchestrates BERT classification, Rule Engine pattern matching, Phase 6/7 RAG evidence retrieval,
local Qwen3 LLM risk interpretation, and deterministic Hybrid Scorer aggregation.
"""

import time
import uuid
import logging
from typing import List, Optional, Dict, Any, Tuple
from src.clause_segmentation.models import SegmentedClause, SegmentationResult
from src.risk_analysis.models import (
    RiskCategory,
    RiskLevel,
    RiskRuleMatch,
    RiskAssessment,
    ContractRiskSummary
)
from src.risk_analysis.rule_engine import RuleEngine
from src.risk_analysis.bert_risk_mapper import BERTRiskMapper
from src.risk_analysis.scoring import HybridScorer
from src.rag.generator import LLMGenerator, LLMGeneratorError

logger = logging.getLogger(__name__)


class ContractRiskAnalyzer:
    """
    Unified analyzer executing complete hybrid contract risk detection & scoring.
    """

    def __init__(
        self,
        rule_engine: Optional[RuleEngine] = None,
        bert_mapper: Optional[BERTRiskMapper] = None,
        scorer: Optional[HybridScorer] = None,
        rag_pipeline: Optional[Any] = None,
        generator: Optional[LLMGenerator] = None,
        bert_classifier: Optional[Any] = None,
        scenario_predictor: Optional[Any] = None,
        max_deep_clauses: int = 15,
    ):
        """
        Initialize ContractRiskAnalyzer with optional subsystem overrides.
        """
        self.rule_engine = rule_engine or RuleEngine()
        self.bert_mapper = bert_mapper or BERTRiskMapper()
        self.scorer = scorer or HybridScorer()
        self.rag_pipeline = rag_pipeline
        self.generator = generator or LLMGenerator()
        self.bert_classifier = bert_classifier
        self._scenario_predictor = scenario_predictor
        self.max_deep_clauses = max_deep_clauses

    @property
    def scenario_predictor(self):
        """Lazily initialize or return FutureScenarioPredictor."""
        if self._scenario_predictor is None:
            from src.risk_analysis.scenario_predictor import FutureScenarioPredictor
            self._scenario_predictor = FutureScenarioPredictor(generator=self.generator)
        return self._scenario_predictor

    def analyze_clause(
        self,
        clause: SegmentedClause,
        document_id: str,
        predicted_clause_type: Optional[str] = None,
        bert_confidence: Optional[float] = None,
        skip_llm: bool = False,
    ) -> RiskAssessment:
        """
        Perform hybrid risk analysis on a single segmented clause.

        Args:
            clause: SegmentedClause object from Phase 5.
            document_id: Identifier of the parent contract document.
            predicted_clause_type: Pre-predicted BERT category string (optional).
            bert_confidence: Pre-predicted BERT softmax confidence (optional).
            skip_llm: If True, evaluates deterministically without querying Qwen3.

        Returns:
            RiskAssessment containing detailed score breakdown, rule matches, evidence, and explanation.
        """
        assessment_id = f"assess_{uuid.uuid4().hex[:8]}"
        clause_text = clause.clause_text.strip()

        # 1. BERT Clause Classification Signal
        clause_type = predicted_clause_type or "Other"
        confidence = float(bert_confidence) if bert_confidence is not None else 1.0

        if self.bert_classifier is not None and predicted_clause_type is None:
            try:
                # If BERT model instance was provided
                pred_type, pred_conf = self.bert_classifier.predict_clause(clause_text)
                clause_type = pred_type
                confidence = pred_conf
            except Exception:
                clause_type = "Other"
                confidence = 0.5

        base_bert_weight, primary_category = self.bert_mapper.get_clause_risk_info(clause_type)
        bert_component_score = self.bert_mapper.calculate_bert_component_score(clause_type, confidence)

        # 2. Rule Engine Pattern Detection Signal
        rule_matches = self.rule_engine.analyze_clause(clause_text)
        rule_component_score = self.scorer.calculate_rule_component_score(rule_matches)

        # Update primary risk category if high-severity rule match exists
        if rule_matches:
            highest_rule = max(rule_matches, key=lambda m: m.severity_weight)
            if highest_rule.severity_weight >= 70.0:
                primary_category = highest_rule.risk_category

        # 3. RAG Benchmark Evidence Signal
        evidence_items: List[Dict[str, Any]] = []
        rag_component_score = 0.0
        evidence_summary = "No benchmark evidence retrieved."

        if self.rag_pipeline is not None and hasattr(self.rag_pipeline, "retriever"):
            try:
                retrieved = self.rag_pipeline.retriever.retrieve_evidence(
                    query=clause_text,
                    top_k=3,
                    similarity_threshold=0.4
                )
                if retrieved:
                    evidence_items = [item.dict() if hasattr(item, "dict") else dict(item) for item in retrieved]
                    sims = [getattr(item, "similarity_score", 0.5) for item in retrieved]
                    avg_sim = sum(sims) / len(sims)
                    rag_component_score = round(max(0.0, min(100.0, avg_sim * 100.0)), 2)
                    evidence_summary = f"Retrieved {len(retrieved)} benchmark evidence clauses (top similarity: {max(sims):.2f})."
            except Exception:
                rag_component_score = 0.0
                evidence_summary = "RAG retrieval attempt failed; defaulting to 0."

        # 4. Local Qwen3 Risk Explanation Signal (or deterministic template if skip_llm=True)
        if skip_llm:
            heuristic_llm_score = 0.0
            if rule_matches:
                max_sev = max(r.severity_weight for r in rule_matches)
                heuristic_llm_score = max_sev
            elif confidence > 0.5 and base_bert_weight > 0:
                heuristic_llm_score = base_bert_weight * confidence
            else:
                words = clause_text.split()
                if len(words) <= 4 and (clause_text.isupper() or not any(p in clause_text for p in [".", ";", ":"])):
                    heuristic_llm_score = 0.0
                else:
                    lower_text = clause_text.lower()
                    if any(k in lower_text for k in ["exclude or limit", "limitation of liability", "unlimited liability", "indemnif"]):
                        heuristic_llm_score = 65.0
                    elif any(k in lower_text for k in ["terminate immediately", "right to terminate", "without cause"]):
                        heuristic_llm_score = 55.0
                    else:
                        heuristic_llm_score = 15.0

            llm_score = round(max(0.0, min(100.0, heuristic_llm_score)), 2)
            if rule_matches:
                explanation = f"Evaluated under {clause_type} with {len(rule_matches)} rule match(es): {', '.join(r.description for r in rule_matches)}."
            else:
                explanation = f"Standard contractual terms evaluated under {clause_type} category."
            key_factors = [r.description for r in rule_matches] if rule_matches else [f"Category: {clause_type}"]
            uncertainty = "Deterministic evaluation: low-risk clause bypassed LLM inference."
        else:
            llm_score, explanation, key_factors, uncertainty = self._get_llm_risk_explanation(
                clause_text=clause_text,
                clause_type=clause_type,
                confidence=confidence,
                rule_matches=rule_matches,
                evidence_summary=evidence_summary
            )

        # 5. Deterministic Hybrid Score Calculation
        score_breakdown = self.scorer.compute_hybrid_score(
            bert_score=bert_component_score,
            rule_score=rule_component_score,
            rag_score=rag_component_score,
            llm_score=llm_score
        )

        risk_level = self.scorer.determine_risk_level(score_breakdown.final_score)

        return RiskAssessment(
            assessment_id=assessment_id,
            document_id=document_id,
            clause_id=clause.clause_id,
            clause_number=clause.clause_number,
            clause_heading=clause.clause_heading,
            clause_text=clause.clause_text,
            clause_type=clause_type,
            bert_confidence=confidence,
            risk_category=primary_category,
            risk_score=score_breakdown.final_score,
            risk_level=risk_level,
            score_breakdown=score_breakdown,
            detected_rules=rule_matches,
            risk_explanation=explanation,
            evidence_summary=evidence_summary,
            key_risk_factors=key_factors,
            evidence=evidence_items,
            source_pages=clause.source_pages,
            uncertainty=uncertainty,
            future_scenario=None
        )

    def analyze_document(
        self,
        segmentation_result: SegmentationResult,
        predicted_clause_types: Optional[Dict[str, Tuple[str, float]]] = None,
        max_deep_clauses: Optional[int] = None
    ) -> ContractRiskSummary:
        """
        Analyze all clauses in a SegmentationResult and produce a ContractRiskSummary.
        Executes two-stage optimized inference:
        Stage 1: Fast deterministic evaluation over all clauses (0 LLM calls).
        Stage 2: Candidate filtering (HIGH/MEDIUM risk, up to max_deep_clauses).
        Stage 3: Deep unified Qwen3 analysis (risk explanation + future scenario in 1 call).
        Stage 4: Recalculate hybrid scores and aggregate contract risk.
        """
        max_deep = max_deep_clauses if max_deep_clauses is not None else self.max_deep_clauses
        t0 = time.perf_counter()

        assessments: List[RiskAssessment] = []
        doc_id = segmentation_result.document_id
        source_name = segmentation_result.source_filename

        # Stage 1: Fast Deterministic Evaluation (0 LLM calls for all clauses)
        t_fast_start = time.perf_counter()
        for clause in segmentation_result.clauses:
            pred_type = None
            pred_conf = None
            if predicted_clause_types and clause.clause_id in predicted_clause_types:
                pred_type, pred_conf = predicted_clause_types[clause.clause_id]

            assessment = self.analyze_clause(
                clause=clause,
                document_id=doc_id,
                predicted_clause_type=pred_type,
                bert_confidence=pred_conf,
                skip_llm=True
            )
            assessments.append(assessment)
        fast_pass_time = time.perf_counter() - t_fast_start
        total_clauses = len(assessments)

        # Stage 2: Filter HIGH and MEDIUM Risk Candidate Clauses
        candidates = [a for a in assessments if a.risk_level in (RiskLevel.HIGH, RiskLevel.MEDIUM)]

        if len(candidates) > max_deep:
            candidates_to_analyze = sorted(candidates, key=lambda a: a.risk_score, reverse=True)[:max_deep]
        else:
            candidates_to_analyze = candidates

        # Stage 3: Deep LLM Analysis (Unified Single Call per candidate)
        t_deep_start = time.perf_counter()
        qwen_calls_count = 0

        for candidate in candidates_to_analyze:
            try:
                citations = self.scenario_predictor._build_citations_from_assessment(candidate)
                llm_score, explanation, key_factors, uncertainty, scenario = (
                    self.scenario_predictor.predict_deep_scenario_and_explanation(
                        clause_id=candidate.clause_id,
                        clause_number=candidate.clause_number,
                        clause_heading=candidate.clause_heading,
                        clause_text=candidate.clause_text,
                        clause_type=candidate.clause_type,
                        bert_confidence=candidate.bert_confidence,
                        risk_category=candidate.risk_category,
                        detected_rules=candidate.detected_rules,
                        evidence_summary=candidate.evidence_summary,
                        citations=citations
                    )
                )
                qwen_calls_count += 1

                # Recompute hybrid score with deep LLM score
                score_breakdown = self.scorer.compute_hybrid_score(
                    bert_score=candidate.score_breakdown.bert_component,
                    rule_score=candidate.score_breakdown.rule_component,
                    rag_score=candidate.score_breakdown.rag_component,
                    llm_score=llm_score
                )
                candidate.risk_score = score_breakdown.final_score
                candidate.risk_level = self.scorer.determine_risk_level(candidate.risk_score)
                candidate.score_breakdown = score_breakdown
                candidate.risk_explanation = explanation
                candidate.key_risk_factors = key_factors
                candidate.uncertainty = uncertainty
                candidate.future_scenario = scenario if candidate.risk_level in (RiskLevel.HIGH, RiskLevel.MEDIUM) else None

            except Exception as e:
                logger.warning(f"Deep analysis failed for clause {candidate.clause_id}: {e}")

        deep_llm_time = time.perf_counter() - t_deep_start
        total_time = time.perf_counter() - t0
        skipped_count = total_clauses - len(candidates_to_analyze)

        # Count final risk levels
        high_cnt = sum(1 for a in assessments if a.risk_level == RiskLevel.HIGH)
        med_cnt = sum(1 for a in assessments if a.risk_level == RiskLevel.MEDIUM)
        low_cnt = sum(1 for a in assessments if a.risk_level == RiskLevel.LOW)

        # Required [PERF] instrumentation
        perf_summary = (
            f"\n==================== [PERF] INFERENCE REPORT ====================\n"
            f"[PERF] Total Clauses: {total_clauses}\n"
            f"[PERF] Deep LLM Candidates: {len(candidates_to_analyze)} (HIGH: {high_cnt}, MEDIUM: {med_cnt})\n"
            f"[PERF] Low-Risk Skipped (0 Qwen calls): {skipped_count}\n"
            f"[PERF] Total Qwen Calls: {qwen_calls_count}\n"
            f"[PERF] Fast Pass Duration: {fast_pass_time:.2f}s\n"
            f"[PERF] Deep LLM Duration: {deep_llm_time:.2f}s\n"
            f"[PERF] Total Analysis Duration: {total_time:.2f}s\n"
            f"================================================================="
        )
        logger.info(perf_summary)
        print(perf_summary)

        return self.scorer.aggregate_contract_risk(
            document_id=doc_id,
            source_filename=source_name,
            assessments=assessments
        )

    def _get_llm_risk_explanation(
        self,
        clause_text: str,
        clause_type: str,
        confidence: float,
        rule_matches: List[RiskRuleMatch],
        evidence_summary: str
    ) -> Tuple[float, str, List[str], str]:
        """Query Qwen3 via LMStudio or generate deterministic fallback."""
        rule_str = ", ".join([f"{r.rule_id} ({r.description})" for r in rule_matches]) or "None"

        user_prompt = (
            f"You are ContractRisk AI's Legal Risk Evaluator.\n"
            f"STRICT GROUNDING & ANTI-HALLUCINATION RULES:\n"
            f"1. Base all factual statements strictly on the supplied clause text.\n"
            f"2. DO NOT infer 'unlimited liability' or uncapped exposure unless the clause text explicitly states unlimited liability or uncapped damages.\n"
            f"3. DO NOT infer breach of contract, illegality, unenforceability, damages entitlement, or legal invalidity unless explicitly supported by the clause text.\n"
            f"4. DO NOT convert the absence of a limitation or liability cap into proof of unlimited liability.\n"
            f"5. If the clause text contains routine, administrative, or non-risky terms (or if BERT category is 'Other' and no rules match), assign a low llm_score (0-25) and state that the clause represents standard/routine terms without significant legal risk.\n"
            f"6. Preserve uncertainty where the clause text is silent or incomplete.\n\n"
            f"TARGET CONTRACTUAL EVIDENCE:\n"
            f"Clause Text: {clause_text}\n"
            f"BERT Clause Category: {clause_type} (Confidence: {confidence:.2f})\n"
            f"Detected Rule Matches: {rule_str}\n"
            f"Benchmark Evidence: {evidence_summary}\n\n"
            f"Respond with a JSON object containing keys: 'risk_explanation' (string), "
            f"'key_risk_factors' (list of strings), 'llm_score' (number 0-100), 'uncertainty' (string)."
        )

        try:
            raw_response = self.generator.generate(
                query="Assess contract clause risk.",
                context=user_prompt
            )
            # Parse extracted JSON fields
            llm_score = float(raw_response.get("llm_score", 50.0))
            llm_score = round(max(0.0, min(100.0, llm_score)), 2)
            explanation = str(raw_response.get("risk_explanation", "Risk analysis generated by local Qwen3 model."))
            key_factors = list(raw_response.get("key_risk_factors", []))
            if not key_factors and rule_matches:
                key_factors = [r.description for r in rule_matches]
            uncertainty = str(raw_response.get("uncertainty", "Grounded analysis subject to user verification."))

            return llm_score, explanation, key_factors, uncertainty

        except Exception as e:
            # Clean fallback when LM Studio is offline or returns unparseable response
            heuristic_llm_score = 0.0
            if rule_matches:
                max_sev = max(r.severity_weight for r in rule_matches)
                heuristic_llm_score = max_sev
            elif confidence > 0.5:
                base_w, _ = self.bert_mapper.get_clause_risk_info(clause_type)
                heuristic_llm_score = base_w * confidence
            else:
                heuristic_llm_score = 25.0

            heuristic_llm_score = round(max(0.0, min(100.0, heuristic_llm_score)), 2)

            explanation = (
                f"Automated risk explanation (LM Studio offline/bypassed): Clause evaluated under "
                f"{clause_type} category with {len(rule_matches)} rule match(es)."
            )
            key_factors = [r.description for r in rule_matches] if rule_matches else [f"Category: {clause_type}"]
            uncertainty = f"Fallback mode active ({type(e).__name__}); local LLM generation was not executed."

            return heuristic_llm_score, explanation, key_factors, uncertainty
