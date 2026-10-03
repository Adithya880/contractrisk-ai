# Phase 7 Retrieval-Augmented Generation (RAG) Technical Report

> **System**: ContractRisk AI  
> **Phase**: Phase 7 — Grounded Retrieval-Augmented Generation (RAG)  
> **Retriever**: Phase 6 FAISS `IndexFlatIP` + `all-MiniLM-L6-v2`  
> **LLM Engine**: Local Qwen3 4B Instruct (`qwen3-4b-instruct-2507`) via LM Studio  

---

## 1. Phase 7 Objective

The objective of Phase 7 is to construct an evidence-grounded Retrieval-Augmented Generation (RAG) architecture for ContractRisk AI. 

The pipeline connects user queries to Phase 6 semantic retrieval, formats top-k retrieved contract clauses into a deterministic context block, queries the local Qwen3 model running on LM Studio (`http://127.0.0.1:1234/v1`), validates evidence citations, and returns structured JSON responses.

---

## 2. RAG Architecture & System Disclosures

```
User Query
    │
    ▼
[RAGRetriever] ──► [Phase 6 FAISS IndexFlatIP] (top_k=5, threshold=0.65)
    │
    ▼
Top-K Retrieved Evidence Items
    │
    ▼
[ContextBuilder] (Formats Evidence Blocks & Enforces ~2048 Token Budget)
    │
    ▼
[LLMGenerator] (Local Qwen3 via LM Studio /v1/chat/completions)
    │
    ▼
[GroundingValidator] (Verifies Citations against Evidence IDs & Checks Fallback)
    │
    ▼
RAGResponse (Answer + Verified Citations + Evidence Provenance + insufficient_evidence flag)
```

> [!IMPORTANT]
> **System Architecture Disclosures**:
> - **RAG Definition**: RAG combines semantic retrieval (FAISS) with local LLM generation (Qwen3).
> - **Explicit Evidence Supply**: Retrieved contract evidence is supplied explicitly in the LLM prompt.
> - **No Legal Guarantee**: The system provides technical decision-support and does **NOT** provide binding legal advice or guarantee legal accuracy.
> - **No Risk Engine**: Risk scoring and regex risk detection are **NOT** part of Phase 7.

---

## 3. Retriever Integration & Configuration

Reuses existing Phase 6 vector search infrastructure directly:

- **Retriever API**: `RAGRetriever` wrapping `FAISSIndexManager` and `ClauseEmbedder`.
- **Default `top_k`**: `5`
- **Default `similarity_threshold`**: `0.65` (Cosine similarity cutoff)
- **Preserved Metadata**: `clause_id`, `document_id`, `clause_number`, `clause_heading`, `clause_text`, `source_pages`, `similarity_score`.

---

## 4. Context Construction & Token Budgeting

The `ContextBuilder` (`src/rag/context_builder.py`) formats retrieved clauses into structured evidence blocks:

```
[Evidence 1]
Clause ID: rag_corpus:clause:001
Clause Number: 1.1
Heading: Confidentiality Obligations
Source Page(s): 1
Similarity Score: 0.8521
Clause Text:
1.1 Confidentiality Obligations. Each Party agrees to maintain...
```

- **Token Budget Limit**: 8,000 characters (~2,048 tokens).
- **Truncation Policy**: Prioritizes highest-ranked results without truncating mid-clause text.

---

## 5. System Prompt & LLM Generation Parameters

### System Prompt Strategy (`src/rag/prompts.py`)
Instructs local Qwen3 to:
1. Answer **ONLY** from the supplied contract evidence.
2. Avoid inventing terms, dates, amounts, parties, or unsupported obligations.
3. If evidence is missing or below threshold, set `insufficient_evidence = true` and respond: `"The retrieved contract evidence is insufficient to answer this question."`
4. Return structured JSON with verified clause citations.

### Generation Hyperparameters
- **API Endpoint**: `http://127.0.0.1:1234/v1/chat/completions`
- **Active Model ID**: `qwen3-4b-instruct-2507` (Discovered via `/v1/models`)
- **Temperature**: `0.2`
- **Top P**: `0.9`
- **Max Tokens**: `1500`

---

## 6. Citation Strategy & Grounding Validation

- **Citation Format**: `[Clause 1.1, p.[1]]` mapping answer claims directly to `clause_id` and `source_pages`.
- **Grounding Validation** (`src/rag/validators.py`):
  - Filters out any citation whose `clause_id` does not exist in the retrieved evidence list.
  - Aligns cited page numbers with actual evidence records.
  - Automatically flags `insufficient_evidence = true` if evidence is empty or similarity scores fall below threshold.

---

## 7. Test Results & Live LM Studio Integration

### Automated Pytest Suite (Mocked HTTP Calls)
All **13 Phase 7 unit tests** passed cleanly in **60.15 seconds**:
- `tests/test_rag_retriever.py`: 1 passed
- `tests/test_rag_context.py`: 2 passed
- `tests/test_rag_prompts_models.py`: 3 passed
- `tests/test_rag_generator.py`: 4 passed (Mocked HTTP calls, backtick stripping, timeout handling)
- `tests/test_rag_pipeline.py`: 3 passed (Supported query, threshold fallback, fake citation filtering)

### Full Regression Test Suite (Phases 4–7)
All **60 regression unit tests** passed cleanly in **76.54 seconds**:

```
======================== 60 passed in 76.54s (0:01:16) ========================
```

### Live LM Studio Smoke Test Results (`scripts/test_rag_lmstudio.py`)
Executed against live local server at `http://127.0.0.1:1234/v1` (`qwen3-4b-instruct-2507`):

