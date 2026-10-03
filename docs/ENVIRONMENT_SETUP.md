# Phase 1 Environment Setup & Verification Guide

This document records the verified Phase 1 development environment for **ContractRisk AI** and instructions for running all verification routines.

---

## Verified Phase 1 Environment Details

- **Operating System**: Windows 11 Home 64-bit
- **Python Version**: Python 3.11.9
- **Virtual Environment**: `.venv`
- **PyTorch**: 2.5.1+cu121
- **CUDA Availability**: `True` (CUDA Toolkit 12.1)
- **GPU Hardware**: NVIDIA GeForce RTX 3050 Laptop GPU (4 GB VRAM)
- **Host RAM**: 16 GB DDR4
- **Transformers**: 5.18.0
- **spaCy**: 3.8.16 (`en_core_web_sm` 3.8.0)
- **Sentence Transformers**: 6.1.0 (`all-MiniLM-L6-v2` -> 384-dimensional dense embeddings)
- **FAISS**: 1.15.1
- **LangChain**: 1.4.3
- **FastAPI**: 0.142.2
- **Pydantic**: 2.13.5
- **LM Studio Server**: `http://127.0.0.1:1234/v1` (`qwen3-4b-instruct-2507` Q4_K_M)

---

## Environment Commands Reference

### 1. Activating Virtual Environment
```powershell
.\.venv\Scripts\Activate.ps1
```

### 2. Checking Python Version
```powershell
.\.venv\Scripts\python.exe --version
# Expected: Python 3.11.9
```

### 3. Checking GPU & CUDA Access
```powershell
.\.venv\Scripts\python.exe scripts/check_gpu.py
# Verifies PyTorch CUDA detection, GPU name (RTX 3050), and VRAM
```

### 4. Checking Core Package Dependencies
```powershell
.\.venv\Scripts\python.exe scripts/check_environment.py
# Verifies imports for PyTorch, Transformers, spaCy, Sentence Transformers, FAISS, LangChain, FastAPI, Pydantic
```

### 5. Checking spaCy Model
```powershell
.\.venv\Scripts\python.exe -c "import spacy; nlp = spacy.load('en_core_web_sm'); print('spaCy model loaded:', nlp.meta['name'], nlp.meta['version'])"
```

### 6. Checking Sentence Transformer & Embeddings
```powershell
.\.venv\Scripts\python.exe -c "from sentence_transformers import SentenceTransformer; m = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2'); emb = m.encode(['test']); print('Embedding shape:', emb.shape)"
```

### 7. Checking FAISS Indexing
```powershell
.\.venv\Scripts\python.exe -c "import faiss, numpy as np; index = faiss.IndexFlatIP(384); print('FAISS index created, d=384')"
```

### 8. Checking LM Studio Local API Connectivity
```powershell
.\.venv\Scripts\python.exe scripts/test_lm_studio.py
# Queries http://127.0.0.1:1234/v1/models and tests model qwen3-4b-instruct-2507
```

---

## Hardware Operating Guidance

- **Standard Development**: Silent/Standard mode is sufficient for coding and documentation.
- **GPU Workloads**: Connect charger and use Performance/Turbo mode when executing heavy ML training or local LLM inference.
