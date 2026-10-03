# Phase 7.1 Hybrid Risk Detection & Risk Scoring Technical Report

> **System**: ContractRisk AI  
> **Module**: Phase 7.1 — Deterministic Hybrid Risk Analysis Pipeline  
> **Status**: COMPLETE  
> **Target Execution Boundary**: Phase 7.1 ONLY (Phase 7.2 & Phase 8+ excluded)  

---

## 1. Executive Summary

Phase 7.1 introduces **Hybrid Risk Detection & Risk Scoring** to **ContractRisk AI**. It converts contract clauses into quantifiable, verifiable risk assessments by combining:
1. **Phase 3 BERT Clause Classification** (30% weight signal)
2. **Deterministic Regex Rule Engine** (35% weight signal)
3. **Phase 6/7 RAG Benchmark Retrieval** (15% weight signal)
4. **Local Qwen3 Grounded Risk Explanation** (20% weight signal)

The hybrid risk engine outputs deterministic numerical scores ($0.0 \text{ to } 100.0$) and categorical ratings (`LOW`, `MEDIUM`, `HIGH`) for each clause and aggregates document-level risk profiles using a weighted non-linear formula.

---

## 2. BERT Clause Type Risk Mapping (`BERTRiskMapper`)

Phase 3 fine-tuned `bert-base-uncased` across 41 legal clause categories. `BERTRiskMapper` treats the predicted category as a baseline risk signal scaled by the model's softmax prediction confidence.

$$\text{BERT Component Score} = \min\left(100.0, W_{\text{base}}(\text{clause\_type}) \times \text{confidence}\right)$$

### Exact Mapping Table (41 BERT Clause Categories)

| Clause Category | Base Weight ($W_{\text{base}}$) | Primary Risk Category | Rationale |
| :--- | :---: | :--- | :--- |
| `Uncapped Liability` | **95.0** | Liability | Direct financial exposure without monetary caps |
| `Termination For Convenience` | **85.0** | Termination | Unilateral cancellation without breach |
| `Liquidated Damages` | **85.0** | Liability | Fixed financial penalty provisions |
| `Non-Compete` | **80.0** | Non-Compete | Restrictive covenants limiting business operations |
| `Exclusivity` | **80.0** | Other | Restrictive sole-provider or sole-buyer clauses |
| `Cap On Liability` | **75.0** | Liability | Monetary limit on recoverable damages |
| `Ip Ownership Assignment` | **75.0** | Intellectual Property | Transfer of intellectual property rights |
| `Joint Ip Ownership` | **70.0** | Intellectual Property | Shared IP ownership causing rights ambiguity |
| `Audit Rights` | **70.0** | Audit Rights | Operational inspection and record review burdens |
| `Most Favored Nation` | **70.0** | Payment Terms | Price matching and concession burdens |
| `Covenant Not To Sue` | **70.0** | Dispute Resolution | Waiver of right to litigate claims |
| `No-Solicit Of Customers` | **65.0** | Non-Compete | Restrictions on customer outreach |
| `No-Solicit Of Employees` | **65.0** | Non-Compete | Restrictions on hiring or soliciting staff |
| `Change Of Control` | **65.0** | Modification | Termination or approval rights upon acquisition |
| `Irrevocable Or Perpetual License` | **65.0** | Intellectual Property | Permanent license grants |
| `Price Restrictions` | **60.0** | Payment Terms | Fixed pricing or resale restrictions |
| `Revenue/Profit Sharing` | **60.0** | Payment Terms | Royalty or profit distribution obligations |
| `Minimum Commitment` | **60.0** | Payment Terms | Guaranteed minimum purchase or spend volume |
| `Unlimited/All-You-Can-Eat-License` | **60.0** | Intellectual Property | Uncapped usage license grants |
| `Notice Period To Terminate Renewal` | **55.0** | Renewal | Strict advance notice windows for non-renewal |
| `Renewal Term` | **55.0** | Renewal | Renewal duration and conditions |
| `Post-Termination Services` | **50.0** | Termination | Transition assistance obligations |
| `Rofr/Rofo/Rofn` | **50.0** | Other | Right of first refusal / option restrictions |
| `Source Code Escrow` | **50.0** | Intellectual Property | Software source code deposit requirements |
| `Non-Disparagement` | **45.0** | Confidentiality | Restrictions on public comments |
| `Competitive Restriction Exception` | **45.0** | Non-Compete | Safe harbor exceptions to non-compete |
| `Anti-Assignment` | **40.0** | Modification | Prohibition against contract transfer |
| `Non-Transferable License` | **40.0** | Intellectual Property | Prohibition against license assignment |
| `Volume Restriction` | **40.0** | Payment Terms | Usage or transaction caps |
| `Warranty Duration` | **40.0** | Warranty | Time limits on express warranties |
| `Insurance` | **35.0** | Liability | Mandatory coverage maintenance |
| `Affiliate License-Licensee` | **30.0** | Intellectual Property | Rights granted to licensee subsidiaries |
| `Affiliate License-Licensor` | **30.0** | Intellectual Property | Rights granted to licensor subsidiaries |
| `Third Party Beneficiary` | **30.0** | Other | Rights granted to non-signatories |
| `License Grant` | **25.0** | Intellectual Property | Standard scope of grant |
| `Governing Law` | **20.0** | Governing Law | Jurisdiction and choice of law |
| `Expiration Date` | **15.0** | Termination | Natural end date of contract |
| `Effective Date` | **10.0** | Other | Start date of agreement |
| `Agreement Date` | **10.0** | Other | Execution date of document |
| `Parties` | **10.0** | Other | Contracting entities |
| `Document Name` | **5.0** | Other | Title of contract document |

