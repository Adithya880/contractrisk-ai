# Phase 6 Embeddings & FAISS Technical Report

> **System**: ContractRisk AI  
> **Phase**: Phase 6 — Semantic Embeddings & FAISS Vector Indexing  
> **Embedding Backbone**: `sentence-transformers/all-MiniLM-L6-v2` (384 Dimensions)  
> **Vector Database**: FAISS `IndexFlatIP` (Exact Inner Product Search)  

---

## 1. Phase 6 Objective

The objective of Phase 6 is to construct the semantic vector embedding and retrieval index layer for ContractRisk AI. 

The pipeline converts Phase 5 `SegmentedClause` objects into 384-dimensional L2-normalized vector embeddings, indexes them into FAISS `IndexFlatIP`, maintains a strict 1-to-1 vector metadata alignment mapping back to original contract clauses, supports deterministic similarity search, and implements disk persistence with schema compatibility validation.

---

## 2. Architecture & System Disclosures

```
Phase 5 SegmentedClause Objects
          │
          ▼
   [ClauseEmbedder] (all-MiniLM-L6-v2, Batch Size 32, CUDA/CPU)
          │
          ▼
   [L2 Vector Normalizer] (||v||₂ = 1.0)
          │
          ▼
   [FAISSIndexManager] ──► [faiss.IndexFlatIP(384)]
          │                     │
          │                     ▼
          ├──────────────► [ClauseMetadata Array] (1-to-1 Index Alignment)
          │
          ▼
   [Similarity Search API] (search(query, top_k, similarity_threshold))
          │
          ▼
   [Persistence Engine] ──► (contract_clauses.faiss + contract_clauses_metadata.json + manifest.json)
```

> [!IMPORTANT]
> **System Architecture Disclosures**:
> - **Embedding Backbone**: `all-MiniLM-L6-v2` produces 384-dimensional embeddings.
> - **Cosine Similarity Approximation**: L2 normalization + `IndexFlatIP` computes exact Cosine Similarity.
> - **Retrieval Infrastructure Only**: Phase 6 provides vector embedding and retrieval infrastructure ONLY.
> - **No RAG Generation**: Retrieval-Augmented Generation (RAG) is **NOT** implemented in Phase 6.
> - **No LLM Generation**: No LLM text generation or answer synthesis is performed in this phase.
> - **Test Corpus Distinction**: Unit/smoke tests use a synthetic contract corpus and do **NOT** populate the eventual production historical knowledge base.

---

## 3. Embedding Pipeline Specifications

| Parameter | Configuration | Technical Rationale |
| :--- | :--- | :--- |
| **Model Name** | `all-MiniLM-L6-v2` | Lightweight 6-layer Transformer (22.9M params), optimized for legal/semantic similarity |
| **Embedding Dimension** | `384` | Standard vector dimension |
| **Device Selection** | Automatic (`CUDA` if available, else `CPU`) | Hardware safety for RTX 3050 Laptop GPU (4 GB VRAM) |
| **Batch Size** | `32` (Configurable) | Conservative GPU VRAM memory safety limit |
| **Normalization** | L2 Unit Norm ($\|v\|_2 = 1.0$) | Guarantees inner product equals Cosine Similarity |

---

## 4. FAISS Index & Metadata Schema

- **FAISS Index Type**: `faiss.IndexFlatIP` (Exact brute-force inner product search). Approximate index structures (`IVF`, `HNSW`) are omitted as the corpus scale permits exact similarity calculation without approximation loss.
- **1-to-1 Metadata Alignment**: Vector index position $i$ in `faiss.IndexFlatIP` corresponds directly to array index $i$ in `ClauseMetadata`.

### `ClauseMetadata` Schema
```json
{
  "vector_index": 0,
  "clause_id": "774992465382e414:clause:006",
  "document_id": "774992465382e414",
  "clause_number": "2.1",
  "clause_heading": "Tenant Indemnity",
  "clause_text": "2.1 Tenant Indemnity. Tenant shall indemnify, defend, and hold harmless Landlord...",
  "source_pages": [1],
  "start_page": 1,
  "end_page": 1,
  "hierarchy_level": 2,
  "parent_clause_number": "ARTICLE II"
}
```

---

## 5. Search API & Persistence Engine

### Search API
`search(query: str, embedder: ClauseEmbedder, top_k: int = 5, similarity_threshold: Optional[float] = None) -> List[SearchResult]`

1. Embeds query using `ClauseEmbedder` (producing L2-normalized 384-d vector).
2. Performs FAISS inner product search (`_index.search(query_vec, top_k)`).
3. Maps matching indices back to `ClauseMetadata`.
4. Filters results below optional `similarity_threshold`.
5. Returns `SearchResult` instances containing similarity scores and full provenance.

