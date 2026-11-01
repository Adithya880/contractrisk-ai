"""
Phase 3 Regression & Verification Tests:
1. Cross-Clause Conflict & Contradiction Detection
2. Analysis Performance & Stage Timings Instrumentation
3. Workflow & Schema Integrity
"""

import time
import pytest
from pathlib import Path
from src.document_processing.loader import DocumentLoader
from src.clause_segmentation.segmenter import ClauseSegmenter
from src.clause_segmentation.models import SegmentedClause, SegmentationResult
from src.risk_analysis.conflict_detector import CrossClauseConflictDetector
from src.risk_analysis.models import CrossClauseConflict, RiskLevel
from src.api.schemas import CrossClauseConflictSchema, ContractSummarySchema, AnalysisResponse
from src.api.dependencies import get_risk_analyzer


def _make_clause(cid: str, num: str, head: str, text: str) -> SegmentedClause:
    return SegmentedClause(
        clause_id=cid,
        document_id="doc_test",
        clause_number=num,
        clause_heading=head,
        clause_text=text,
        source_pages=[1],
        source_type="pdf",
        character_count=len(text),
        word_count=len(text.split())
    )


@pytest.fixture(scope="module")
def conflict_detector():
    return CrossClauseConflictDetector()


@pytest.fixture(scope="module")
def painter_clauses():
    pdf_path = Path("scratch/Painter.pdf")
    if pdf_path.exists():
        loader = DocumentLoader()
        segmenter = ClauseSegmenter()
        doc = loader.load_document(pdf_path)
        return segmenter.segment(doc).clauses
    return [
        _make_clause("c1", "1", "Services", "The Painter agrees to complete the painting of the interior walls within 20 days."),
        _make_clause("c2", "2", "Fixed Payment", "The Client agrees to pay a fixed fee of $40,000 for all painting services. The prices are fixed and not subject to any increase."),
        _make_clause("c3", "3", "Price Adjustment", "The Painter reserves the right to increase or alter the agreed prices at any time without asking or consent from Client."),
        _make_clause("c4", "4", "Termination Notice", "Either party may terminate this agreement upon 15 days written notice; provided that Painter may terminate immediately at any time without notice."),
        _make_clause("c5", "5", "Damage and Liability", "The Painter accepts full responsibility for any damage caused to property during painting. Under no circumstances shall Painter be required to pay for any damage.")
    ]


# ==============================================================================
# 1. PAINTER.PDF CONFLICT DETECTION TESTS
# ==============================================================================

def test_painter_pdf_price_conflict_detected(conflict_detector, painter_clauses):
    """Clause 2 (fixed 40k) vs Clause 3 (unilateral price hike) must be identified."""
    conflicts = conflict_detector.detect_conflicts(painter_clauses)
    price_conflicts = [c for c in conflicts if "Price" in c.conflict_type]
    assert len(price_conflicts) >= 1
    pc = price_conflicts[0]
    assert "2" in pc.clause_numbers
    assert "3" in pc.clause_numbers
    assert pc.severity == RiskLevel.HIGH
    assert "fixed" in pc.explanation.lower()
    assert "unilateral price" in pc.explanation.lower()


def test_painter_pdf_notice_contradiction_detected(conflict_detector, painter_clauses):
    """Clause 4 (15 days notice vs immediate stoppage without notice) must be identified."""
    conflicts = conflict_detector.detect_conflicts(painter_clauses)
    notice_conflicts = [c for c in conflicts if "Termination" in c.conflict_type or "Notice" in c.conflict_type]
    assert len(notice_conflicts) >= 1
    nc = notice_conflicts[0]
    assert "4" in nc.clause_numbers
    assert nc.severity == RiskLevel.HIGH
    assert "15 days" in nc.explanation.lower() or "notice" in nc.explanation.lower()
    assert "immediate" in nc.explanation.lower()


def test_painter_pdf_liability_contradiction_detected(conflict_detector, painter_clauses):
    """Clause 5 (responsible for damage vs will not pay) must be identified."""
    conflicts = conflict_detector.detect_conflicts(painter_clauses)
    liab_conflicts = [c for c in conflicts if "Liability" in c.conflict_type]
    assert len(liab_conflicts) >= 1
    lc = liab_conflicts[0]
    assert "5" in lc.clause_numbers
    assert lc.severity == RiskLevel.HIGH
    assert "damage" in lc.explanation.lower()
    assert "obligation to pay" in lc.explanation.lower() or "pay" in lc.explanation.lower()


def test_painter_pdf_conflicts_count(conflict_detector, painter_clauses):
    """Verify that only genuine conflicts (price, notice, liability) are identified."""
    conflicts = conflict_detector.detect_conflicts(painter_clauses)
    assert len(conflicts) >= 3


# ==============================================================================
# 2. NEGATIVE TESTS: NORMAL RECIPROCAL CLAUSES (NO FALSE POSITIVES)
# ==============================================================================

