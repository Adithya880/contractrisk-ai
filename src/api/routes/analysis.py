










"""
Analysis route module for POST /api/v1/analyze and document read endpoints.
Ingests PDF and DOCX contracts, executes complete Phase 4-8.2.1 pipeline,
persists full analysis results to relational database (Phase 9),
and returns structured risk and future scenario assessments.
"""

import os
import time
import hashlib
import tempfile
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from src.api.dependencies import (
    get_document_loader,
    get_clause_segmenter,
    get_risk_analyzer,
    get_scenario_predictor
)
from src.api.schemas import (
    AnalysisResponse,
    DocumentMetadataSchema,
    ContractSummarySchema,
    ClauseAssessmentSchema,
    RuleMatchSchema,
    ComponentBreakdownSchema,
    FutureScenarioSchema,
    CrossClauseConflictSchema
)
from src.document_processing.loader import DocumentLoader
from src.clause_segmentation.segmenter import ClauseSegmenter
from src.risk_analysis.analyzer import ContractRiskAnalyzer
from src.risk_analysis.scenario_predictor import FutureScenarioPredictor
from src.risk_analysis.models import RiskLevel
from src.document_processing.exceptions import (
    UnsupportedFileTypeError,
    CorruptedDocumentError,
    EmptyDocumentError
)
from src.database.connection import get_db, get_db_session
from src.database.repositories import ContractRepository

logger = logging.getLogger(__name__)

router = APIRouter()

MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB Limit
ALLOWED_EXTENSIONS = {".pdf", ".docx"}

# In-memory tracking of real-time pipeline execution progress per task ID
_ANALYSIS_PROGRESS: Dict[str, Dict[str, Any]] = {}


def _update_progress(task_id: Optional[str], stage: int, pct: int, stage_name: str):
    """Update pipeline execution state for a client tracking task."""
    if not task_id:
        return
    _ANALYSIS_PROGRESS[task_id] = {
        "stage": stage,
        "pct": pct,
        "stage_name": stage_name,
        "updated_at": time.time(),
    }
    # Keep dictionary bounded
    if len(_ANALYSIS_PROGRESS) > 200:
        oldest_key = next(iter(_ANALYSIS_PROGRESS))
        _ANALYSIS_PROGRESS.pop(oldest_key, None)


