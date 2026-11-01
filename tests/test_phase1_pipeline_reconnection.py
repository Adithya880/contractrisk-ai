"""
Phase 1 Integration Test Suite: Core AI Pipeline Reconnection
-------------------------------------------------------------
Verifies:
1. BERT inference wrapper (single and batch predictions).
2. Persistent FAISS vector index loading and semantic retrieval from reference corpus.
3. Analyzer integration (BERT categories assigned, RAG evidence retrieved).
4. Strictly transparent hybrid risk scoring without silent weight rescaling.
5. Supporting evidence serialization and schema compatibility.
"""

import tempfile
from pathlib import Path
import pytest
import pymupdf as fitz

from src.api.dependencies import get_risk_analyzer, get_bert_model, get_rag_pipeline
from src.clause_segmentation.models import SegmentedClause, SegmentationResult
from src.document_processing.loader import DocumentLoader
from src.document_processing.models import SourceType
from src.models.bert_predictor import get_bert_predictor
from src.risk_analysis.models import RiskLevel
from src.risk_analysis.scoring import HybridScorer
from src.api.schemas import ClauseAssessmentSchema, ComponentBreakdownSchema


def test_bert_clause_classification_diversity():
    """Verify BERT assigns distinct, accurate categories rather than defaulting to 'Other'."""
    predictor = get_bert_predictor()
    
    test_cases = [
        ("This Agreement shall be governed by and construed in accordance with the laws of New York.", ["Governing Law"]),
        ("In no event shall either party be liable for any indirect, special, or consequential damages.", ["Cap On Liability", "Uncapped Liability"]),
        ("Either party may terminate this agreement at any time upon thirty days prior written notice.", ["Termination For Convenience"]),
        ("Employee agrees not to engage in any competitive business activity for two years.", ["Non-Compete", "No-Solicit Of Employees"])
    ]
    
    for text, expected_categories in test_cases:
        label, conf = predictor.predict_clause(text)
        assert label in expected_categories, f"Expected one of '{expected_categories}', got '{label}' for: {text}"
        assert label != "Other", f"Clause defaulted to 'Other' for: {text}"
        assert 0.0 < conf <= 1.0


def test_faiss_persistent_corpus_retrieval():
    """Verify persistent FAISS index is loaded and retrieves relevant precedents."""
    rag_pipe = get_rag_pipeline()
    assert rag_pipe is not None, "RAG pipeline failed to initialize"
    assert rag_pipe.retriever.index_manager.total_vectors >= 9000
    
    query = "Neither party shall be liable for indirect, incidental, or consequential damages."
    evidence = rag_pipe.retriever.retrieve_evidence(query, top_k=3, similarity_threshold=0.40)
    
    assert len(evidence) > 0, "No evidence retrieved from reference corpus"
    top_item = evidence[0]
    assert top_item.similarity_score >= 0.70
    assert "liability" in top_item.clause_heading.lower() or "liability" in top_item.clause_text.lower()


def test_contract_risk_analyzer_hybrid_execution():
    """Verify ContractRiskAnalyzer executes BERT, Rule, RAG, and transparent scoring."""
    analyzer = get_risk_analyzer()
    assert analyzer.bert_classifier is not None, "BERT classifier not connected to analyzer"
    assert analyzer.rag_pipeline is not None, "RAG pipeline not connected to analyzer"
    
    # Test Governing Law clause
    gov_clause = SegmentedClause(
        clause_id="c_gov_01",
        document_id="doc_test",
        clause_number="1.1",
        clause_heading="Governing Law",
        clause_text="This Agreement shall be governed by and construed in accordance with the laws of the State of Delaware.",
        source_type=SourceType.PDF,
        source_pages=[1],
        character_count=100,
        word_count=18
    )
    
    assess = analyzer.analyze_clause(gov_clause, document_id="doc_test", skip_llm=True)
    
    # Verify BERT category is Governing Law, not Other
    assert assess.clause_type == "Governing Law"
    assert assess.bert_confidence > 0.50
    assert assess.score_breakdown.bert_component > 0.0
    
    # Verify RAG retrieved evidence from persistent corpus
    assert len(assess.evidence) > 0
    assert assess.score_breakdown.rag_component > 0.0
    assert assess.evidence[0]["similarity_score"] >= 0.70
    assert assess.evidence[0]["document_id"] == "reference_corpus"
    
    # Verify strict transparent scoring: 0.30 * BERT + 0.35 * Rule + 0.15 * RAG + 0.20 * LLM
    sb = assess.score_breakdown
    expected_score = round(
        0.30 * sb.bert_component +
        0.35 * sb.rule_component +
        0.15 * sb.rag_component +
        0.20 * sb.llm_component,
        2
    )
    assert assess.risk_score == expected_score, f"Expected {expected_score}, got {assess.risk_score}"
    assert assess.risk_level == RiskLevel.LOW


def test_transparent_scoring_no_rescaling():
    """Verify that when BERT or RAG returns 0, no silent dynamic rescaling occurs."""
    scorer = HybridScorer()
    
    # S_BERT = 0.0, S_Rule = 60.0, S_RAG = 0.0, S_LLM = 50.0
    # Expected: 0.30(0) + 0.35(60) + 0.15(0) + 0.20(50) = 21.0 + 10.0 = 31.0
    breakdown = scorer.compute_hybrid_score(
        bert_score=0.0,
        rule_score=60.0,
        rag_score=0.0,
        llm_score=50.0
    )
    assert breakdown.final_score == 31.0
    assert breakdown.bert_weight == 0.30
    assert breakdown.rule_weight == 0.35
    assert breakdown.rag_weight == 0.15
    assert breakdown.llm_weight == 0.20
    
    missing = HybridScorer.identify_missing_signals(breakdown)
    assert "BERT (no category risk signal)" in missing
    assert "RAG (no benchmark evidence)" in missing


def test_evidence_serialization_compatibility():
    """Verify evidence items are serialized cleanly into ClauseAssessmentSchema."""
    breakdown_schema = ComponentBreakdownSchema(
        bert_component=15.0,
        rule_component=0.0,
        rag_component=85.0,
        llm_component=15.0,
        final_score=20.0
    )
    
    evidence_data = [
        {
            "clause_id": "ref_00123",
            "source_clause_id": "ref_00123",
            "document_id": "reference_corpus",
            "clause_number": "REF-124",
            "clause_heading": "Governing Law",
            "clause_text": "This Agreement shall be governed by Delaware law.",
            "source_pages": [1],
            "similarity_score": 0.942
        }
    ]
    
    schema = ClauseAssessmentSchema(
        clause_id="c_01",
        clause_number="1.1",
        clause_heading="Governing Law",
        clause_text="Governed by Delaware law.",
        risk_score=20.0,
        risk_level="LOW",
        risk_category="Governing Law",
        bert_label="Governing Law",
        bert_confidence=0.85,
        rule_matches=[],
        component_score_breakdown=breakdown_schema,
        llm_explanation="Routine legal terms.",
        key_risk_factors=["Governing Law"],
        uncertainty="None",
        evidence=evidence_data,
        future_scenario=None
    )
    
    assert len(schema.evidence) == 1
    assert schema.evidence[0]["clause_id"] == "ref_00123"
    assert schema.evidence[0]["similarity_score"] == 0.942
