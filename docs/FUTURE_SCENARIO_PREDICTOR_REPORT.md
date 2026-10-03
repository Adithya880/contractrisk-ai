# Phase 7.2 & 7.2.1 Future Scenario Predictor Technical Report

> **System**: ContractRisk AI  
> **Module**: Phase 7.2 & Phase 7.2.1 Grounding-Hardening Pass — Future Scenario Predictor  
> **Status**: COMPLETE  
> **Target Execution Boundary**: Phase 7.2 / 7.2.1 ONLY (Phase 8+ excluded)  

---

## 1. Purpose & Overview

The **Future Scenario Predictor** is a decision-support module that consumes a Phase 7.1 `RiskAssessment` and generates an evidence-grounded hypothetical future scenario explaining what could happen if the identified contractual risk is triggered or remains unaddressed.

### Core Objectives & Hardening Rules (Phase 7.2.1)
1. **Evidence-Grounded Prediction**: Every scenario is traceable strictly to contractual text and retrieved evidence.
2. **Anti-Hallucination Directives**: Prohibits inventing specific unmentioned entities, monetary amounts (e.g. "$10M"), specific unmentioned notice windows (e.g. "60 days"), specific unmentioned products, or ungrounded industry contexts absent from the clause text.
3. **Plausible Trigger Identification**: Identifies specific events (e.g. breach notice, third-party claim, market change) that could activate the risk.
4. **Conditional Phrasing**: Enforces strict conditional phrasing (e.g., *"If a claim were to arise..."*, *"Should a dispute occur..."*) to prevent presenting hypothetical outcomes as guaranteed facts.
5. **Separation of Facts & Assumptions**: Explicitly isolates contractual facts from necessary analytical assumptions in a dedicated array.
6. **Preserve Uncertainty**: Flags missing parameters, unstated monetary limits, or jurisdiction ambiguities in the `uncertainty` field.
7. **Phase 7.1 Score Isolation**: The Phase 7.1 hybrid risk scoring formula ($0.30 \times S_{\text{bert}} + 0.35 \times S_{\text{rule}} + 0.15 \times S_{\text{rag}} + 0.20 \times S_{\text{llm}}$) and risk level thresholds remain **100% untouched**.

---

## 2. Architecture & Pipeline Integration

The predictor operates downstream from Phase 7.1 Risk Analysis:

```
Contract Clause
      ↓
Phase 7.1 Hybrid Risk Assessment (Score, Level, Rules, BERT, Evidence)
      ↓
FutureScenarioPredictor (Grounding Validation & Anti-Hallucination Checks)
      ↓
Local Qwen3 LLM (LM Studio http://127.0.0.1:1234/v1)
      ↓
FutureScenario (Structured Output & Citations)
```

### Module Location
- `src/risk_analysis/scenario_models.py`: Defines the `FutureScenario` Pydantic v2 data model.
- `src/risk_analysis/scenario_predictor.py`: Implements `FutureScenarioPredictor` handling prompting, JSON validation, anti-hallucination constraints, and conservative fallback execution.

---

## 3. Input & Output Schemas

### Input Data (`RiskAssessment`)
The predictor consumes existing Phase 7.1 and Phase 7 models without duplicating data structures:
- `clause_id`, `clause_number`, `clause_text`
- `clause_type` (BERT prediction & confidence)
- `risk_category` & `risk_level`
- `risk_score` & `score_breakdown`
- `detected_rules` (regex rule matches)
- `evidence` & `source_pages` (provenance)

### Output Schema (`FutureScenario` Pydantic Model)

```python
class FutureScenario(BaseModel):
    scenario_id: str
    clause_id: str
    clause_number: Optional[str] = None
    scenario_title: str
    trigger_condition: str
    scenario_description: str
    possible_consequence: str
    supporting_evidence: List[Citation]
    assumptions: List[str]
    uncertainty: str
    fallback_active: bool = False
    disclaimer: str
```

---

## 4. Grounding & Anti-Hallucination Prompt Strategy

The predictor queries the local Qwen3 model (`qwen3-4b-instruct-2507`) via LM Studio using `LLMGenerator`. The prompt enforces strict anti-hallucination directives:

1. **Strict Evidence Base**: Base the scenario ONLY on supplied contractual evidence.
2. **No Invented Specific Facts**: Do NOT invent dollar amounts, specific dates, notice days, or unmentioned industry topics.
3. **Conditional Phrasing**: Every hypothetical trigger event MUST be phrased conditionally ("If a claim were to arise...").
4. **Fact vs. Assumption Isolation**: Keep assumptions strictly in the `assumptions` array.
5. **Explicit Uncertainty**: Document unstated caps, unstated notice periods, or jurisdictional ambiguity.
6. **JSON Only Output**: Return raw JSON matching the required schema.

---

## 5. Validation & Failure Handling

