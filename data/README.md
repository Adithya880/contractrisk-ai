# Data Directory

This directory is designated for raw input contracts, supervised training datasets, and processed evaluation splits.

## Exclusion from Version Control

In accordance with repository hygiene and privacy standards:
- Raw contractual documents (`.pdf`, `.docx`, `.xlsx`) and training datasets (`.csv`) are excluded from Git version control via `.gitignore`.
- Intermediate processed files and split outputs are not committed to GitHub.

## Directory Layout & Placement

When working locally, place your data in the respective subdirectories as documented:

```text
data/
├── raw/         # Place raw legal_contract_clauses.csv or input legal contract corpora
├── processed/   # Cleaned and deduplicated dataset files (e.g., cleaned_clauses.csv)
├── review/      # Data audit reports and anomaly review logs
└── splits/      # Partitioned training, validation, and test datasets (train.csv, validation.csv, test.csv)
```

## Dataset Specifications

- The classifier pipeline expects dataset schemas with `clause_text`, `clause_type` (41 categories), and `risk_level` (`Low`, `Medium`, `High`).
- For complete schema definitions, validation checks, and distribution characteristics, refer to [`docs/DATASET_REPORT.md`](../docs/DATASET_REPORT.md).