@router.get(
    "/analysis/progress/{task_id}",
    summary="Get Pipeline Execution Progress",
    description="Poll real-time execution stage and completion percentage for a given task ID."
)
def get_analysis_progress(task_id: str):
    """Return real-time stage progress for an active analysis task."""
    info = _ANALYSIS_PROGRESS.get(task_id)
    if info:
        return info
    return {"stage": 0, "pct": 0, "stage_name": "Document extraction"}


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze Contract Risk & Predict Future Scenarios",
    description=(
        "Upload a PDF or DOCX contract document to execute full document processing, "
        "clause segmentation, BERT classification, hybrid risk scoring, RAG evidence retrieval, "
        "local Qwen3 risk explanation, evidence-grounded future scenario prediction, and database persistence."
    )
)
def analyze_contract(
    request: Request,
    file: UploadFile = File(..., description="PDF (.pdf) or DOCX (.docx) contract file."),
    loader: DocumentLoader = Depends(get_document_loader),
    segmenter: ClauseSegmenter = Depends(get_clause_segmenter),
    analyzer: ContractRiskAnalyzer = Depends(get_risk_analyzer),
    scenario_predictor: FutureScenarioPredictor = Depends(get_scenario_predictor)
) -> AnalysisResponse:
    """Execute complete ContractRisk AI pipeline on an uploaded contract file."""
    task_id = request.headers.get("X-Task-ID") if hasattr(request, "headers") else None
    _update_progress(task_id, stage=0, pct=0, stage_name="Document extraction")

    # 1. File Extension & Format Validation
    filename = file.filename or "contract"
    ext = Path(filename).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Only PDF (.pdf) and DOCX (.docx) contracts are supported."
        )

    # 2. Read File Bytes & Validate File Size
    try:
        content_bytes = file.file.read()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read uploaded file contents."
        )

    if not content_bytes or len(content_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty."
        )

    if len(content_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed limit of {MAX_FILE_SIZE_BYTES // (1024*1024)} MB."
        )

    # 3. Create Temporary File & Execute Pipeline
    temp_file = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
    temp_path = temp_file.name

    try:
        temp_file.write(content_bytes)
        temp_file.close()

        # Step A: Ingestion & Normalization (Phase 4)
        _update_progress(task_id, stage=0, pct=12, stage_name="Document extraction")
        try:
            extracted_doc = loader.load_document(temp_path)
            extracted_doc.source_filename = filename
        except UnsupportedFileTypeError as e:
            raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=str(e))
        except (EmptyDocumentError, CorruptedDocumentError) as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Document parsing error: {e}")
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to process document: {e}")

        # Step B: Clause Segmentation (Phase 5)
        _update_progress(task_id, stage=1, pct=25, stage_name="Clause segmentation")
        try:
            segmentation_result = segmenter.segment(extracted_doc)
            segmentation_result.source_filename = filename
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Clause segmentation failed: {e}")

        if not segmentation_result.clauses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document contains no extractable legal clauses."
            )

        # Step C: Hybrid Risk Analysis (Phases 3 + 7.1 + 7)
        def progress_cb(stage: int, pct: int, name: str):
            _update_progress(task_id, stage, pct, name)

        try:
            summary = analyzer.analyze_document(segmentation_result, progress_callback=progress_cb)
            summary.source_filename = filename
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Risk analysis execution failed: {e}")

        # Determine target assessments for database persistence & response:
        # Preserve all evaluated clauses if available, otherwise fallback to highest_risk_assessments
        target_assessments = summary.all_assessments if summary.all_assessments else summary.highest_risk_assessments

        # Helper to format supporting evidence citations with precedent details
        def _format_citations(raw_cits, assess_evidence, target_clause_id):
            ev_map = {str(e.get("clause_id")): e for e in assess_evidence if isinstance(e, dict)}
            formatted = []
            for cit in raw_cits:
                c_dict = cit.model_dump() if hasattr(cit, "model_dump") else (dict(cit) if isinstance(cit, dict) else {"clause_id": str(cit)})
                cid = str(c_dict.get("clause_id", ""))
                if cid in ev_map:
                    ev = ev_map[cid]
                    c_dict["source_type"] = "precedent_benchmark"
                    c_dict["similarity_score"] = ev.get("similarity_score", 0.0)
                    c_dict["source_clause_id"] = ev.get("source_clause_id", cid)
                    c_dict["document_id"] = ev.get("document_id", "reference_corpus")
                    c_dict["clause_heading"] = ev.get("clause_heading", "Benchmark Precedent")
                    c_dict["clause_text"] = ev.get("clause_text", "")
                elif cid == target_clause_id:
                    c_dict["source_type"] = "target_clause"
                    c_dict["source_clause_id"] = cid
                else:
                    c_dict["source_type"] = "precedent_benchmark"
                formatted.append(c_dict)
            return formatted

        # Step D: Future Scenario Collection (Phase 7.2 / 7.2.1)
        # Deep candidate clauses already have pre-computed scenarios attached from unified generation!
        scenario_map: Dict[str, FutureScenarioSchema] = {}
        for assess in target_assessments:
            if assess.risk_level in (RiskLevel.HIGH, RiskLevel.MEDIUM):
                precomputed = getattr(assess, "future_scenario", None)
                if precomputed is not None:
                    scenario_map[assess.clause_id] = FutureScenarioSchema(
                        scenario_id=precomputed.scenario_id,
                        clause_id=precomputed.clause_id,
                        clause_number=precomputed.clause_number,
                        scenario_title=precomputed.scenario_title,
                        trigger_condition=precomputed.trigger_condition,
                        scenario_description=precomputed.scenario_description,
                        possible_consequence=precomputed.possible_consequence,
                        supporting_evidence=_format_citations(precomputed.supporting_evidence, assess.evidence, assess.clause_id),
                        assumptions=precomputed.assumptions,
                        uncertainty=precomputed.uncertainty,
                        fallback_active=precomputed.fallback_active,
                        disclaimer=precomputed.disclaimer
                    )
                else:
                    if scenario_predictor.generator.is_available(timeout=0.5):
                        try:
                            scen = scenario_predictor.predict_scenario(assess)
                            if scen is not None:
                                scenario_map[assess.clause_id] = FutureScenarioSchema(
                                    scenario_id=scen.scenario_id,
                                    clause_id=scen.clause_id,
                                    clause_number=scen.clause_number,
                                    scenario_title=scen.scenario_title,
                                    trigger_condition=scen.trigger_condition,
                                    scenario_description=scen.scenario_description,
                                    possible_consequence=scen.possible_consequence,
                                    supporting_evidence=_format_citations(scen.supporting_evidence, assess.evidence, assess.clause_id),
                                    assumptions=scen.assumptions,
                                    uncertainty=scen.uncertainty,
                                    fallback_active=scen.fallback_active,
                                    disclaimer=scen.disclaimer
                                )
                        except Exception:
                            pass
            # NORMAL and LOW-risk clauses bypass Qwen3 scenario generation: scenario_map[assess.clause_id] remains None

        # Step E: Phase 9 Database Persistence
        _update_progress(task_id, stage=7, pct=95, stage_name="Final analysis")
        try:
            with get_db_session() as session:
                repo = ContractRepository(session)
                repo.save_analysis(
                    summary=summary,
                    all_assessments=target_assessments,
                    scenario_map=scenario_map,
                    filename=filename,
                    document_type="PDF" if ext == ".pdf" else "DOCX"
                )
        except Exception as db_err:
            logger.warning(f"Database persistence skipped/failed: {db_err}")
            # If database is offline or not configured, API still returns valid analysis response
            # unless strict persistence is enforced

        # Step F: Construct API Response Schemas (Preserved 100% compatible)
        doc_schema = DocumentMetadataSchema(
            document_id=summary.document_id,
            filename=filename,
            document_type="PDF" if ext == ".pdf" else "DOCX",
            number_of_clauses=summary.analyzed_clauses_count
        )

        comb_scen = getattr(summary, "combined_scenario", None)
        comb_scen_schema = None
        if comb_scen:
            comb_scen_schema = FutureScenarioSchema(
                scenario_id=comb_scen.scenario_id,
                clause_id=comb_scen.clause_id,
                clause_number=comb_scen.clause_number,
                scenario_title=comb_scen.scenario_title,
                trigger_condition=comb_scen.trigger_condition,
                scenario_description=comb_scen.scenario_description,
                possible_consequence=comb_scen.possible_consequence,
                supporting_evidence=[
                    cit.model_dump() if hasattr(cit, "model_dump") else (dict(cit) if isinstance(cit, dict) else {"clause_id": str(cit)})
                    for cit in getattr(comb_scen, "supporting_evidence", [])
                ],
                assumptions=getattr(comb_scen, "assumptions", []),
                uncertainty=getattr(comb_scen, "uncertainty", ""),
                fallback_active=getattr(comb_scen, "fallback_active", False),
                disclaimer=getattr(comb_scen, "disclaimer", "")
            )

        conflict_schemas = [
            CrossClauseConflictSchema(
                conflict_id=c.conflict_id,
                conflict_type=c.conflict_type,
                severity=c.severity.value if hasattr(c.severity, "value") else str(c.severity),
                clause_ids=c.clause_ids,
                clause_numbers=c.clause_numbers,
                explanation=c.explanation,
                conflicting_excerpt_a=c.conflicting_excerpt_a,
                conflicting_excerpt_b=c.conflicting_excerpt_b
            )
            for c in getattr(summary, "cross_clause_conflicts", [])
        ]
        intra_conflict_schemas = [
            CrossClauseConflictSchema(
                conflict_id=c.conflict_id,
                conflict_type=c.conflict_type,
                severity=c.severity.value if hasattr(c.severity, "value") else str(c.severity),
                clause_ids=c.clause_ids,
                clause_numbers=c.clause_numbers,
                explanation=c.explanation,
                conflicting_excerpt_a=c.conflicting_excerpt_a,
                conflicting_excerpt_b=c.conflicting_excerpt_b
            )
            for c in getattr(summary, "intra_clause_contradictions", [])
        ]
        pipeline_timings = getattr(summary, "pipeline_timings", {})

        summary_schema = ContractSummarySchema(
            risk_score=summary.contract_risk_score,
            risk_level=summary.contract_risk_level.value,
            normal_risk_clause_count=summary.normal_risk_clauses_count,
            high_risk_clause_count=summary.high_risk_clauses_count,
            medium_risk_clause_count=summary.medium_risk_clauses_count,
            low_risk_clause_count=summary.low_risk_clauses_count,
            combined_scenario=comb_scen_schema,
            cross_clause_conflicts=conflict_schemas,
            intra_clause_contradictions=intra_conflict_schemas,
            pipeline_timings=pipeline_timings
        )

        clause_schemas: List[ClauseAssessmentSchema] = []
        for assess in target_assessments:
            sb = assess.score_breakdown
            breakdown_schema = ComponentBreakdownSchema(
                bert_component=sb.bert_component,
                rule_component=sb.rule_component,
                rag_component=sb.rag_component,
                llm_component=sb.llm_component,
                final_score=sb.final_score
            )

            rule_schemas = [
                RuleMatchSchema(
                    rule_id=r.rule_id,
                    risk_category=r.risk_category.value,
                    description=r.description,
                    severity_weight=r.severity_weight,
                    matched_text=r.matched_text
                ) for r in assess.detected_rules
            ]

            c_intra_schemas = [
                CrossClauseConflictSchema(
                    conflict_id=ic.conflict_id,
                    conflict_type=ic.conflict_type,
                    severity=ic.severity.value if hasattr(ic.severity, "value") else str(ic.severity),
                    clause_ids=ic.clause_ids,
                    clause_numbers=ic.clause_numbers,
                    explanation=ic.explanation,
                    conflicting_excerpt_a=ic.conflicting_excerpt_a,
                    conflicting_excerpt_b=ic.conflicting_excerpt_b
                )
                for ic in getattr(assess, "intra_clause_contradictions", [])
            ]

            llm_st = assess.llm_inference_status.value if hasattr(assess.llm_inference_status, "value") else str(assess.llm_inference_status)

            c_schema = ClauseAssessmentSchema(
                clause_id=assess.clause_id,
                clause_number=assess.clause_number,
                clause_heading=assess.clause_heading,
                clause_text=assess.clause_text,
                risk_score=assess.risk_score,
                risk_level=assess.risk_level.value,
                risk_category=assess.risk_category.value,
                bert_label=assess.clause_type,
                bert_confidence=assess.bert_confidence,
                is_uncertain_classification=getattr(assess, "is_uncertain_classification", False),
                display_category=getattr(assess, "display_category", assess.clause_type),
                rule_matches=rule_schemas,
                intra_clause_contradictions=c_intra_schemas,
                component_score_breakdown=breakdown_schema,
                llm_explanation=assess.risk_explanation,
                llm_inference_status=llm_st,
                key_risk_factors=assess.key_risk_factors,
                uncertainty=assess.uncertainty,
                evidence=[dict(e) for e in assess.evidence if isinstance(e, dict)],
                future_scenario=scenario_map.get(assess.clause_id)
            )
            clause_schemas.append(c_schema)

        return AnalysisResponse(
            document=doc_schema,
            contract_summary=summary_schema,
            clause_assessments=clause_schemas,
            combined_scenario=comb_scen_schema,
            cross_clause_conflicts=conflict_schemas,
            intra_clause_contradictions=intra_conflict_schemas,
            pipeline_timings=pipeline_timings
        )

    finally:
        # Guaranteed temporary file cleanup
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