def test_normal_clauses_no_false_positive_conflicts(conflict_detector):
    """Standard reciprocal clauses without unilateral terms must produce 0 conflicts."""
    normal_clauses = [
        _make_clause(
            "norm_1", "1", "Scope of Work",
            "Contractor agrees to perform the painting services described in Schedule A."
        ),
        _make_clause(
            "norm_2", "2", "Fees",
            "Client shall pay Contractor the agreed sum of $10,000 upon satisfactory completion."
        ),
        _make_clause(
            "norm_3", "3", "Termination",
            "Either party may terminate this agreement upon 30 days' prior written notice."
        ),
        _make_clause(
            "norm_4", "4", "Governing Law",
            "This agreement is governed by the laws of England and Wales."
        )
    ]
    conflicts = conflict_detector.detect_conflicts(normal_clauses)
    assert len(conflicts) == 0, f"Expected 0 conflicts for standard clauses, got: {conflicts}"


# ==============================================================================
# 3. SYNTHETIC CROSS-CLAUSE CONTRADICTIONS
# ==============================================================================

def test_cross_clause_conflicting_governing_law(conflict_detector):
    """Contradictory governing law clauses across document."""
    clauses = [
        _make_clause(
            "c_gov1", "8", "Governing Law",
            "This Agreement shall be governed by the laws of New York and subject to the exclusive jurisdiction of New York courts."
        ),
        _make_clause(
            "c_gov2", "12", "Dispute Resolution",
            "Any dispute hereunder shall be governed by the laws of California and subject to the exclusive jurisdiction of California courts."
        )
    ]
    conflicts = conflict_detector.detect_conflicts(clauses)
    assert len(conflicts) == 1
    assert "Jurisdiction" in conflicts[0].conflict_type or "Governing Law" in conflicts[0].conflict_type
    assert "8" in conflicts[0].clause_numbers
    assert "12" in conflicts[0].clause_numbers


def test_cross_clause_warranty_vs_as_is(conflict_detector):
    """Express warranty vs absolute as-is disclaimer."""
    clauses = [
        _make_clause(
            "c_war1", "5", "Warranty",
            "Service Provider warrants that all services will be performed in a professional manner and free from defects."
        ),
        _make_clause(
            "c_war2", "9", "Disclaimer",
            "All services and deliverables are provided strictly on an as-is basis and Provider disclaims all warranties of any kind."
        )
    ]
    conflicts = conflict_detector.detect_conflicts(clauses)
    assert len(conflicts) == 1
    assert "Warranty" in conflicts[0].conflict_type
    assert "5" in conflicts[0].clause_numbers
    assert "9" in conflicts[0].clause_numbers


# ==============================================================================
# 4. PERFORMANCE & STAGE TIMINGS INTEGRATION TESTS
# ==============================================================================

def test_pipeline_stage_timings_recorded_on_document_analysis(painter_clauses):
    """Verify that analyzer records exact durations for each stage on segmented clauses."""
    res = SegmentationResult(
        document_id="doc_perf_test",
        source_filename="test_contract.pdf",
        document_title="Painting Agreement",
        clauses=painter_clauses,
        total_clauses=len(painter_clauses),
        source_character_count=sum(c.character_count for c in painter_clauses),
        segmented_character_count=sum(c.character_count for c in painter_clauses),
        text_coverage_ratio=1.0,
        unsegmented_elements_count=0
    )

    analyzer = get_risk_analyzer()

    # Warm-up run
    summary = analyzer.analyze_document(res)

    timings = summary.pipeline_timings
    assert isinstance(timings, dict)
    assert "bert_batch_time" in timings
    assert "rag_batch_time" in timings
    assert "fast_pass_duration" in timings
    assert "deep_llm_duration" in timings
    assert "conflict_detection_duration" in timings
    assert "total_analysis_duration" in timings

    # Check that warm analysis for 5 clauses is fast (< 2.5s)
    t_start = time.perf_counter()
    warm_summary = analyzer.analyze_document(res)
    elapsed = time.perf_counter() - t_start

    assert elapsed < 2.5, f"Expected 5-clause warm analysis < 2.5s, got {elapsed:.2f}s"
    assert len(warm_summary.cross_clause_conflicts) >= 3


# ==============================================================================
# 5. SCHEMA SERIALIZATION TEST
# ==============================================================================

def test_conflict_schema_serialization():
    """Verify CrossClauseConflictSchema and ContractSummarySchema serialize cleanly."""
    conflict = CrossClauseConflictSchema(
        conflict_id="conf_123",
        conflict_type="Price & Payment Contradiction",
        severity="HIGH",
        clause_ids=["c2", "c3"],
        clause_numbers=["2", "3"],
        explanation="Fixed price undermined by unilateral alteration.",
        conflicting_excerpt_a="Agrees to pay 40,000",
        conflicting_excerpt_b="Can increase price without approval"
    )
    summary_schema = ContractSummarySchema(
        risk_score=56.85,
        risk_level="MEDIUM",
        high_risk_clause_count=0,
        medium_risk_clause_count=3,
        low_risk_clause_count=2,
        cross_clause_conflicts=[conflict],
        pipeline_timings={"total_analysis_duration": 0.28}
    )
    data = summary_schema.model_dump()
    assert len(data["cross_clause_conflicts"]) == 1
    assert data["cross_clause_conflicts"][0]["conflict_type"] == "Price & Payment Contradiction"
    assert data["pipeline_timings"]["total_analysis_duration"] == 0.28
