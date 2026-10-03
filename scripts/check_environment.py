"""
Environment Package Verification Script for ContractRisk AI
------------------------------------------------------------
Verifies imports and versions for:
- Python
- PyTorch
- Transformers
- spaCy (including loading en_core_web_sm)
- Sentence Transformers
- FAISS
- LangChain
- FastAPI
- Pydantic
Reports actual errors if any package fails to import.
"""

import sys
import importlib

def check_package(package_name, import_name=None):
    if import_name is None:
        import_name = package_name
    try:
        module = importlib.import_module(import_name)
        version = getattr(module, "__version__", "installed")
        print(f"  [OK] {package_name:<22} : {version}")
        return True, version
    except Exception as e:
        print(f"  [FAIL] {package_name:<22} : IMPORT ERROR -> {e}")
        return False, str(e)

def check_environment():
    print("=" * 65)
    print(" CONTRACTRISK AI — PHASE 1 ENVIRONMENT VERIFICATION")
    print("=" * 65)

    py_version = sys.version.split()[0]
    print(f"Python Version: {py_version}")

    print("\nVerifying Phase 1 Package Dependencies:")
    packages = [
        ("PyTorch", "torch"),
        ("Transformers", "transformers"),
        ("spaCy", "spacy"),
        ("Sentence Transformers", "sentence_transformers"),
        ("FAISS", "faiss"),
        ("LangChain", "langchain"),
        ("FastAPI", "fastapi"),
        ("Pydantic", "pydantic"),
    ]

    all_passed = True
    for name, import_name in packages:
        status, _ = check_package(name, import_name)
        if not status:
            all_passed = False

    print("\nVerifying spaCy Model (en_core_web_sm):")
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        model_ver = nlp.meta.get("version", "loaded")
        print(f"  [OK] en_core_web_sm          : {model_ver}")
    except Exception as e:
        print(f"  [FAIL] en_core_web_sm model load failed: {e}")
        all_passed = False

    print("\nVerifying Sentence Transformers & FAISS Indexing:")
    try:
        from sentence_transformers import SentenceTransformer
        import faiss
        import numpy as np

        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        sample_text = ["This is a test legal contract clause regarding indemnification."]
        embeddings = model.encode(sample_text, convert_to_numpy=True)
        dim = embeddings.shape[1]
        print(f"  [OK] sentence-transformers/all-MiniLM-L6-v2 loaded.")
        print(f"  [OK] Generated embedding dimension: {dim}")

        embeddings = embeddings.astype(np.float32)
        faiss.normalize_L2(embeddings)
        index = faiss.IndexFlatIP(dim)
        index.add(embeddings)
        print(f"  [OK] FAISS IndexFlatIP test search index count: {index.ntotal}")

    except Exception as e:
        print(f"  [FAIL] Sentence Transformers / FAISS verification failed: {e}")
        all_passed = False

    print("=" * 65)
    if all_passed:
        print(" [SUMMARY] All Phase 1 environment verification tests PASSED!")
    else:
        print(" [SUMMARY] One or more environment checks FAILED.")
    print("=" * 65)
    return all_passed

if __name__ == "__main__":
    success = check_environment()
    sys.exit(0 if success else 1)
