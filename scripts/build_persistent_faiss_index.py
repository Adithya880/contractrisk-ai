"""
Build Persistent FAISS Vector Index for ContractRisk AI
------------------------------------------------------
Indexes 9,447 reference contract clauses from data/processed/cleaned_clauses.csv
using ClauseEmbedder (all-MiniLM-L6-v2) and FAISSIndexManager (IndexFlatIP).
Saves the index, metadata, and manifest to models/faiss_index/.
Validates persistence, reloading, and semantic retrieval accuracy.
"""

import os
import sys
import time
import logging
from pathlib import Path

# Enable offline mode for cached HF models
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import numpy as np
import torch

from src.clause_segmentation.models import SegmentedClause
from src.document_processing.models import SourceType
from src.embeddings.embedder import ClauseEmbedder
from src.embeddings.index import FAISSIndexManager
from src.rag.retriever import RAGRetriever

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DATA_PATH = Path("data/processed/cleaned_clauses.csv")
OUTPUT_DIR = Path("models/faiss_index")


def build_and_persist_index():
    t0 = time.time()
    logger.info(f"Loading reference corpus from: {DATA_PATH.resolve()}")

    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Reference dataset not found at: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)
    logger.info(f"Loaded {len(df)} records from {DATA_PATH.name}")

    # Build SegmentedClause objects with full provenance
    clauses: list[SegmentedClause] = []
    skipped = 0

    for idx, row in df.iterrows():
        raw_text = row.get("cleaned_clause_text")
        if pd.isna(raw_text) or not str(raw_text).strip():
            raw_text = row.get("clause_text")

        text = str(raw_text).strip() if pd.notna(raw_text) else ""
        if not text:
            skipped += 1
            continue

        c_type = str(row.get("clause_type", "General")).strip()
        clause_id = f"ref_{idx:05d}"
        clause_num = f"REF-{idx+1}"

        clause = SegmentedClause(
            clause_id=clause_id,
            document_id="reference_corpus",
            clause_number=clause_num,
            clause_heading=c_type,
            clause_text=text,
            source_type=SourceType.PDF,
            source_pages=[1],
            character_count=len(text),
            word_count=len(text.split()),
        )
        clauses.append(clause)

    logger.info(f"Prepared {len(clauses)} valid reference clauses (skipped {skipped} empty).")

    # Initialize embedder and index manager
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Initializing ClauseEmbedder (all-MiniLM-L6-v2) on {device}...")
    embedder = ClauseEmbedder(device=device, batch_size=128)

    index_manager = FAISSIndexManager(dimension=ClauseEmbedder.EMBEDDING_DIM)

    # Build index
    logger.info(f"Embedding and indexing {len(clauses)} clauses...")
    t_embed = time.time()
    total_indexed = index_manager.build_index(clauses, embedder)
    embed_dur = time.time() - t_embed
    logger.info(f"Indexed {total_indexed} vectors in {embed_dur:.2f} seconds ({total_indexed/embed_dur:.1f} clauses/sec).")

    # Persist index to models/faiss_index/
    logger.info(f"Saving FAISS index to {OUTPUT_DIR.resolve()}...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    index_manager.save(OUTPUT_DIR)
    logger.info(f"[SUCCESS] FAISS index, metadata, and manifest saved successfully.")

    # Validation: Reload from disk into fresh manager
    logger.info("Validating persistence by loading from disk into a fresh FAISSIndexManager...")
    fresh_manager = FAISSIndexManager(dimension=ClauseEmbedder.EMBEDDING_DIM)
    fresh_manager.load(OUTPUT_DIR)
    assert fresh_manager.total_vectors == total_indexed, (
        f"Vector count mismatch after reload: {fresh_manager.total_vectors} vs {total_indexed}"
    )
    logger.info(f"[PASSED] Reloaded index contains exact vector count: {fresh_manager.total_vectors}")

    # Semantic Retrieval Verification
    retriever = RAGRetriever(index_manager=fresh_manager, embedder=embedder)
    test_queries = [
        "In no event shall either party be liable for any indirect, punitive, or consequential damages.",
        "This Agreement shall be governed by and construed in accordance with the laws of Delaware.",
        "Either party may terminate this Agreement without cause upon giving 30 days prior written notice."
    ]

    logger.info("\n--- SEMANTIC RETRIEVAL VERIFICATION ---")
    for q in test_queries:
        logger.info(f"\nQuery: '{q[:75]}...'")
        evidence = retriever.retrieve_evidence(q, top_k=2, similarity_threshold=0.40)
        assert len(evidence) > 0, f"Retrieval failed for query: {q}"
        for i, item in enumerate(evidence, 1):
            logger.info(
                f"  Match {i}: [{item.clause_heading}] (sim: {item.similarity_score:.4f}, id: {item.clause_id}) -> {item.clause_text[:90]}..."
            )

    total_time = time.time() - t0
    logger.info(f"\n[DONE] FAISS Persistent Index Build & Validation completed in {total_time:.2f} seconds.")


if __name__ == "__main__":
    build_and_persist_index()
