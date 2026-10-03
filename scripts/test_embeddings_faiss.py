"""
ContractRisk AI - Phase 6 Embeddings & FAISS Verification & Smoke Test Script

This script verifies end-to-end functionality of Phase 4 loader -> Phase 5 segmenter ->
Phase 6 embedding generation, FAISS index construction, similarity search, and persistence.
"""

import json
import os
import sys
import tempfile
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import fitz
from src.clause_segmentation import ClauseSegmenter
from src.document_processing import DocumentLoader
from src.embeddings import ClauseEmbedder, FAISSIndexManager


def create_sample_contract_pdf(file_path: Path) -> None:
    """Creates a synthetic multi-clause PDF contract."""
    doc = fitz.open()

    p1 = doc.new_page()
    p1.insert_text(
        (50, 50),
        "COMMERCIAL LEASE AGREEMENT\n\n"
        "ARTICLE I. DEFINITIONS AND PREMISES\n"
        "1.1 Premises. Premises refers to Suite 400 located at 500 Commercial Blvd.\n"
        "1.2 Rent. Rent means the monthly fee of $5,000.00 USD payable on the 1st of each month.\n\n"
        "ARTICLE II. INDEMNIFICATION AND LIABILITY\n"
        "2.1 Tenant Indemnity. Tenant shall indemnify, defend, and hold harmless Landlord "
        "from third-party claims arising from Tenant's use of the Premises.\n"
        "2.2 Cap on Liability. In no event shall Landlord's cumulative liability exceed "
        "the total rent paid by Tenant in the preceding twelve (12) months.\n\n"
        "ARTICLE III. CONFIDENTIALITY\n"
        "3.1 Confidentiality. Each party agrees to maintain non-public financial and operational "
        "information in strict confidence."
    )

    doc.save(file_path)
    doc.close()


def run_verification():
    print("=" * 70)
    print(" CONTRACTRISK AI -- PHASE 6 EMBEDDINGS & FAISS SMOKE TEST")
    print("=" * 70)
    print(" [NOTE] Indexing a synthetic TEST/DEMO contract corpus.")

    loader = DocumentLoader()
    segmenter = ClauseSegmenter()
    embedder = ClauseEmbedder()
    index_manager = FAISSIndexManager()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        pdf_path = tmp_path / "sample_lease.pdf"
        index_dir = tmp_path / "faiss_test_index"

        create_sample_contract_pdf(pdf_path)

        print("\n[STEP 1] Ingesting & Segmenting Contract (Phase 4 -> Phase 5)...")
        extracted_doc = loader.load_document(pdf_path)
        seg_result = segmenter.segment(extracted_doc)
        print(f"  [OK] Extracted {seg_result.total_clauses} clauses from contract.")

        print("\n[STEP 2] Generating L2-Normalized Embeddings & Building FAISS Index...")
        vector_count = index_manager.build_index(seg_result.clauses, embedder)
        assert vector_count == seg_result.total_clauses
        assert index_manager.total_vectors == vector_count
        print(f"  [OK] Successfully indexed {vector_count} 384-dimensional vectors in FAISS IndexFlatIP.")

        print("\n[STEP 3] Performing Semantic Retrieval Sanity Check...")
        query = "What are the tenant indemnification and liability obligations?"
        print(f"  Query: '{query}'")

        results = index_manager.search(query, embedder, top_k=3)
        assert len(results) > 0
        top_result = results[0]

        print(f"  [OK] Top Retrieved Result:")
        print(f"       Clause ID        : {top_result.clause_id}")
        print(f"       Clause Number    : {top_result.clause_number}")
        print(f"       Clause Heading   : {top_result.clause_heading}")
        print(f"       Similarity Score : {top_result.similarity_score:.4f}")
        print(f"       Snippet          : {top_result.clause_text[:90]}...")

        # Sanity assertion: Top result must be Section 2.1 Tenant Indemnity
        assert "2.1" in (top_result.clause_number or "") or "Indemnity" in (top_result.clause_heading or "")
        assert top_result.similarity_score > 0.40

        print("\n[STEP 4] Testing Index Persistence & Reload Compatibility...")
        index_manager.save(index_dir)
        assert (index_dir / "contract_clauses.faiss").exists()
        assert (index_dir / "contract_clauses_metadata.json").exists()
        assert (index_dir / "manifest.json").exists()

        reloaded_manager = FAISSIndexManager()
        reloaded_manager.load(index_dir)
        assert reloaded_manager.total_vectors == vector_count

        post_reload_results = reloaded_manager.search(query, embedder, top_k=3)
        assert len(post_reload_results) == len(results)
        assert post_reload_results[0].clause_id == results[0].clause_id
        assert abs(post_reload_results[0].similarity_score - results[0].similarity_score) < 1e-5
        print("  [OK] Post-reload search produced identical retrieval results.")

    print("\n" + "=" * 70)
    print(" [SUCCESS] ALL PHASE 6 EMBEDDING & FAISS SMOKE TESTS PASSED CLEANLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_verification()