@router.get(
    "/documents",
    summary="List Processed Contract Documents",
    description="Retrieve paginated list of persisted contract documents from database."
)
def list_documents(limit: int = 50, offset: int = 0):
    """Optional read endpoint listing processed contract documents."""
    try:
        with get_db_session() as session:
            repo = ContractRepository(session)
            docs = repo.list_documents(limit=limit, offset=offset)
            return [
                {
                    "document_id": d.document_id,
                    "filename": d.filename,
                    "document_type": d.document_type,
                    "uploaded_at": d.uploaded_at.isoformat() if d.uploaded_at else None,
                    "clause_count": d.clause_count,
                    "status": d.processing_status
                } for d in docs
            ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database query failed: {e}"
        )


@router.get(
    "/documents/{document_id}",
    summary="Get Document Detail & Analysis Record",
    description="Retrieve full persisted document, clauses, risk assessments, and scenario predictions by document ID."
)
def get_document_detail(document_id: str):
    """Optional read endpoint returning complete document analysis details."""
    try:
        with get_db_session() as session:
            repo = ContractRepository(session)
            doc = repo.get_document(document_id)
            if not doc:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Document with ID '{document_id}' not found in database."
                )
            
            return {
                "document_id": doc.document_id,
                "filename": doc.filename,
                "document_type": doc.document_type,
                "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
                "clause_count": doc.clause_count,
                "status": doc.processing_status,
                "summaries": [
                    {
                        "risk_score": s.risk_score,
                        "risk_level": s.risk_level,
                        "high_risk_count": s.high_risk_count,
                        "medium_risk_count": s.medium_risk_count,
                        "low_risk_count": s.low_risk_count
                    } for s in doc.summaries
                ],
                "clauses": [
                    {
                        "clause_id": c.clause_id,
                        "clause_number": c.clause_number,
                        "clause_title": c.clause_title,
                        "clause_text": c.clause_text,
                        "risk_assessment": {
                            "risk_category": c.risk_assessment.risk_category,
                            "risk_level": c.risk_assessment.risk_level,
                            "final_score": c.risk_assessment.final_score,
                            "risk_explanation": c.risk_assessment.risk_explanation,
                            "rule_matches": [
                                {
                                    "rule_id": rm.rule_id,
                                    "severity": rm.severity,
                                    "matched_text": rm.matched_text
                                } for rm in c.risk_assessment.rule_matches
                            ]
                        } if c.risk_assessment else None
                    } for c in doc.clauses
                ]
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database retrieval failed: {e}"
        )


@router.get(
    "/rules",
    summary="Get Rule Library",
    description="Returns all active Risk Engine rules across all risk domains."
)
def get_rule_library():
    """Return all active Risk Engine rules."""
    from src.risk_analysis.rules import RISK_RULES
    return [
        {
            "rule_id": r["rule_id"],
            "risk_category": r["risk_category"].value if hasattr(r["risk_category"], "value") else str(r["risk_category"]),
            "description": r["description"],
            "severity_weight": r["severity_weight"],
        }
        for r in RISK_RULES
    ]
