"""
Future Scenario Predictor Module for Phase 7.2 / Phase 7.2.1 Grounding-Hardening Pass.
Consumes Phase 7.1 RiskAssessment objects and generates strictly evidence-grounded
hypothetical future risk scenarios using local Qwen3 model via LM Studio.
"""

import uuid
import json
import re
from typing import List, Optional, Dict, Any, Tuple
from pydantic import ValidationError

from src.rag.generator import LLMGenerator
from src.rag.models import Citation
from src.risk_analysis.models import RiskAssessment, RiskLevel, ContractRiskSummary, RiskCategory
from src.risk_analysis.scenario_models import FutureScenario


SCENARIO_SYSTEM_PROMPT = """You are ContractRisk AI's Future Scenario Predictor.
Your task is to analyze the supplied contract clause and risk assessment data to generate a plausible, hypothetical future scenario explaining what could happen if the identified contractual risk is triggered or remains unaddressed.

STRICT GROUNDING & ANTI-HALLUCINATION RULES:
1. BASE SCENARIO STRICTLY ON SUPPLIED EVIDENCE: Use ONLY facts, categories, and terms directly stated in the supplied clause text or benchmark evidence.
2. DO NOT INVENT SPECIFIC UNMENTIONED FACTS: Do NOT invent specific unmentioned dollar amounts (e.g. "$10M"), specific unmentioned notice periods (e.g. "60 days", "30 days" unless stated in clause), specific unmentioned industries, specific unmentioned products (e.g. "environmental contamination"), or specific unmentioned entities.
3. CONDITIONAL PHRASING FOR HYPOTHETICAL EVENTS: Every unsupported future event or trigger MUST be phrased conditionally (e.g. "If a claim were to arise...", "Should a dispute occur regarding..."). NEVER state hypothetical future events as established facts.
4. ISOLATE FACTS FROM ASSUMPTIONS: Keep contractual facts in the narrative text, and place all hypothetical premises strictly in the 'assumptions' array.
5. PRESERVE UNCERTAINTY: If the clause text or evidence is missing specific parameters (such as monetary caps, notice windows, or jurisdiction), explicitly document this ambiguity in the 'uncertainty' field.
6. KEEP FACTUAL TRIGGERS FACTUAL: Do NOT rewrite factual conditions (such as 'payment becomes overdue' or 'prices are altered') as legal conclusions (such as 'a breach of contract occurs' or 'unlawful breach') unless the clause text itself explicitly characterizes the event as a breach.
7. RETURN ONLY VALID JSON: Return ONLY a valid JSON object matching the required structure.

REQUIRED JSON FORMAT:
{
  "scenario_title": "<Concise title grounded in clause category and risk level>",
  "trigger_condition": "<Conditional triggering event (e.g. 'If payment were to become overdue under Clause...')>",
  "scenario_description": "<Grounded narrative using conditional phrasing for future developments>",
  "possible_consequence": "<Potential legal, financial, or operational impact>",
  "assumptions": ["<Assumption 1>", "<Assumption 2>"],
  "uncertainty": "<Statement of missing context, ambiguity, or analytical uncertainty>"
}
"""

