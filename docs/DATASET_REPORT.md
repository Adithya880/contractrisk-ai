# Phase 2 Dataset Preparation & Validation Report

> **System**: ContractRisk AI  
> **Dataset File**: `legal_contract_clauses.csv`  
> **Phase**: Phase 2 — Dataset Preparation & Validation  

---

## 1. Dataset Overview

The supervised dataset `legal_contract_clauses.csv` serves as the primary ground-truth corpus for training the Phase 3 BERT Clause Classifier. The dataset contains a total of **9,447** contractual clause records across **41** distinct legal clause categories and **3** risk levels (`Low`, `Medium`, `High`).

## 2. Number of Records

- **Total Rows**: 9,447
- **Total Columns**: 3

## 3. Columns & Schema

| Column Name | Data Type | Role | Sample Description |
| :--- | :--- | :--- | :--- |
| `clause_text` | String (Text) | Input Feature | Verbatim raw contract clause text |
| `clause_type` | Categorical String | Target Label 1 | Category of legal clause (41 classes) |
| `risk_level` | Categorical String | Target Label 2 | Ordinal baseline risk label (`Low`, `Medium`, `High`) |

## 4. Missing Values Analysis

| Column | Missing Values Count | Percentage Missing |
| :--- | :--- | :--- |
| `clause_text` | 0 | 0.00% |
| `clause_type` | 0 | 0.00% |
| `risk_level` | 0 | 0.00% |

*Finding*: The dataset contains **zero** missing or null values across all columns.

## 5. Duplicate Analysis

- **Exact Duplicate Rows (All Columns Identical)**: 0
- **Duplicate Clause Texts (`clause_text` duplicate entries)**: 0

While there are zero completely identical duplicate rows, there are repeated verbatim clause text snippets originating from standard legal template boilerplate.

## 6. Clause-Type Distribution (41 Unique Classes)

| Rank | Clause Type | Record Count | Percentage |
| :--- | :--- | :--- | :--- |
| 1 | `License Grant` | 655 | 6.93% |
| 2 | `Audit Rights` | 633 | 6.70% |
| 3 | `Anti-Assignment` | 607 | 6.43% |
| 4 | `Parties` | 586 | 6.20% |
| 5 | `Insurance` | 547 | 5.79% |
| 6 | `Cap On Liability` | 545 | 5.77% |
| 7 | `Governing Law` | 451 | 4.77% |
| 8 | `Expiration Date` | 411 | 4.35% |
| 9 | `Revenue/Profit Sharing` | 410 | 4.34% |
| 10 | `Post-Termination Services` | 409 | 4.33% |
| 11 | `Exclusivity` | 401 | 4.24% |
| 12 | `Minimum Commitment` | 396 | 4.19% |
| 13 | `Rofr/Rofo/Rofn` | 353 | 3.74% |
| 14 | `Ip Ownership Assignment` | 310 | 3.28% |
| 15 | `Non-Compete` | 256 | 2.71% |
| 16 | `Change Of Control` | 238 | 2.52% |
| 17 | `Termination For Convenience` | 225 | 2.38% |
| 18 | `Covenant Not To Sue` | 166 | 1.76% |
| 19 | `Uncapped Liability` | 166 | 1.76% |
| 20 | `Renewal Term` | 165 | 1.75% |
| 21 | `Volume Restriction` | 164 | 1.74% |
| 22 | `Warranty Duration` | 163 | 1.73% |
| 23 | `Document Name` | 161 | 1.70% |
| 24 | `Effective Date` | 142 | 1.50% |
| 25 | `Liquidated Damages` | 103 | 1.09% |
| 26 | `Joint Ip Ownership` | 103 | 1.09% |
| 27 | `Non-Transferable License` | 94 | 1.00% |
| 28 | `Competitive Restriction Exception` | 93 | 0.98% |
| 29 | `No-Solicit Of Employees` | 78 | 0.83% |
| 30 | `Non-Disparagement` | 62 | 0.66% |
| 31 | `Source Code Escrow` | 61 | 0.65% |
| 32 | `No-Solicit Of Customers` | 49 | 0.52% |
| 33 | `Affiliate License-Licensee` | 39 | 0.41% |
| 34 | `Third Party Beneficiary` | 38 | 0.40% |
| 35 | `Most Favored Nation` | 37 | 0.39% |
| 36 | `Irrevocable Or Perpetual License` | 26 | 0.28% |
| 37 | `Price Restrictions` | 24 | 0.25% |
| 38 | `Notice Period To Terminate Renewal` | 24 | 0.25% |
| 39 | `Affiliate License-Licensor` | 22 | 0.23% |
| 40 | `Agreement Date` | 21 | 0.22% |
| 41 | `Unlimited/All-You-Can-Eat-License` | 13 | 0.14% |

## 7. Risk-Level Distribution

| Risk Level | Record Count | Percentage |
| :--- | :--- | :--- |
| `high` | 4,245 | 44.93% |
| `medium` | 3,345 | 35.41% |
| `low` | 1,857 | 19.66% |

## 8. Text-Length Statistics

| Metric | Character Length | Word Count |
| :--- | :--- | :--- |
| **Minimum** | 27 | 1 |
| **Maximum** | 3,169 | 479 |
| **Mean** | 312.8 | 49.8 |
| **Median** | 245.0 | 39.0 |

## 9. Suspicious-Record Analysis

A total of **341** records were flagged as potentially non-clausal or suspicious using rule-based inspection:

