# ContractRisk AI — Phase 9 PostgreSQL Persistence Report

## 1. Executive Overview
Phase 9 introduces relational persistence for **ContractRisk AI**. All extracted document metadata, segmented contractual clauses, hybrid risk scores, score component breakdowns, regex rule matches, benchmark evidence citations, evidence-grounded future scenarios, contract summaries, and reproducibility runs are atomically persisted to PostgreSQL via SQLAlchemy 2.x and Alembic.

The database layer functions purely as a persistence service: **it does not calculate risk or alter existing business logic**. Existing API response structures (`POST /api/v1/analyze`) remain 100% backward compatible.

---

## 2. Environment Configuration
PostgreSQL connection parameters are configured dynamically through environment variables in `.env` (derived from `.env.example`):

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=contractrisk
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password_here
DATABASE_URL=postgresql+psycopg://postgres:your_password_here@localhost:5432/contractrisk
```

---

## 3. Relational Database Schema
The database architecture consists of 8 relational tables designed using SQLAlchemy 2.x `DeclarativeBase` with explicit foreign keys, indexes, unique constraints, and cascade deletion rules:

```mermaid
erDiagram
    documents ||--o{ clauses : "1 -> many"
    documents ||--o{ contract_summaries : "1 -> many"
    documents ||--o{ analysis_runs : "1 -> many"
    clauses ||--o| risk_assessments : "1 -> 1"
    risk_assessments ||--o{ rule_matches : "1 -> many"
    risk_assessments ||--o{ evidence_citations : "1 -> many"
    risk_assessments ||--o| future_scenarios : "1 -> 1"

    documents {
        int id PK
        string document_id UK
        string filename
        string document_type
        datetime uploaded_at
        int page_count
        int clause_count
        string processing_status
    }

    clauses {
        int id PK
        string document_id FK
        string clause_id
        string clause_number
        string clause_title
        text clause_text
        json source_pages
        int sequence_number
    }

    risk_assessments {
        int id PK
        int clause_db_id FK
        string risk_category
        string risk_level
        float final_score
        float bert_score
        float rule_score
        float rag_score
        float llm_score
        text risk_explanation
    }

    rule_matches {
        int id PK
        int risk_assessment_id FK
        string rule_id
        string category
        float severity
        text matched_text
    }

    evidence_citations {
        int id PK
        int risk_assessment_id FK
        string source_clause_id
        text source_text
        float similarity_score
    }

    future_scenarios {
        int id PK
        int risk_assessment_id FK
        string scenario_title
        text trigger_condition
        text scenario_description
        text possible_consequence
        json assumptions
        text uncertainty
    }

    contract_summaries {
        int id PK
        string document_id FK
        float risk_score
        string risk_level
        int high_risk_count
        int medium_risk_count
        int low_risk_count
    }

    analysis_runs {
        int id PK
        string run_id UK
        string document_id FK
        string pipeline_version
        string status
    }
```

---

## 4. Alembic Migration Setup
Alembic migration control is fully configured under `alembic/`:

- **Configuration File**: `alembic.ini`
- **Environment**: `alembic/env.py` (loads `Base.metadata` and `settings.database_url`)
- **Initial Migration**: `alembic/versions/001_initial_schema.py`

### Migration Commands
```bash
# Apply migrations to initialize PostgreSQL database
alembic upgrade head

# Rollback initial migration if needed
alembic downgrade -1
```

---

## 5. PostgreSQL Installation & System Setup Instructions

### Prerequisites & Check
Check if PostgreSQL is installed on Windows:
```powershell
postgres --version
Get-Service -Name '*postgres*'
```

### Installation Options (If PostgreSQL is NOT installed)
1. **Via Windows Package Manager (winget)**:
   ```powershell
   winget install PostgreSQL.PostgreSQL.17
   ```
2. **Database Initialization in psql**:
   ```sql
   CREATE DATABASE contractrisk;
   CREATE USER postgres WITH ENCRYPTED PASSWORD 'postgres';
   GRANT ALL PRIVILEGES ON DATABASE contractrisk TO postgres;
   ```
3. **Apply Schema Migrations**:
   ```bash
   alembic upgrade head
   ```

---

## 6. Verification & Test Suite Results

- **Existing Pipeline Regression Tests**: `105 / 105 PASSED` (100% pass rate)
- **Phase 9 Database Persistence Tests**: `11 / 11 PASSED` (100% pass rate)
- **Total Test Suite**: `116 / 116 PASSED`

---

## 7. API Behavior & Backward Compatibility
- **Endpoint**: `POST /api/v1/analyze` (Preserved 100% backward compatible output)
- **Optional Read Endpoints**:
  - `GET /api/v1/documents`: List processed contract documents
  - `GET /api/v1/documents/{document_id}`: Retrieve persisted clauses, assessments, scenarios, and contract summaries