UNIFIED_DEEP_SYSTEM_PROMPT = """You are ContractRisk AI's Senior Legal Risk Evaluator & Future Scenario Predictor.
Your task is to analyze the supplied contract clause, classification data, and detected risk patterns to perform a unified evaluation:
1. Explain why the clause poses a legal or commercial risk and score the risk severity (0-100).
2. Generate a plausible, hypothetical future scenario explaining what could happen if the risk is triggered or remains unaddressed.

STRICT GROUNDING & ANTI-HALLUCINATION RULES:
1. BASE EVALUATION STRICTLY ON SUPPLIED EVIDENCE: Use ONLY facts, categories, and terms directly stated in the clause text or benchmark evidence.
2. DO NOT INVENT SPECIFIC UNMENTIONED FACTS: Do NOT invent unmentioned causes of action (e.g. "product defect", "third-party claim", "punitive damages", "injuries", "regulatory penalties"), unmentioned dollar figures (e.g. "$10M"), unmentioned notice periods (e.g. "60 days", "30 days" unless stated in clause), unmentioned entities, or unmentioned products.
3. PRESERVATION CARVE-OUTS ARE NOT EXCLUSIONS: If a clause states "Nothing in these terms shall exclude or limit liability for [death/injury/fraud]", that clause PRESERVES liability for that issue. Do NOT mischaracterize it as excluding or waiving liability.
4. CONDITIONAL PHRASING FOR HYPOTHETICAL EVENTS: Every future scenario trigger or development MUST be phrased conditionally (e.g. "If a claim were to arise...", "Should a dispute occur regarding..."). Never state hypothetical future events as established facts.
5. ISOLATE FACTS FROM ASSUMPTIONS: Keep factual clause references in the description, and place all hypothetical premises strictly in the 'assumptions' array.
6. PRESERVE UNCERTAINTY: If the clause text is ambiguous or silent on specific terms (such as monetary caps, notice windows, or governing law), explicitly document this in 'uncertainty'.
7. KEEP FACTUAL TRIGGERS FACTUAL: Do not characterize events as breaches unless explicitly stated in the clause text.
8. RETURN ONLY VALID JSON: Return ONLY a valid JSON object matching the required structure.

REQUIRED JSON FORMAT:
{
  "llm_score": <number 0-100 indicating risk severity>,
  "risk_explanation": "<Detailed grounded explanation of the specific risk posed by the clause>",
  "key_risk_factors": ["<Risk factor 1>", "<Risk factor 2>"],
  "scenario_title": "<Concise title grounded in clause category and risk level>",
  "trigger_condition": "<Conditional triggering event (e.g. 'If payment were to become overdue under Clause...')>",
  "scenario_description": "<Grounded narrative using conditional phrasing for future developments>",
  "possible_consequence": "<Potential legal, financial, or operational impact>",
  "assumptions": ["<Assumption 1>", "<Assumption 2>"],
  "uncertainty": "<Statement of missing context, ambiguity, or analytical uncertainty>"
}
"""