### Persistence & Compatibility Validation
`save(dir_path)` writes:
- `contract_clauses.faiss`: Binary FAISS vector index file.
- `contract_clauses_metadata.json`: Serialized JSON array of metadata records.
- `manifest.json`: Compatibility manifest containing `model_name`, `embedding_dimension` (384), `normalization` ("L2"), `faiss_index_type` ("IndexFlatIP"), `total_vectors`, and ISO timestamp.

`load(dir_path)` enforces strict validation checks:
- Rejects index if `embedding_dimension != 384`.
- Rejects index if `FAISS.ntotal != len(metadata)`.

---

## 6. Semantic Retrieval Sanity Check

- **Sanity Query**: `"What are the tenant indemnification and liability obligations?"`
- **Indexed Test Corpus**: 9 segmented contract clauses from a synthetic Commercial Lease Agreement.
- **Retrieved Top Result**:
  - **Clause ID**: `774992465382e414:clause:006`
  - **Clause Number**: `2.1`
  - **Clause Heading**: `Tenant Indemnity`
  - **Similarity Score**: **`0.7925`** (79.25% Cosine Similarity)
  - **Result Verification**: The top retrieved clause directly addresses tenant indemnification obligations.

---

## 7. Test Results & Regression Verification

### Phase 6 Unit Test Suite (`pytest`)
All **10 Phase 6 unit tests** passed cleanly:
- `tests/test_embeddings.py`: 4 passed (Dimension=384, L2 unit norm, batching, empty input)
- `tests/test_faiss_index.py`: 3 passed (Index building, persistence save/load, count mismatch detection)
- `tests/test_retrieval.py`: 3 passed (Semantic sanity check, top-k retrieval, threshold filtering)

### Full Regression Suite (Phases 4–6)
All **47 regression tests** passed cleanly in **54.34 seconds**:

```
============================= 47 passed in 54.34s =============================
```

### CLI Verification Smoke Test (`scripts/test_embeddings_faiss.py`)
- **Pipeline Execution**: Phase 4 loader $\rightarrow$ Phase 5 segmenter $\rightarrow$ Phase 6 index manager
- **Vector Count**: 9 vectors indexed (384 dimensions)
- **Sanity Query Match**: Clause `2.1 Tenant Indemnity` retrieved at rank 1 with score `0.7925`
- **Persistence Verification**: Post-reload query returned identical rank 1 clause and score (`0.7925`)

---

## 8. Summary of Files Created & Modified

### Files Created
- [models.py](file:///C:/Users/adith/Desktop/BEING%20CODER/AI%20CLAUSE%20ANALYSER/src/embeddings/models.py) — Pydantic v2 data models (`ClauseMetadata`, `SearchResult`, `IndexManifest`)
- [embedder.py](file:///C:/Users/adith/Desktop/BEING%20CODER/AI%20CLAUSE%20ANALYSER/src/embeddings/embedder.py) — L2-normalized SentenceTransformer (`all-MiniLM-L6-v2`) embedder
- [index.py](file:///C:/Users/adith/Desktop/BEING%20CODER/AI%20CLAUSE%20ANALYSER/src/embeddings/index.py) — `FAISSIndexManager` wrapping `IndexFlatIP`, metadata alignment, search API, and persistence
- [__init__.py](file:///C:/Users/adith/Desktop/BEING%20CODER/AI%20CLAUSE%20ANALYSER/src/embeddings/__init__.py) — Package initialization and public API export
- [test_embeddings.py](file:///C:/Users/adith/Desktop/BEING%20CODER/AI%20CLAUSE%20ANALYSER/tests/test_embeddings.py) — Pytest unit test suite for embedder
- [test_faiss_index.py](file:///C:/Users/adith/Desktop/BEING%20CODER/AI%20CLAUSE%20ANALYSER/tests/test_faiss_index.py) — Pytest unit test suite for FAISS index manager
- [test_retrieval.py](file:///C:/Users/adith/Desktop/BEING%20CODER/AI%20CLAUSE%20ANALYSER/tests/test_retrieval.py) — Pytest unit test suite for similarity search & retrieval sanity check
- [test_embeddings_faiss.py](file:///C:/Users/adith/Desktop/BEING%20CODER/AI%20CLAUSE%20ANALYSER/scripts/test_embeddings_faiss.py) — CLI verification & smoke test script
- [EMBEDDINGS_FAISS_REPORT.md](file:///C:/Users/adith/Desktop/BEING%20CODER/AI%20CLAUSE%20ANALYSER/docs/EMBEDDINGS_FAISS_REPORT.md) — Comprehensive technical report

### Files Modified
- None (Phase 1–5 source code and Phase 3 BERT model checkpoints remain 100% untouched)