---

## 3. Rule Engine Architecture (`RuleEngine`)

The `RuleEngine` executes deterministic regular expression pattern matching across 16 legal risk domains. When multiple rules match a single clause, their severity weights $w_1, w_2, \dots, w_k \in [0, 100]$ are aggregated using an **asymptotic decay model** to prevent artificial score clipping:

$$S_{\text{rule}} = \min\left(100.0, 100.0 \times \left(1.0 - \prod_{i=1}^k \left(1.0 - \frac{w_i}{100.0}\right)\right)\right)$$

### Predefined Rule Categories & Severities

- **Liability**: Unlimited liability ($95.0$), Consequential damages ($85.0$), Restrictive liability cap ($70.0$)
- **Indemnification**: Broad hold harmless ($85.0$), Unilateral indemnity ($75.0$)
- **Termination**: Convenience termination ($80.0$), Abnormally short notice period ($85.0$), Unexpired term fee acceleration ($90.0$)
- **Payment Terms**: Non-refundable fees ($70.0$), High late payment interest ($75.0$)
- **Intellectual Property**: Broad IP assignment ($85.0$), Irrevocable exclusive license ($75.0$)
- **Modification**: Unilateral terms modification ($85.0$)
- **Renewal**: Automatic renewal ($60.0$)
- **Non-Compete**: Restrictive covenant ($85.0$)
- **Audit Rights**: Unrestricted audit ($75.0$)
- **Warranty**: Disclaimer of warranties ($70.0$)
- **Dispute Resolution**: Jury trial / class action waiver ($75.0$)
- **Data Privacy**: Unrestricted data processing/transfer ($85.0$)

---

## 4. Deterministic Hybrid Scoring Formula (`HybridScorer`)

To guarantee strict reproducibility and mathematical control, **local Qwen3 LLM outputs do NOT set the numerical score independently**. The final clause risk score is calculated via the fixed hybrid formula:

$$\text{Final Risk Score} = 0.30 \times S_{\text{bert}} + 0.35 \times S_{\text{rule}} + 0.15 \times S_{\text{rag}} + 0.20 \times S_{\text{llm}}$$

### Risk Rating Thresholds

| Risk Level | Score Range | Technical Meaning |
| :--- | :---: | :--- |
| **`LOW`** | $\text{Score} < 35.0$ | Low legal exposure; standard commercial language |
| **`MEDIUM`** | $35.0 \le \text{Score} < 70.0$ | Moderate risk; requires standard legal review |
| **`HIGH`** | $\text{Score} \ge 70.0$ | Severe risk indicator; requires explicit legal escalation |

### Contract-Level Risk Aggregation

A single severe clause can compromise an entire contract. Document-level risk combines the worst-case clause risk with overall contract context:

$$\text{Contract Risk Score} = 0.6 \times \max(\text{Clause Scores}) + 0.4 \times \text{mean}(\text{Clause Scores})$$

---

## 5. Local Qwen3 Grounded Risk Explanation Integration

The system queries the local Qwen3 model (`qwen3-4b-instruct-2507`) via LM Studio (`http://127.0.0.1:1234/v1`). Qwen3 provides:
1. Grounded risk explanations referencing clause text and detected rules.
2. Structured key risk factor extraction.
3. Perceived risk severity score ($S_{\text{llm}}$).
4. Explicit statements of analytical uncertainty.

### Offline & Fallback Safety

If LM Studio is unreachable or offline during runtime, `ContractRiskAnalyzer` triggers an automatic fallback mode without raising an unhandled exception:
- $S_{\text{llm}}$ defaults to rule severity or scaled BERT score.
- Qualitative explanation documents rule/category findings.
- Uncertainty field explicitly flags active fallback state (`LM Studio Offline`).

---

## 6. Verification & Test Results

### 1. Unit Tests (`pytest tests/test_risk*.py`)
- **`tests/test_risk_rules.py`**: Pattern matching, severity weights, empty string handling, and false-positive checks $\to$ **7 / 7 PASSED**.
- **`tests/test_risk_scoring.py`**: Confidence scaling, asymptotic rule aggregation, 30/35/15/20 weights, thresholds, contract aggregation $\to$ **5 / 5 PASSED**.
- **`tests/test_risk_analyzer.py`**: Facade orchestration, mocked LLM response, fallback handling, document aggregation $\to$ **3 / 3 PASSED**.

### 2. Live LM Studio Smoke Test (`scripts/test_risk_analysis.py`)
- Executed against synthetic contract clauses using active `qwen3-4b-instruct-2507` model.
- **Results**:
  - Clause 14.2 (Limitation of Liability & Indemnification): **78.74 (HIGH)**
  - Clause 8.1 (Non-Compete & Renewal): **69.02 (MEDIUM)**
  - Clause 1.1 (Effective Date & Governing Law): **20.88 (LOW)**
  - Document Summary Score: **69.73 / 100.0 (MEDIUM)**

### 3. Full Regression Suite (Phases 4–7.1)
- Executed full test suite:
  ```powershell
  $env:PYTHONPATH="."
  .\.venv\Scripts\pytest.exe tests/ -v
  ```
- **Total Tests Passed**: **75 / 75 PASSED** ($100\%$ pass rate across Phase 4, 5, 6, 7, and 7.1).

---

## 7. Limitations & Legal Disclaimer

1. **Decision Support Signal**: Risk scores are heuristic decision-support metrics and do **NOT** constitute formal legal advice or guarantees of legal enforceability.
2. **Context Scope**: Clause assessments evaluate individual clauses and retrieved evidence, which should be reviewed in full contract context by a qualified legal professional.