class FutureScenarioPredictor:
    """
    Predictor module generating strictly evidence-grounded future risk scenarios for contract clauses.
    """

    def __init__(self, generator: Optional[LLMGenerator] = None):
        """Initialize scenario predictor with LLM generator."""
        self.generator = generator or LLMGenerator()

    def predict_scenario(self, assessment: RiskAssessment) -> FutureScenario:
        """
        Generate a validated FutureScenario for a given RiskAssessment.
        Reuses pre-computed unified scenario if already present on the assessment.
        """
        if getattr(assessment, "future_scenario", None) is not None:
            return assessment.future_scenario

        scenario_id = f"scen_{uuid.uuid4().hex[:8]}"

        # 1. Build Citation objects from assessment provenance
        citations = self._build_citations_from_assessment(assessment)

        # 2. Construct prompt for Qwen3 (always attempt LLM generation for grounded scenario)
        context_prompt = self._build_scenario_prompt(assessment)

        # 3. Query local Qwen3 model
        try:
            raw_json = self.generator.generate(
                query="Generate grounded future risk scenario.",
                context=context_prompt
            )
            # Validate JSON structure & enforce strict grounding constraints via Pydantic
            scenario = self._parse_and_validate_response(
                raw_json=raw_json,
                scenario_id=scenario_id,
                assessment=assessment,
                citations=citations
            )
            return scenario

        except Exception as e:
            # Conservative fallback execution if LLM fails, times out, or returns unparseable JSON
            return self._build_fallback_scenario(
                scenario_id=scenario_id,
                assessment=assessment,
                citations=citations,
                error_message=str(e)
            )

    def predict_document_scenarios(self, summary: ContractRiskSummary) -> List[FutureScenario]:
        """
        Generate future scenarios for all highest-risk clause assessments in a contract summary.

        Args:
            summary: ContractRiskSummary from Phase 7.1.

        Returns:
            List of FutureScenario models for top risk assessments.
        """
        scenarios: List[FutureScenario] = []
        for assessment in summary.highest_risk_assessments:
            scenario = self.predict_scenario(assessment)
            scenarios.append(scenario)
        return scenarios

    def predict_deep_scenario_and_explanation(
        self,
        clause_id: str,
        clause_number: Optional[str],
        clause_heading: Optional[str],
        clause_text: str,
        clause_type: str,
        bert_confidence: float,
        risk_category: RiskCategory,
        detected_rules: list,
        evidence_summary: str,
        citations: List[Citation]
    ) -> Tuple[float, str, List[str], str, FutureScenario]:
        """
        Execute unified single-shot Qwen3 generation producing both risk explanation
        and grounded future scenario for high/medium risk candidate clauses.
        """
        scenario_id = f"scen_{uuid.uuid4().hex[:8]}"
        rules_str = ", ".join([f"[{r.rule_id}] {r.description} (Severity: {r.severity_weight})" for r in detected_rules]) or "None"

        context_prompt = (
            f"{UNIFIED_DEEP_SYSTEM_PROMPT}\n\n"
            f"--- TARGET CONTRACTUAL EVIDENCE ---\n"
            f"Clause ID: {clause_id}\n"
            f"Clause Number: {clause_number or 'N/A'}\n"
            f"Clause Heading: {clause_heading or 'Untitled'}\n"
            f"Clause Text: {clause_text}\n"
            f"BERT Category: {clause_type} (Confidence: {bert_confidence:.2f})\n"
            f"Detected Rules: {rules_str}\n"
            f"Benchmark Evidence: {evidence_summary}\n\n"
            f"Generate the unified risk evaluation and grounded future scenario JSON now:"
        )

        try:
            raw_json = self.generator.generate(
                query="Perform unified deep risk and scenario evaluation.",
                context=context_prompt
            )
            llm_score = float(raw_json.get("llm_score", 50.0))
            llm_score = round(max(0.0, min(100.0, llm_score)), 2)
            explanation = str(raw_json.get("risk_explanation") or "Risk analysis generated by local Qwen3 model.").strip()
            key_factors = list(raw_json.get("key_risk_factors", []))
            if not key_factors and detected_rules:
                key_factors = [r.description for r in detected_rules]
            uncertainty = str(raw_json.get("uncertainty") or "Grounded analysis subject to user verification.").strip()

            class _AssessAdapter:
                def __init__(self, **kwargs):
                    self.__dict__.update(kwargs)

            adapter = _AssessAdapter(
                clause_id=clause_id,
                clause_number=clause_number,
                clause_heading=clause_heading,
                clause_text=clause_text,
                clause_type=clause_type,
                risk_category=risk_category,
                risk_explanation=explanation
            )

            scenario = self._parse_and_validate_response(
                raw_json=raw_json,
                scenario_id=scenario_id,
                assessment=adapter,
                citations=citations
            )
            return llm_score, explanation, key_factors, uncertainty, scenario

        except Exception as e:
            heuristic_llm_score = 0.0
            if detected_rules:
                heuristic_llm_score = max(r.severity_weight for r in detected_rules)
            else:
                heuristic_llm_score = 50.0
            heuristic_llm_score = round(max(0.0, min(100.0, heuristic_llm_score)), 2)

            explanation = (
                f"Automated risk explanation (fallback mode active): Clause evaluated under "
                f"{clause_type} category with {len(detected_rules)} rule match(es)."
            )
            key_factors = [r.description for r in detected_rules] if detected_rules else [f"Category: {clause_type}"]
            uncertainty = f"Fallback mode active ({type(e).__name__}); local LLM generation was not executed."

            class _AssessAdapterFallback:
                def __init__(self, **kwargs):
                    self.__dict__.update(kwargs)

            adapter_fallback = _AssessAdapterFallback(
                clause_id=clause_id,
                clause_number=clause_number,
                clause_heading=clause_heading,
                clause_text=clause_text,
                clause_type=clause_type,
                risk_category=risk_category,
                risk_level=RiskLevel.MEDIUM,
                risk_score=heuristic_llm_score,
                risk_explanation=explanation,
                detected_rules=detected_rules
            )

            fallback_scenario = self._build_fallback_scenario(
                scenario_id=scenario_id,
                assessment=adapter_fallback,
                citations=citations,
                error_message=str(e)
            )
            return heuristic_llm_score, explanation, key_factors, uncertainty, fallback_scenario

    def _build_scenario_prompt(self, assessment: RiskAssessment) -> str:
        """Construct detailed evidence prompt for Qwen3."""
        rules_str = ", ".join([f"[{r.rule_id}] {r.description} (Severity: {r.severity_weight})" for r in assessment.detected_rules]) or "None"
        evidence_str = assessment.evidence_summary or "No benchmark evidence."

        return (
            f"{SCENARIO_SYSTEM_PROMPT}\n\n"
            f"--- TARGET CONTRACTUAL EVIDENCE ---\n"
            f"Clause ID: {assessment.clause_id}\n"
            f"Clause Number: {assessment.clause_number or 'N/A'}\n"
            f"Clause Heading: {assessment.clause_heading or 'Untitled'}\n"
            f"Clause Text: {assessment.clause_text}\n"
            f"BERT Category: {assessment.clause_type} (Confidence: {assessment.bert_confidence:.2f})\n"
            f"Primary Risk Category: {assessment.risk_category.value}\n"
            f"Risk Level: {assessment.risk_level.value} (Hybrid Score: {assessment.risk_score:.2f})\n"
            f"Detected Rules: {rules_str}\n"
            f"Benchmark Evidence: {evidence_str}\n"
            f"Risk Explanation Summary: {assessment.risk_explanation}\n\n"
            f"Generate the grounded hypothetical future scenario JSON now:"
        )

    def _parse_and_validate_response(
        self,
        raw_json: Dict[str, Any],
        scenario_id: str,
        assessment: RiskAssessment,
        citations: List[Citation]
    ) -> FutureScenario:
        """Parse raw LLM output dictionary into FutureScenario Pydantic model with grounding checks."""
        if not isinstance(raw_json, dict):
            raise ValueError(f"LLM output must be a JSON dict, got {type(raw_json)}")

        title = str(raw_json.get("scenario_title") or f"Potential {assessment.risk_category.value} Exposure").strip()
        trigger = str(raw_json.get("trigger_condition") or "Contractual disagreement or performance failure").strip()
        desc = str(raw_json.get("scenario_description") or assessment.risk_explanation).strip()
        consequence = str(raw_json.get("possible_consequence") or "Potential financial or operational impact").strip()

        # Enforce conditional phrasing on trigger condition if missing
        if not any(cond in trigger.lower() for cond in ["if", "should", "in the event", "were to"]):
            trigger = f"If a dispute or trigger event were to occur regarding: {trigger}"

        raw_assumptions = raw_json.get("assumptions", [])
        if isinstance(raw_assumptions, list):
            assumptions = [str(a).strip() for a in raw_assumptions if str(a).strip()]
        else:
            assumptions = [str(raw_assumptions).strip()]

        if not assumptions:
            assumptions = ["Contract provisions enforced according to literal terms under applicable law."]

        uncertainty = str(raw_json.get("uncertainty") or "Scenario is hypothetical and subject to judicial interpretation.").strip()

        # Flag missing specific context in uncertainty if clause text lacks details
        if "uncapped" in assessment.clause_type.lower() and "dollar" not in assessment.clause_text.lower():
            if "monetary limit" not in uncertainty.lower() and "unspecified" not in uncertainty.lower():
                uncertainty += " Specific financial limit is unstated in clause text."

        return FutureScenario(
            scenario_id=scenario_id,
            clause_id=assessment.clause_id,
            clause_number=assessment.clause_number,
            scenario_title=title,
            trigger_condition=trigger,
            scenario_description=desc,
            possible_consequence=consequence,
            supporting_evidence=citations,
            assumptions=assumptions,
            uncertainty=uncertainty,
            fallback_active=False
        )

    def _build_citations_from_assessment(self, assessment: RiskAssessment) -> List[Citation]:
        """Construct list of Citation objects from RiskAssessment provenance."""
        citations = []
        # Primary clause citation
        citations.append(Citation(
            clause_id=assessment.clause_id,
            clause_number=assessment.clause_number,
            source_pages=assessment.source_pages
        ))

        # Benchmark evidence citations if present
        for ev in assessment.evidence:
            ev_id = str(ev.get("clause_id", ""))
            ev_num = ev.get("clause_number")
            ev_pages = ev.get("source_pages", [])
            if ev_id and ev_id != assessment.clause_id:
                citations.append(Citation(
                    clause_id=ev_id,
                    clause_number=ev_num,
                    source_pages=ev_pages
                ))
        return citations

    def _build_low_risk_scenario(
        self,
        scenario_id: str,
        assessment: RiskAssessment,
        citations: List[Citation]
    ) -> FutureScenario:
        """Construct evidence-grounded scenario for standard contractual clauses."""
        heading_str = f"Clause {assessment.clause_number} ({assessment.clause_heading})" if assessment.clause_number else (assessment.clause_heading or "Clause")
        title = f"Potential {assessment.risk_category.value} Scenario ({heading_str})"
        desc = assessment.risk_explanation if (assessment.risk_explanation and "Automated risk explanation" not in assessment.risk_explanation) else (
            f"Under {heading_str}, provisions stipulate: '{assessment.clause_text[:120]}...'. "
            f"Contractual performance is governed by literal provisions under applicable commercial law."
        )
        return FutureScenario(
            scenario_id=scenario_id,
            clause_id=assessment.clause_id,
            clause_number=assessment.clause_number,
            scenario_title=title,
            trigger_condition=f"If performance or enforcement disputes arise under {heading_str}.",
            scenario_description=desc,
            possible_consequence=f"Contractual rights or obligations enforced under {assessment.risk_category.value} provisions (Hybrid Score: {assessment.risk_score:.2f}).",
            supporting_evidence=citations,
            assumptions=["Parties perform obligations in accordance with written contractual terms"],
            uncertainty=f"Grounded in clause text; literal enforcement subject to applicable governing law.",
            fallback_active=False
        )

    def _build_fallback_scenario(
        self,
        scenario_id: str,
        assessment: RiskAssessment,
        citations: List[Citation],
        error_message: str
    ) -> FutureScenario:
        """Construct conservative fallback FutureScenario when LLM generation fails or returns invalid output."""
        rule_desc = assessment.detected_rules[0].description if assessment.detected_rules else f"Category: {assessment.risk_category.value}"

        return FutureScenario(
            scenario_id=scenario_id,
            clause_id=assessment.clause_id,
            clause_number=assessment.clause_number,
            scenario_title=f"Hypothetical {assessment.risk_category.value} Risk Scenario (Fallback)",
            trigger_condition=f"If an unaddressed risk trigger occurs related to: {rule_desc}.",
            scenario_description=(
                f"In the event of a contractual breach or dispute under Clause {assessment.clause_number or assessment.clause_id}, "
                f"the presence of '{assessment.clause_type}' terms could lead to unmitigated financial or operational exposure."
            ),
            possible_consequence=(
                f"Potential liability or operational restrictions under {assessment.risk_level.value} "
                f"risk level (Hybrid Score: {assessment.risk_score:.2f})."
            ),
            supporting_evidence=citations,
            assumptions=[
                "Contract provisions enforced according to literal terms",
                "Fallback mode active due to offline/invalid LLM generation"
            ],
            uncertainty=f"Fallback execution mode active ({error_message[:100]}); score and scenario derived from rule engine.",
            fallback_active=True
        )
