"""
ContractRisk AI - Phase 7 RAG Live LM Studio Integration & Smoke Test Script

Tests end-to-end RAG pipeline functionality against live LM Studio server (http://127.0.0.1:1234/v1)
using synthetic contract corpus for supported and unsupported queries.
"""

import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.clause_segmentation.models import SegmentedClause
from src.document_processing.models import SourceType
from src.embeddings import ClauseEmbedder, FAISSIndexManager
from src.rag import LLMGenerator, RAGPipeline


def build_synthetic_rag_corpus() -> list[SegmentedClause]:
    """Generates synthetic contract clauses covering key legal topics."""
    return [
        SegmentedClause(
            clause_id="rag_corpus:clause:001",
            document_id="msa_2026_contract",
            clause_number="1.1",
            clause_heading="Confidentiality Obligations",
            clause_text=(
                "1.1 Confidentiality Obligations. Each Party agrees to maintain all proprietary technical data, "
                "trade secrets, and financial information disclosed by the other Party in strict confidence. "
                "Confidential Information shall not be disclosed to any third party without prior written consent."
            ),
            source_type=SourceType.PDF,
            source_pages=[1],
            character_count=298,
            word_count=42,
        ),
        SegmentedClause(
            clause_id="rag_corpus:clause:002",
            document_id="msa_2026_contract",
            clause_number="2.1",
            clause_heading="Termination for Convenience",
            clause_text=(
                "2.1 Termination for Convenience. Either Party may terminate this Agreement at any time "
                "for convenience upon providing at least thirty (30) days prior written notice to the other Party."
            ),
            source_type=SourceType.PDF,
            source_pages=[1],
            character_count=211,
            word_count=32,
        ),
        SegmentedClause(
            clause_id="rag_corpus:clause:003",
            document_id="msa_2026_contract",
            clause_number="3.1",
            clause_heading="Intellectual Property Ownership",
            clause_text=(
                "3.1 Intellectual Property Ownership. All custom software, inventions, source code, and "
                "deliverables created or developed under this Agreement shall remain the sole and exclusive "
                "property of Licensor. Licensee receives no ownership rights."
            ),
            source_type=SourceType.PDF,
            source_pages=[2],
            character_count=252,
            word_count=35,
        ),
        SegmentedClause(
            clause_id="rag_corpus:clause:004",
            document_id="msa_2026_contract",
            clause_number="4.1",
            clause_heading="Payment Terms",
            clause_text=(
                "4.1 Payment Terms. Licensee shall pay all undisputed invoices within thirty (30) days "
                "of the invoice date. Late payments shall accrue interest at the rate of 1.5% per month."
            ),
            source_type=SourceType.PDF,
            source_pages=[2],
            character_count=192,
            word_count=29,
        ),
        SegmentedClause(
            clause_id="rag_corpus:clause:005",
            document_id="msa_2026_contract",
            clause_number="5.1",
            clause_heading="Indemnification",
            clause_text=(
                "5.1 Indemnification. Licensee agrees to defend, indemnify, and hold harmless Licensor "
                "against any third-party claims, losses, or damages arising out of Licensee's misuse of the Software."
            ),
            source_type=SourceType.PDF,
            source_pages=[3],
            character_count=214,
            word_count=31,
        ),
    ]


def run_verification():
    print("=" * 70)
    print(" CONTRACTRISK AI -- PHASE 7 RAG LIVE LM STUDIO INTEGRATION TEST")
    print("=" * 70)

    embedder = ClauseEmbedder()
    index_manager = FAISSIndexManager()
    generator = LLMGenerator()

    # Discover active model ID from LM Studio /v1/models
    active_model = generator.get_active_model_id()
    print(f"  [INFO] LM Studio Base URL : {generator.base_url}")
    print(f"  [INFO] Active Model ID    : {active_model}")

    corpus = build_synthetic_rag_corpus()
    index_manager.build_index(corpus, embedder)
    print(f"  [OK] Indexed {index_manager.total_vectors} synthetic contract clauses into FAISS.")

    pipeline = RAGPipeline(
        index_manager=index_manager,
        embedder=embedder,
        generator=generator,
    )

    test_queries = [
        {
            "category": "Confidentiality",
            "query": "What are the confidentiality obligations?",
            "expected_insufficient": False,
        },
        {
            "category": "Termination",
            "query": "When can the agreement be terminated?",
            "expected_insufficient": False,
        },
        {
            "category": "Intellectual Property",
            "query": "Who owns the intellectual property created under the agreement?",
            "expected_insufficient": False,
        },
        {
            "category": "Payment Terms",
            "query": "What are the payment terms and invoice due dates?",
            "expected_insufficient": False,
        },
        {
            "category": "Unsupported Query (Governing Law)",
            "query": "What is the governing law and choice of venue of this agreement?",
            "expected_insufficient": True,
        },
    ]

    print("\n" + "=" * 70)
    print(" RUNNING SEMANTIC RAG GROUNDING SANITY CHECKS")
    print("=" * 70)

    for idx, test in enumerate(test_queries, start=1):
        q = test["query"]
        cat = test["category"]
        exp_insuf = test["expected_insufficient"]

        print(f"\n[QUERY {idx}] Category: {cat}")
        print(f"  Query: '{q}'")

        response = pipeline.answer_query(q, top_k=3, similarity_threshold=0.60)

        print(f"  Model ID              : {response.model_name}")
        print(f"  Insufficient Evidence : {response.insufficient_evidence}")
        print(f"  Retrieved Evidence    : {len(response.evidence)} items")
        print(f"  Citations Count       : {len(response.citations)}")
        print(f"  Answer                :\n    {response.answer}")

        if response.citations:
            cit_str = ", ".join(f"[{c.clause_number or c.clause_id}, p.{c.source_pages}]" for c in response.citations)
            print(f"  Verified Citations    : {cit_str}")

        if exp_insuf:
            assert response.insufficient_evidence is True
            assert "insufficient" in response.answer.lower()
            print("  [OK] Correctly flagged insufficient evidence for unindexed query.")
        else:
            assert response.insufficient_evidence is False
            assert len(response.evidence) > 0
            assert len(response.citations) > 0
            print("  [OK] Successfully generated grounded answer with verified citations.")

    print("\n" + "=" * 70)
    print(" [SUCCESS] ALL PHASE 7 RAG INTEGRATION TESTS PASSED CLEANLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_verification()
