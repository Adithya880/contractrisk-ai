"""
Contract Risk Analyzer Facade for Phase 7.1.
Orchestrates BERT classification, Rule Engine pattern matching, Phase 6/7 RAG evidence retrieval,
local Qwen3 LLM risk interpretation, and deterministic Hybrid Scorer aggregation.
"""

import os
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
    ContractRiskSummary,
    LLMInferenceStatus
)
from src.risk_analysis.rule_engine import RuleEngine
from src.risk_analysis.bert_risk_mapper import BERTRiskMapper
from src.risk_analysis.scoring import HybridScorer
from src.rag.generator import LLMGenerator, LLMGeneratorError, LMStudioConnectionError

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
        conflict_detector: Optional[Any] = None,
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
        self._conflict_detector = conflict_detector
        self.max_deep_clauses = max_deep_clauses

    @property
    def scenario_predictor(self):
        """Lazily initialize or return FutureScenarioPredictor."""
        if self._scenario_predictor is None:
            from src.risk_analysis.scenario_predictor import FutureScenarioPredictor
            self._scenario_predictor = FutureScenarioPredictor(generator=self.generator)
        return self._scenario_predictor

    @property
    def conflict_detector(self):
        """Lazily initialize or return CrossClauseConflictDetector."""
        if self._conflict_detector is None:
            from src.risk_analysis.conflict_detector import CrossClauseConflictDetector
            self._conflict_detector = CrossClauseConflictDetector()
        return self._conflict_detector

    def analyze_clause(
        self,
        clause: SegmentedClause,
        document_id: str,
        predicted_clause_type: Optional[str] = None,
        bert_confidence: Optional[float] = None,
        skip_llm: bool = False,
        pre_retrieved_evidence: Optional[List[Dict[str, Any]]] = None,
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
        confidence_threshold = float(os.getenv("BERT_CONFIDENCE_THRESHOLD", "0.45"))
        is_uncertain = confidence < confidence_threshold
        display_category = "Uncertain – manual review recommended" if is_uncertain else clause_type

        if self.bert_classifier is not None and predicted_clause_type is None:
            try:
                # If BERT model instance was provided
                pred_type, pred_conf = self.bert_classifier.predict_clause(clause_text)
                clause_type = pred_type
                confidence = pred_conf
                is_uncertain = confidence < confidence_threshold
                display_category = "Uncertain – manual review recommended" if is_uncertain else clause_type
            except Exception as e:
                logger.warning(f"BERT prediction failed for clause {clause.clause_id}: {e}")
                clause_type = "Other"
                confidence = 0.5
                is_uncertain = confidence < confidence_threshold
                display_category = "Uncertain – manual review recommended" if is_uncertain else clause_type

        base_bert_weight, primary_category = self.bert_mapper.get_clause_risk_info(clause_type)
        bert_component_score = self.bert_mapper.calculate_bert_component_score(clause_type, confidence)

        # 2. Rule Engine Pattern Detection Signal & Intra-Clause Inconsistency Check
        rule_matches = self.rule_engine.analyze_clause(clause_text)
        rule_component_score = self.scorer.calculate_rule_component_score(rule_matches)

        # Intra-clause contradiction and asymmetry check
        intra_conflicts = self.conflict_detector.detect_intra_clause_contradictions([clause])
        if intra_conflicts:
            # Internal legal contradictions (e.g. damages disclaimed but liability unlimited,
            # or mutual notice contradicted by unilateral immediate stoppage) represent severe risk
            rule_component_score = max(rule_component_score, 85.0)

        # Primary risk domain determination:
        # BERT provides clause_type independently. If BERT category risk mapping is OTHER and a rule matched,
        # assign the highest rule's risk domain to primary_category, but NEVER overwrite clause_type!
        if primary_category == RiskCategory.OTHER and rule_matches:
            highest_rule = max(rule_matches, key=lambda m: m.severity_weight)
            if highest_rule.risk_category != RiskCategory.OTHER:
                primary_category = highest_rule.risk_category

        # 3. RAG Benchmark Evidence Signal
        evidence_items: List[Dict[str, Any]] = []
        rag_component_score = 0.0
        evidence_summary = "No benchmark evidence retrieved."

        if pre_retrieved_evidence is not None:
            # Optimized batched retrieval path: use pre-retrieved evidence
            evidence_items = pre_retrieved_evidence
            if evidence_items:
                sims = [float(e.get("similarity_score", 0.5)) for e in evidence_items]
                avg_sim = sum(sims) / len(sims)
                rag_component_score = round(max(0.0, min(100.0, avg_sim * 100.0)), 2)
                top_heading = evidence_items[0].get("clause_heading", "Benchmark")
                evidence_summary = (
                    f"Retrieved {len(evidence_items)} benchmark precedent clauses "
                    f"(top similarity: {max(sims):.2f}, precedent type: [{top_heading}])."
                )
        elif self.rag_pipeline is not None and hasattr(self.rag_pipeline, "retriever"):
            try:
                retrieved = self.rag_pipeline.retriever.retrieve_evidence(
                    query=clause_text,
                    top_k=3,
                    similarity_threshold=0.40
                )
                if retrieved:
                    evidence_items = []
                    sims = []
                    for item in retrieved:
                        sim = float(getattr(item, "similarity_score", 0.5))
                        sims.append(sim)
                        evidence_items.append({
                            "clause_id": getattr(item, "clause_id", "Precedent"),
                            "source_clause_id": getattr(item, "clause_id", "Precedent"),
                            "document_id": getattr(item, "document_id", "reference_corpus"),
                            "clause_number": getattr(item, "clause_number", None),
                            "clause_heading": getattr(item, "clause_heading", "Precedent"),
                            "clause_text": getattr(item, "clause_text", ""),
                            "source_pages": getattr(item, "source_pages", [1]),
                            "similarity_score": round(sim, 4),
                        })
                    avg_sim = sum(sims) / len(sims)
                    rag_component_score = round(max(0.0, min(100.0, avg_sim * 100.0)), 2)
                    top_heading = evidence_items[0].get("clause_heading", "Benchmark")
                    evidence_summary = (
                        f"Retrieved {len(retrieved)} benchmark precedent clauses "
                        f"(top similarity: {max(sims):.2f}, precedent type: [{top_heading}])."
                    )
            except Exception as e:
                logger.warning(f"RAG retrieval failed for clause {clause.clause_id}: {e}")
                rag_component_score = 0.0
                evidence_summary = f"RAG retrieval attempt failed ({type(e).__name__}); defaulting to 0."

        # 4. Local Qwen3 Risk Explanation Signal (or explicit skipped status if skip_llm=True)
        if skip_llm:
            llm_score = 0.0
            explanation = None
            key_factors = [r.description for r in rule_matches] if rule_matches else [f"Category: {clause_type}"]
            uncertainty = "Qwen3 inference was intentionally skipped as clause did not require deep evaluation."
            llm_status = LLMInferenceStatus.SKIPPED
        else:
            llm_score, explanation, key_factors, uncertainty, llm_status = self._get_llm_risk_explanation(
                clause_text=clause_text,
                clause_type=clause_type,
                confidence=confidence,
                rule_matches=rule_matches,
                evidence_summary=evidence_summary
            )

        if intra_conflicts:
            for ic in intra_conflicts:
                key_factors.insert(0, f"Contradiction: {ic.conflict_type} ({ic.explanation})")

        # 5. Deterministic Hybrid Score Calculation
        score_breakdown = self.scorer.compute_hybrid_score(
            bert_score=bert_component_score,
            rule_score=rule_component_score,
            rag_score=rag_component_score,
            llm_score=llm_score
        )

        risk_level = self.scorer.determine_risk_level(
            score=score_breakdown.final_score,
            rule_matches=rule_matches,
            clause_type=clause_type
        )

        return RiskAssessment(
            assessment_id=assessment_id,
            document_id=document_id,
            clause_id=clause.clause_id,
            clause_number=clause.clause_number,
            clause_heading=clause.clause_heading,
            clause_text=clause.clause_text,
            clause_type=clause_type,
            bert_confidence=confidence,
            is_uncertain_classification=is_uncertain,
            display_category=display_category,
            risk_category=primary_category,
            risk_score=score_breakdown.final_score,
            risk_level=risk_level,
            score_breakdown=score_breakdown,
            detected_rules=rule_matches,
            intra_clause_contradictions=intra_conflicts,
            risk_explanation=explanation,
            llm_inference_status=llm_status,
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
        max_deep_clauses: Optional[int] = None,
        progress_callback: Optional[Any] = None,
        skip_llm: bool = False
    ) -> ContractRiskSummary:
        """
        Analyze all clauses in a SegmentationResult and produce a ContractRiskSummary.
        Executes two-stage optimized inference:
        Stage 1: Fast deterministic evaluation over all clauses (0 LLM calls).
        Stage 2: Candidate filtering (HIGH/MEDIUM risk, up to max_deep_clauses).
        Stage 3: Deep unified Qwen3 analysis (risk explanation + future scenario in 1 call).
        Stage 4: Recalculate hybrid scores and aggregate contract risk.
        """
        max_deep = 0 if skip_llm else (max_deep_clauses if max_deep_clauses is not None else self.max_deep_clauses)
        t0 = time.perf_counter()

        assessments: List[RiskAssessment] = []
        doc_id = segmentation_result.document_id
        source_name = segmentation_result.source_filename

        # Stage 1: Fast Deterministic Evaluation (0 LLM calls for all clauses)
        t_fast_start = time.perf_counter()

        # Batch predict all clauses with BERT for significant inference speedup
        t_bert_start = time.perf_counter()
        if progress_callback:
            try:
                progress_callback(2, 37, "Clause classification")
            except Exception:
                pass
        if predicted_clause_types is None and self.bert_classifier is not None and hasattr(self.bert_classifier, "predict_clauses_batch"):
            try:
                texts = [c.clause_text for c in segmentation_result.clauses]
                batch_preds = self.bert_classifier.predict_clauses_batch(texts)
                predicted_clause_types = {
                    c.clause_id: pred
                    for c, pred in zip(segmentation_result.clauses, batch_preds)
                }
            except Exception as e:
                logger.warning(f"Batch BERT prediction failed; falling back to per-clause: {e}")
        bert_batch_time = time.perf_counter() - t_bert_start

        # Stage 2: Risk detection (Rule Matching & Evidence Preparation)
        if progress_callback:
            try:
                progress_callback(3, 50, "Risk detection")
            except Exception:
                pass

        # Stage 3: Batch retrieve RAG evidence for all clauses in a single vectorized pass
        t_rag_batch_start = time.perf_counter()
        if progress_callback:
            try:
                progress_callback(4, 62, "Evidence retrieval")
            except Exception:
                pass
        batch_evidence_map: Dict[str, List[Dict[str, Any]]] = {}
        if self.rag_pipeline is not None and hasattr(self.rag_pipeline, "retriever") and hasattr(self.rag_pipeline.retriever, "retrieve_evidence_batch"):
            try:
                all_clause_texts = [c.clause_text.strip() for c in segmentation_result.clauses]
                batch_ev_results = self.rag_pipeline.retriever.retrieve_evidence_batch(
                    queries=all_clause_texts,
                    top_k=3,
                    similarity_threshold=0.40
                )
                for clause_obj, retrieved_list in zip(segmentation_result.clauses, batch_ev_results):
                    c_ev_items: List[Dict[str, Any]] = []
                    for item in retrieved_list:
                        sim = float(getattr(item, "similarity_score", 0.5))
                        c_ev_items.append({
                            "clause_id": getattr(item, "clause_id", "Precedent"),
                            "source_clause_id": getattr(item, "clause_id", "Precedent"),
                            "document_id": getattr(item, "document_id", "reference_corpus"),
                            "clause_number": getattr(item, "clause_number", None),
                            "clause_heading": getattr(item, "clause_heading", "Precedent"),
                            "clause_text": getattr(item, "clause_text", ""),
                            "source_pages": getattr(item, "source_pages", [1]),
                            "similarity_score": round(sim, 4),
                        })
                    batch_evidence_map[clause_obj.clause_id] = c_ev_items
            except Exception as e:
                logger.warning(f"Batch RAG retrieval failed; falling back to per-clause retrieval: {e}")
        rag_batch_time = time.perf_counter() - t_rag_batch_start

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
                skip_llm=True,
                pre_retrieved_evidence=batch_evidence_map.get(clause.clause_id)
            )
            assessments.append(assessment)
        fast_pass_time = time.perf_counter() - t_fast_start
        total_clauses = len(assessments)

        # Stage 2: Filter HIGH and MEDIUM Risk Candidate Clauses & Contradictions
        candidates = [
            a for a in assessments
            if a.risk_level in (RiskLevel.HIGH, RiskLevel.MEDIUM)
            or len(getattr(a, "intra_clause_contradictions", [])) > 0
            or len(a.detected_rules) > 0
        ]

        if len(candidates) > max_deep:
            candidates_to_analyze = sorted(candidates, key=lambda a: a.risk_score, reverse=True)[:max_deep]
        else:
            candidates_to_analyze = candidates

        # Stage 3: Deep LLM Analysis (Unified Single Call per candidate)
        t_deep_start = time.perf_counter()
        if progress_callback:
            try:
                progress_callback(5, 75, "Risk explanation")
            except Exception:
                pass
        qwen_calls_count = 0

        lm_studio_online = False if skip_llm else self.generator.is_available(timeout=0.8)
        if not lm_studio_online:
            if not skip_llm and candidates_to_analyze:
                logger.info(
                    f"[QWEN3] LM Studio server is offline or unreachable. "
                    f"Marking {len(candidates_to_analyze)} candidates as UNAVAILABLE."
                )
            for candidate in candidates_to_analyze:
                candidate.llm_inference_status = LLMInferenceStatus.UNAVAILABLE if not skip_llm else LLMInferenceStatus.SKIPPED
                candidate.risk_explanation = None
                candidate.future_scenario = None
                candidate.uncertainty = (
                    "LM Studio server is offline; Qwen3 inference was unavailable."
                    if not skip_llm else
                    "Qwen3 inference was intentionally skipped as clause did not require deep evaluation."
                )
        else:
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
                    candidate.llm_inference_status = LLMInferenceStatus.SUCCESS
                    # Recompute hybrid score with real deep LLM score
                    score_breakdown = self.scorer.compute_hybrid_score(
                        bert_score=candidate.score_breakdown.bert_component,
                        rule_score=candidate.score_breakdown.rule_component,
                        rag_score=candidate.score_breakdown.rag_component,
                        llm_score=llm_score
                    )
                    candidate.risk_score = score_breakdown.final_score
                    candidate.risk_level = self.scorer.determine_risk_level(
                        candidate.risk_score, candidate.detected_rules, candidate.clause_type
                    )
                    candidate.score_breakdown = score_breakdown
                    candidate.risk_explanation = explanation
                    candidate.key_risk_factors = key_factors
                    candidate.uncertainty = uncertainty
                    candidate.future_scenario = scenario if candidate.risk_level in (RiskLevel.HIGH, RiskLevel.MEDIUM) else None

                except Exception as e:
                    logger.warning(f"Deep analysis failed for clause {candidate.clause_id}: {e}")
                    status = LLMInferenceStatus.UNAVAILABLE if isinstance(e, LMStudioConnectionError) else LLMInferenceStatus.FAILED
                    candidate.llm_inference_status = status
                    candidate.risk_explanation = None
                    candidate.future_scenario = None
                    candidate.uncertainty = f"Qwen3 deep analysis did not execute: {e}"

        deep_llm_time = time.perf_counter() - t_deep_start

        # Stage 4: Cross-Clause & Intra-Clause Contradiction Detection
        t_conflict_start = time.perf_counter()
        cross_conflicts = self.conflict_detector.detect_cross_clause_conflicts(assessments)
        intra_conflicts = self.conflict_detector.detect_intra_clause_contradictions(assessments)
        conflict_time = time.perf_counter() - t_conflict_start

        total_time = time.perf_counter() - t0
        skipped_count = total_clauses - len(candidates_to_analyze)

        # Count final risk levels
        high_cnt = sum(1 for a in assessments if a.risk_level == RiskLevel.HIGH)
        med_cnt = sum(1 for a in assessments if a.risk_level == RiskLevel.MEDIUM)
        low_cnt = sum(1 for a in assessments if a.risk_level == RiskLevel.LOW)
        norm_cnt = sum(1 for a in assessments if a.risk_level == RiskLevel.NORMAL)

        # Stage Timings dictionary
        pipeline_timings = {
            "bert_batch_time": round(bert_batch_time, 4),
            "rag_batch_time": round(rag_batch_time, 4),
            "fast_pass_duration": round(fast_pass_time, 4),
            "deep_llm_duration": round(deep_llm_time, 4),
            "conflict_detection_duration": round(conflict_time, 4),
            "total_analysis_duration": round(total_time, 4),
        }

        # Required [PERF] instrumentation
        perf_summary = (
            f"\n==================== [PERF] INFERENCE REPORT ====================\n"
            f"[PERF] Total Clauses: {total_clauses}\n"
            f"[PERF] Deep LLM Candidates: {len(candidates_to_analyze)} (HIGH: {high_cnt}, MEDIUM: {med_cnt})\n"
            f"[PERF] Low/Normal Risk Skipped (0 Qwen calls): {skipped_count}\n"
            f"[PERF] Total Qwen Calls: {qwen_calls_count}\n"
            f"[PERF] Risk Levels: NORMAL={norm_cnt}, LOW={low_cnt}, MEDIUM={med_cnt}, HIGH={high_cnt}\n"
            f"[PERF] BERT Batch Time: {bert_batch_time:.3f}s\n"
            f"[PERF] RAG Batch Retrieval: {rag_batch_time:.3f}s\n"
            f"[PERF] Fast Pass Duration: {fast_pass_time:.3f}s\n"
            f"[PERF] Deep LLM Duration: {deep_llm_time:.3f}s\n"
            f"[PERF] Conflict Detection: {conflict_time:.3f}s (Cross: {len(cross_conflicts)}, Intra: {len(intra_conflicts)})\n"
            f"[PERF] Total Analysis Duration: {total_time:.3f}s\n"
            f"================================================================="
        )
        logger.info(perf_summary)
        print(perf_summary)

        if progress_callback:
            try:
                progress_callback(6, 88, "Future scenario generation")
            except Exception:
                pass

        summary = self.scorer.aggregate_contract_risk(
            document_id=doc_id,
            source_filename=source_name,
            assessments=assessments
        )
        summary.cross_clause_conflicts = cross_conflicts
        summary.intra_clause_contradictions = intra_conflicts
        summary.pipeline_timings = pipeline_timings

        summary.combined_scenario = None
        if lm_studio_online and len(candidates_to_analyze) > 0:
            try:
                summary.combined_scenario = self.scenario_predictor.predict_combined_scenario(
                    assessments=assessments,
                    document_id=doc_id
                )
            except Exception as e:
                logger.warning(f"Combined scenario generation failed: {e}")
                summary.combined_scenario = None

        if progress_callback:
            try:
                progress_callback(7, 95, "Final analysis")
            except Exception:
                pass

        return summary

    def _get_llm_risk_explanation(
        self,
        clause_text: str,
        clause_type: str,
        confidence: float,
        rule_matches: List[RiskRuleMatch],
        evidence_summary: str
    ) -> Tuple[float, Optional[str], List[str], str, LLMInferenceStatus]:
        """Query Qwen3 via LMStudio or return actual inference status."""
        key_factors = [r.description for r in rule_matches] if rule_matches else [f"Category: {clause_type}"]

        if not self.generator.is_available(timeout=1.0):
            return (
                0.0,
                None,
                key_factors,
                "LM Studio server is offline or unreachable; Qwen3 inference was unavailable.",
                LLMInferenceStatus.UNAVAILABLE
            )

        rule_str = ", ".join([f"{r.rule_id} ({r.description})" for r in rule_matches]) or "None"

        eval_system_prompt = (
            "You are ContractRisk AI's Legal Risk Evaluator.\n"
            "STRICT GROUNDING & ANTI-HALLUCINATION RULES:\n"
            "1. Base all factual statements strictly on the supplied clause text.\n"
            "2. DO NOT infer 'unlimited liability' or uncapped exposure unless the clause text explicitly states unlimited liability or uncapped damages.\n"
            "3. DO NOT infer breach of contract, illegality, unenforceability, damages entitlement, or legal invalidity unless explicitly supported by the clause text.\n"
            "4. DO NOT convert the absence of a limitation or liability cap into proof of unlimited liability.\n"
            "5. If the clause text contains routine, administrative, or non-risky terms, assign a low llm_score (0-20) and state that the clause represents standard/routine terms without significant legal risk.\n"
            "6. Preserve uncertainty where the clause text is silent or incomplete.\n"
            "7. Return ONLY a valid JSON object matching this schema:\n"
            "{\n"
            '  "llm_score": <number 0-100>,\n'
            '  "risk_explanation": "<Detailed grounded explanation>",\n'
            '  "key_risk_factors": ["<factor 1>", ...],\n'
            '  "uncertainty": "<analytical uncertainty>"\n'
            "}"
        )

        user_context = (
            f"TARGET CONTRACTUAL EVIDENCE:\n"
            f"Clause Text: {clause_text}\n"
            f"BERT Clause Category: {clause_type} (Confidence: {confidence:.2f})\n"
            f"Detected Rule Matches: {rule_str}\n"
            f"Benchmark Evidence: {evidence_summary}\n\n"
            f"Evaluate the contractual risk and generate the required JSON now:"
        )

        try:
            raw_response = self.generator.generate(
                query="Assess contract clause risk.",
                context=user_context,
                system_prompt=eval_system_prompt,
                max_tokens=800,
                timeout=30,
            )
            # Parse extracted JSON fields
            llm_score = float(raw_response.get("llm_score", 50.0))
            llm_score = round(max(0.0, min(100.0, llm_score)), 2)
            explanation = str(raw_response.get("risk_explanation", "")).strip() or None
            parsed_factors = list(raw_response.get("key_risk_factors", []))
            if parsed_factors:
                key_factors = parsed_factors
            uncertainty = str(raw_response.get("uncertainty", "Grounded analysis subject to user verification.")).strip()

            return llm_score, explanation, key_factors, uncertainty, LLMInferenceStatus.SUCCESS

        except Exception as e:
            logger.warning(f"Qwen3 generation failed: {e}")
            status = LLMInferenceStatus.UNAVAILABLE if isinstance(e, LMStudioConnectionError) else LLMInferenceStatus.FAILED
            return (
                0.0,
                None,
                key_factors,
                f"Qwen3 inference did not execute ({type(e).__name__}): {e}",
                status
            )