| Query Category | Question | Insufficient Flag | Verified Citation | Grounded Answer Summary |
| :--- | :--- | :--- | :--- | :--- |
| **Confidentiality** | *"What are the confidentiality obligations?"* | `False` | `[1.1, p.[1]]` | Strict confidentiality for proprietary technical data and trade secrets. |
| **Termination** | *"When can the agreement be terminated?"* | `False` | `[2.1, p.[1]]` | At any time for convenience upon 30 days prior written notice. |
| **Intellectual Property** | *"Who owns the intellectual property?"* | `False` | `[3.1, p.[2]]` | Licensor owns all custom software and deliverables exclusively. |
| **Payment Terms** | *"What are the payment terms?"* | `False` | `[4.1, p.[2]]` | Undisputed invoices due within 30 days; 1.5% interest per month. |
| **Governing Law (Unsupported)** | *"What is the governing law of this agreement?"* | `True` | None | *"The retrieved contract evidence is insufficient to answer this question."* |

---

## 8. Example RAG Interaction Output

```json
{
  "query": "When can the agreement be terminated?",
  "answer": "The agreement can be terminated at any time for convenience by either party upon providing at least thirty (30) days prior written notice to the other party.",
  "evidence": [
    {
      "clause_id": "rag_corpus:clause:002",
      "document_id": "msa_2026_contract",
      "clause_number": "2.1",
      "clause_heading": "Termination for Convenience",
      "clause_text": "2.1 Termination for Convenience. Either Party may terminate this Agreement at any time for convenience upon providing at least thirty (30) days prior written notice to the other Party.",
      "source_pages": [1],
      "similarity_score": 0.8142
    }
  ],
  "citations": [
    {
      "clause_id": "rag_corpus:clause:002",
      "clause_number": "2.1",
      "source_pages": [1]
    }
  ],
  "insufficient_evidence": false,
  "model_name": "qwen3-4b-instruct-2507",
  "retrieval_top_k": 3,
  "retrieval_threshold": 0.60
}
```

---

## 9. Known Limitations

1. **Context Window Constraint**: Context budget is capped at ~2048 tokens; contracts with dozens of top-k clauses prioritize highest-similarity results.
2. **Local Inference Latency**: Local Qwen3 CPU/GPU inference requires ~2-4 seconds per query response.
3. **No Risk Engine**: RAG provides evidence retrieval and Q&A; risk categorization and scoring are handled in later phases.

---

## 10. Summary of Files Created & Modified

### Files Created
- [models.py](file:///C:/Users/adith/Desktop/BEING%20CODER/AI%20CLAUSE%20ANALYSER/src/rag/models.py) — Pydantic v2 data models (`RAGEvidenceItem`, `Citation`, `RAGResponse`)
- [retriever.py](file:///C:/Users/adith/Desktop/BEING%20CODER/AI%20CLAUSE%20ANALYSER/src/rag/retriever.py) — `RAGRetriever` wrapping Phase 6 FAISS search
- [context_builder.py](file:///C:/Users/adith/Desktop/BEING%20CODER/AI%20CLAUSE%20ANALYSER/src/rag/context_builder.py) — `ContextBuilder` for prompt context formatting and budget capping
- [prompts.py](file:///C:/Users/adith/Desktop/BEING%20CODER/AI%20CLAUSE%20ANALYSER/src/rag/prompts.py) — System prompts and user prompt templates enforcing evidence grounding
- [generator.py](file:///C:/Users/adith/Desktop/BEING%20CODER/AI%20CLAUSE%20ANALYSER/src/rag/generator.py) — `LLMGenerator` connecting to LM Studio `/v1/chat/completions`
- [validators.py](file:///C:/Users/adith/Desktop/BEING%20CODER/AI%20CLAUSE%20ANALYSER/src/rag/validators.py) — Grounding and citation validation engine
- [pipeline.py](file:///C:/Users/adith/Desktop/BEING%20CODER/AI%20CLAUSE%20ANALYSER/src/rag/pipeline.py) — Main `RAGPipeline` facade
- [__init__.py](file:///C:/Users/adith/Desktop/BEING%20CODER/AI%20CLAUSE%20ANALYSER/src/rag/__init__.py) — Package initialization and public API exports
- [test_rag_retriever.py](file:///C:/Users/adith/Desktop/BEING%20CODER/AI%20CLAUSE%20ANALYSER/tests/test_rag_retriever.py) — Pytest suite for retriever
- [test_rag_context.py](file:///C:/Users/adith/Desktop/BEING%20CODER/AI%20CLAUSE%20ANALYSER/tests/test_rag_context.py) — Pytest suite for context builder
- [test_rag_prompts_models.py](file:///C:/Users/adith/Desktop/BEING%20CODER/AI%20CLAUSE%20ANALYSER/tests/test_rag_prompts_models.py) — Pytest suite for prompts and models
- [test_rag_generator.py](file:///C:/Users/adith/Desktop/BEING%20CODER/AI%20CLAUSE%20ANALYSER/tests/test_rag_generator.py) — Pytest suite for generator (mocked HTTP)
- [test_rag_pipeline.py](file:///C:/Users/adith/Desktop/BEING%20CODER/AI%20CLAUSE%20ANALYSER/tests/test_rag_pipeline.py) — Pytest suite for pipeline
- [test_rag_lmstudio.py](file:///C:/Users/adith/Desktop/BEING%20CODER/AI%20CLAUSE%20ANALYSER/scripts/test_rag_lmstudio.py) — Live LM Studio CLI integration & smoke test script
- [RAG_REPORT.md](file:///C:/Users/adith/Desktop/BEING%20CODER/AI%20CLAUSE%20ANALYSER/docs/RAG_REPORT.md) — Comprehensive technical report

### Files Modified
- None (Phase 1–6 source code and Phase 3 BERT model checkpoints remain 100% untouched)
