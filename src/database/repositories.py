"""
Repository Layer for Database Persistence in ContractRisk AI.
Encapsulates CRUD operations for documents, clauses, risk assessments, rule matches, scenarios, and summaries.
Does NOT perform any risk calculation; strictly persists pre-computed pipeline outputs inside a transaction.
"""

import uuid
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select

from src.database.models import (
    DocumentModel,
    ClauseModel,
    RiskAssessmentModel,
    RuleMatchModel,
    EvidenceCitationModel,
    FutureScenarioModel,
    ContractSummaryModel,
    AnalysisRunModel
)
from src.risk_analysis.models import ContractRiskSummary, RiskAssessment
from src.risk_analysis.scenario_predictor import FutureScenario


class ContractRepository:
    """Repository handling atomic persistence and retrieval of analyzed contract documents."""

    def __init__(self, session: Session):
        self.session = session

    def get_document(self, document_id: str) -> Optional[DocumentModel]:
        """Fetch a document model by unique document_id with relationships populated."""
        stmt = (
            select(DocumentModel)
            .where(DocumentModel.document_id == document_id)
            .options(
                joinedload(DocumentModel.clauses)
                .joinedload(ClauseModel.risk_assessment)
                .joinedload(RiskAssessmentModel.rule_matches),
                joinedload(DocumentModel.clauses)
                .joinedload(ClauseModel.risk_assessment)
                .joinedload(RiskAssessmentModel.future_scenario),
                joinedload(DocumentModel.summaries)
            )
        )
        return self.session.scalars(stmt).unique().first()

    def list_documents(self, limit: int = 50, offset: int = 0) -> List[DocumentModel]:
        """Fetch paginated list of processed document records."""
        stmt = (
            select(DocumentModel)
            .order_by(DocumentModel.uploaded_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(stmt).all())

    def save_analysis(
        self,
        summary: ContractRiskSummary,
        all_assessments: List[RiskAssessment],
        scenario_map: Dict[str, Any],
        filename: str,
        document_type: str = "PDF"
    ) -> DocumentModel:
        """
        Atomically persist all pipeline outputs for a contract analysis run inside a transaction:
        1. Document metadata
        2. Clauses
        3. Risk assessments & Component score breakdowns
        4. Rule matches
        5. Evidence citations
        6. Future scenarios
        7. Contract summary
        8. Analysis run tracking
        """
        # 1. Upsert / Create Document Record
        doc = self.get_document(summary.document_id)
        if doc is None:
            doc = DocumentModel(
                document_id=summary.document_id,
                filename=filename,
                document_type=document_type,
                page_count=1,
                clause_count=summary.analyzed_clauses_count,
                processing_status="COMPLETED",
                metadata_json={"source_filename": summary.source_filename}
            )
            self.session.add(doc)
            self.session.flush()  # Ensure document_id is committed in transaction
        else:
            doc.filename = filename
            doc.clause_count = summary.analyzed_clauses_count
            doc.processing_status = "COMPLETED"

        # 2. Persist Clauses & Risk Assessments
        for seq, assess in enumerate(all_assessments, 1):
            # Check existing clause or instantiate
            stmt = select(ClauseModel).where(
                ClauseModel.document_id == summary.document_id,
                ClauseModel.clause_id == assess.clause_id
            )
            clause_record = self.session.scalars(stmt).first()

            if clause_record is None:
                clause_record = ClauseModel(
                    document_id=summary.document_id,
                    clause_id=assess.clause_id,
                    clause_number=assess.clause_number,
                    clause_title=assess.clause_heading,
                    clause_text=assess.clause_text,
                    source_pages=assess.source_pages or [1],
                    sequence_number=seq
                )
                self.session.add(clause_record)
                self.session.flush()
            else:
                clause_record.clause_number = assess.clause_number
                clause_record.clause_title = assess.clause_heading
                clause_record.clause_text = assess.clause_text

            # Create or update RiskAssessment record
            sb = assess.score_breakdown
            if clause_record.risk_assessment:
                self.session.delete(clause_record.risk_assessment)
                self.session.flush()

            ra_record = RiskAssessmentModel(
                clause_db_id=clause_record.id,
                risk_category=assess.risk_category.value,
                risk_level=assess.risk_level.value,
                final_score=assess.risk_score,
                bert_score=sb.bert_component,
                rule_score=sb.rule_component,
                rag_score=sb.rag_component,
                llm_score=sb.llm_component,
                bert_clause_type=assess.clause_type,
                bert_confidence=assess.bert_confidence,
                risk_explanation=assess.risk_explanation,
                uncertainty=assess.uncertainty,
                key_risk_factors=assess.key_risk_factors
            )
            self.session.add(ra_record)
            self.session.flush()

            # Rule matches
            for rule in assess.detected_rules:
                rm = RuleMatchModel(
                    risk_assessment_id=ra_record.id,
                    rule_id=rule.rule_id,
                    rule_name=rule.description,
                    category=rule.risk_category.value,
                    severity=rule.severity_weight,
                    matched_text=rule.matched_text
                )
                self.session.add(rm)

            # Evidence citations
            for ev in assess.evidence:
                source_cid = ev.get("clause_id") or ev.get("source_clause_id")
                source_txt = ev.get("text") or ev.get("clause_text") or str(ev)
                sim_score = ev.get("similarity_score") or ev.get("score")
                citation = EvidenceCitationModel(
                    risk_assessment_id=ra_record.id,
                    source_clause_id=source_cid,
                    source_text=source_txt,
                    similarity_score=float(sim_score) if sim_score is not None else None,
                    citation_metadata=ev if isinstance(ev, dict) else {}
                )
                self.session.add(citation)

            # Future Scenario
            scen_obj = scenario_map.get(assess.clause_id)
            if scen_obj:
                scen_dict = scen_obj.model_dump() if hasattr(scen_obj, "model_dump") else (
                    scen_obj.dict() if hasattr(scen_obj, "dict") else scen_obj
                )
                fs_record = FutureScenarioModel(
                    risk_assessment_id=ra_record.id,
                    scenario_id=scen_dict.get("scenario_id") or f"scen_{uuid.uuid4().hex[:8]}",
                    clause_id=assess.clause_id,
                    scenario_title=scen_dict.get("scenario_title", "Risk Scenario"),
                    trigger_condition=scen_dict.get("trigger_condition", ""),
                    scenario_description=scen_dict.get("scenario_description", ""),
                    possible_consequence=scen_dict.get("possible_consequence", ""),
                    assumptions=scen_dict.get("assumptions", []),
                    uncertainty=scen_dict.get("uncertainty", ""),
                    fallback_active=scen_dict.get("fallback_active", False),
                    disclaimer=scen_dict.get("disclaimer", "")
                )
                self.session.add(fs_record)

        # 3. Contract Summary Record
        summary_record = ContractSummaryModel(
            document_id=summary.document_id,
            risk_score=summary.contract_risk_score,
            risk_level=summary.contract_risk_level.value,
            high_risk_count=summary.high_risk_clauses_count,
            medium_risk_count=summary.medium_risk_clauses_count,
            low_risk_count=summary.low_risk_clauses_count,
            clause_count=summary.analyzed_clauses_count
        )
        self.session.add(summary_record)

        # 4. Analysis Run Record
        run_record = AnalysisRunModel(
            run_id=f"run_{uuid.uuid4().hex[:12]}",
            document_id=summary.document_id,
            pipeline_version="1.0.0",
            model_info={"engine": "ContractRisk AI Hybrid Pipeline"},
            status="COMPLETED"
        )
        self.session.add(run_record)

        self.session.flush()
        return doc