`FutureScenarioPredictor` implements robust error handling to ensure LLM failures never crash the risk analysis pipeline:

| Error Case | System Behavior |
| :--- | :--- |
| **Valid JSON** | Parsed directly into `FutureScenario` Pydantic model with verified citations |
| **Non-Conditional Trigger** | Automatically formatted to prepend conditional phrasing |
| **Unstated Financial Cap** | Enriches `uncertainty` field flagging unstated monetary limit in clause text |
| **Malformed/Invalid JSON** | Triggers `_build_fallback_scenario()`, returning conservative fallback (`fallback_active=True`) |
| **LM Studio Offline / HTTP Error** | Catches `Exception` and executes safe fallback scenario |
| **Low Risk Baseline (<30 Score)** | Executes fast deterministic low-risk baseline without invoking LLM call |

---

## 6. Verification & Test Results

### 1. Phase 7.2 / 7.2.1 Unit Tests (`pytest tests/test_scenario_predictor.py -v`)
- `test_predict_scenario_high_risk_mocked_llm`: **PASSED**
- `test_predict_scenario_medium_risk_mocked_llm`: **PASSED**
- `test_predict_scenario_low_risk_baseline`: **PASSED**
- `test_predict_scenario_malformed_llm_json_fallback`: **PASSED**
- `test_predict_scenario_connection_error_fallback`: **PASSED**
- `test_enforce_conditional_phrasing_on_trigger`: **PASSED**
- `test_uncertainty_preservation_on_ambiguous_clause`: **PASSED**
- `test_anti_hallucination_fact_assumption_isolation`: **PASSED**
- **Unit Test Summary**: **8 / 8 PASSED**

### 2. Live Qwen3 Smoke Test Script (`scripts/test_scenario_predictor.py`)
- Executed full scenario prediction on synthetic contract clauses against live Qwen3 on LM Studio.
- **Results**: Successfully generated grounded, non-hallucinated scenarios across High, Medium, Low risk, insufficient evidence, and malformed LLM response cases.

### 3. Full Regression Suite (Phases 4–7.2.1)
- Executed `pytest tests/ -v`.
- **Regression Summary**: **83 / 83 PASSED** ($100\%$ pass rate across Phase 4, 5, 6, 7, 7.1, 7.2, and 7.2.1).
- **Phase 7.1 Regression Intact**: Zero modifications were made to completed Phase 1–7.1 code.

---

## 7. Real Grounded Qwen3 Scenario Example

Below is an actual output generated by Qwen3 (`qwen3-4b-instruct-2507`) during the Phase 7.2.1 live smoke test for a HIGH-risk clause:

```
======================================================================
 FUTURE SCENARIO PREDICTOR -- [CASE 1: HIGH RISK CLAUSE]
======================================================================
Clause        : 14.2 — Limitation of Liability & Indemnification
Clause ID     : clause_142
Risk Level    : HIGH
Risk Score    : 78.74 / 100.0
BERT Category : Uncapped Liability
Fallback Active: False
----------------------------------------------------------------------

Scenario Title:
  Uncapped Liability Exposure Under Broad Indemnification Terms

Trigger Condition:
  If a dispute were to arise regarding the performance of contractual obligations or if Vendor were to exercise its unilateral right to terminate the agreement for convenience without cause

Scenario Description:
  Should a third-party claim be brought against the Vendor, Clause 14.2 requires the Customer to defend, indemnify, and hold harmless the Vendor from all claims, damages, and costs. Because the clause contains no cap on indemnification obligations, the Customer could be obligated to absorb the full financial burden of the dispute. Simultaneously, the Vendor could terminate the agreement for convenience, leaving the Customer with ongoing financial liabilities.

Possible Consequence:
  Vendor may face significant financial or operational exposure due to broad indemnification obligations and lack of defined liability caps, even though it is restricted from unlimited liability under the clause.

Supporting Evidence (1 Citations):
  * [clause_142] Clause 14.2 (Pages: [5])

Assumptions:
  - A dispute arises regarding the performance of contractual obligations
  - Vendor exercises its unilateral right to terminate for convenience without cause
  - Customer fulfills its obligation to defend, indemnify, and hold harmless Vendor as required by the clause

Uncertainty:
  The clause does not specify any monetary cap on liability or define what constitutes 'all claims, damages, and costs,' creating ambiguity about the scope and potential financial impact of the indemnification obligation. Additionally, no jurisdictional context or governing law is provided to assess enforceability or limits. Specific financial limit is unstated in clause text.
======================================================================
```

---

## 8. Technical Limitations & Disclaimer

1. **Hypothetical Decision Support**: Generated scenarios are decision-support signals illustrating potential risk trajectories. They are **NOT** guaranteed predictions or legal advice.
2. **Predictive Evaluation**: Predictive accuracy has not been validated against an empirical historical litigation dataset.