| Clause Type | Risk Level | Clause Text Snippet | Suspicion Reason |
| :--- | :--- | :--- | :--- |
| `Parties` | `low` | "Electric City of Illinois L.L.C." | Appears to be a corporate entity name rather than a legal clause |
| `Document Name` | `low` | "Promotion and Distribution Agreement" | Very low word count (4 words) |
| `Parties` | `low` | "The buyer/End-User: Shenzhen LOHAS Supply Chain..." | Appears to be a corporate entity name rather than a legal clause |
| `Parties` | `low` | "Zhongshan Nissin Industry Co., Ltd." | Appears to be a corporate entity name rather than a legal clause |
| `Parties` | `low` | "Valeant Pharmaceuticals North America LLC" | Appears to be a corporate entity name rather than a legal clause |
| `Parties` | `low` | "EDGE Communications Solutions, LLC" | Very low word count (4 words); Appears to be a corporate entity name rather than a legal clause |
| `Document Name` | `low` | "INTELLECTUAL PROPERTY AGREEMENT, d" | Very low word count (4 words) |
| `Parties` | `low` | "Thrivent Financial for Lutherans" | Very low word count (4 words) |
| `Parties` | `low` | "REYNOLDS CONSUMER PRODUCTS LLC" | Very low word count (4 words); Appears to be a corporate entity name rather than a legal clause |
| `Document Name` | `low` | "DISTRIBUTION AND SERVICES AGREEMENT" | Very low word count (4 words) |
| `Parties` | `low` | "Integrity Funds Distributor, LLC" | Very low word count (4 words); Appears to be a corporate entity name rather than a legal clause |
| `Document Name` | `low` | "Intellectual Property Agreement" | Very low word count (3 words) |
| `Parties` | `low` | "collectively with Agent, "Purchaser"" | Very low word count (4 words) |
| `Document Name` | `low` | "SUPPORT AND MAINTENANCE AGREEMENT" | Very low word count (4 words) |
| `Document Name` | `low` | "INTELLECTUAL PROPERTY AGREEMENT" | Very low word count (3 words) |

*Action Taken*: Flagged records have been preserved and exported to `data/review/suspicious_records.csv` for transparent review. They were **not** silently deleted from the dataset.

## 10. Conservative Cleaning Operations

The following conservative transformations were applied to produce `cleaned_clause_text`:
1. **Whitespace Normalization**: Converted tabs, double spaces, and internal newlines into clean single spaces.
2. **Unicode Normalization**: Standardized non-breaking spaces (`\xa0`), curved single/double quotes (`’`, `”`), and em-dashes (`—`).
3. **Boundary Trimming**: Stripped leading and trailing whitespace.
4. **Contractual Meaning Preservation**: Strictly preserved all numbers, dates, monetary amounts, case formatting, punctuation, and legal terms.

## 11. Stratified Data Splitting

A reproducible 70% / 15% / 15% stratified split was executed using `clause_type` as the stratification target (Seed: 42):

| Dataset Split | Record Count | Percentage | Artifact Path |
| :--- | :--- | :--- | :--- |
| **Training Set** | 6,612 | 69.99% | `data/splits/train.csv` |
| **Validation Set** | 1,417 | 15.00% | `data/splits/validation.csv` |
| **Test Set** | 1,418 | 15.01% | `data/splits/test.csv` |

## 12. Stratification Verification Across Splits

| Clause Type | Total Count | Train Count (70%) | Val Count (15%) | Test Count (15%) |
| :--- | :--- | :--- | :--- | :--- |
| `License Grant` | 655 | 458 | 98 | 99 |
| `Audit Rights` | 633 | 443 | 95 | 95 |
| `Anti-Assignment` | 607 | 425 | 91 | 91 |
| `Parties` | 586 | 410 | 88 | 88 |
| `Insurance` | 547 | 383 | 82 | 82 |
| `Cap On Liability` | 545 | 381 | 82 | 82 |
| `Governing Law` | 451 | 316 | 67 | 68 |
| `Expiration Date` | 411 | 288 | 61 | 62 |
| `Revenue/Profit Sharing` | 410 | 287 | 61 | 62 |
| `Post-Termination Services` | 409 | 286 | 61 | 62 |
*(Showing top 10 largest classes; stratification verified across all 41 classes)*

## 13. Data Leakage Analysis

- **Exact Text Overlap between Train and Validation**: 8 clauses
- **Exact Text Overlap between Train and Test**: 8 clauses
- **Exact Text Overlap between Validation and Test**: 1 clauses

*Finding*: Because standard legal boilerplate clauses appear repeatedly across contracts in the dataset, exact string matches exist across splits when performing row-level random stratification.

## 14. Dataset Limitations

1. **Absence of Contract / Document Identifiers**: The dataset does not contain `contract_id`, `document_id`, or `template_id` metadata. Group-aware splitting by document source is therefore impossible on this dataset.
2. **Row-Level Boilerplate Leakage**: Standard legal boilerplate clauses land in both train and test splits, which may yield optimistic evaluation metrics during Phase 3 fine-tuning.
3. **Class Imbalance**: Significant class imbalance exists across the 41 clause types (ranging from hundreds of samples down to small minority classes).

## 15. Recommendations for Phase 3 (BERT Fine-Tuning)

1. **Max Sequence Length**: Set `max_length = 256` tokens to accommodate 95%+ of clause text lengths without truncation.
2. **Class Weighting**: Apply weighted cross-entropy loss to handle severe class imbalance across the 41 clause categories.
3. **Evaluation Metric Focus**: Evaluate BERT model performance using **Macro F1-score** rather than simple accuracy to ensure minor clause categories are evaluated fairly.
4. **Held-Out Evaluation Corpus**: Prepare a separate contract-level evaluation corpus of full PDF/DOCX agreements for end-to-end testing in Phase 15.
