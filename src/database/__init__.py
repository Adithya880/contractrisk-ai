"""
Database Package for ContractRisk AI.
"""

from src.database.config import settings
from src.database.connection import engine, SessionLocal, get_db, get_db_session
from src.database.models import (
    Base,
    DocumentModel,
    ClauseModel,
    RiskAssessmentModel,
    RuleMatchModel,
    EvidenceCitationModel,
    FutureScenarioModel,
    ContractSummaryModel,
    AnalysisRunModel
)
from src.database.repositories import ContractRepository

__all__ = [
    "settings",
    "engine",
    "SessionLocal",
    "get_db",
    "get_db_session",
    "Base",
    "DocumentModel",
    "ClauseModel",
    "RiskAssessmentModel",
    "RuleMatchModel",
    "EvidenceCitationModel",
    "FutureScenarioModel",
    "ContractSummaryModel",
    "AnalysisRunModel",
    "ContractRepository"
]
