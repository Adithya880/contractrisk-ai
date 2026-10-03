"""
FastAPI Dependency Providers for ContractRisk AI.
Instantiates and provides pipeline services for API endpoint routes.
Allows dependency overrides during testing.
"""

from typing import Optional
from src.document_processing.loader import DocumentLoader
from src.clause_segmentation.segmenter import ClauseSegmenter
from src.risk_analysis.analyzer import ContractRiskAnalyzer
from src.risk_analysis.scenario_predictor import FutureScenarioPredictor


_document_loader: Optional[DocumentLoader] = None
_clause_segmenter: Optional[ClauseSegmenter] = None
_risk_analyzer: Optional[ContractRiskAnalyzer] = None
_scenario_predictor: Optional[FutureScenarioPredictor] = None


def get_document_loader() -> DocumentLoader:
    global _document_loader
    if _document_loader is None:
        _document_loader = DocumentLoader()
    return _document_loader


def get_clause_segmenter() -> ClauseSegmenter:
    global _clause_segmenter
    if _clause_segmenter is None:
        _clause_segmenter = ClauseSegmenter()
    return _clause_segmenter


def get_risk_analyzer() -> ContractRiskAnalyzer:
    global _risk_analyzer
    if _risk_analyzer is None:
        _risk_analyzer = ContractRiskAnalyzer()
    return _risk_analyzer


def get_scenario_predictor() -> FutureScenarioPredictor:
    global _scenario_predictor
    if _scenario_predictor is None:
        _scenario_predictor = FutureScenarioPredictor()
    return _scenario_predictor
