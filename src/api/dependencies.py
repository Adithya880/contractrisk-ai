"""
FastAPI Dependency Providers for ContractRisk AI.
Instantiates and provides pipeline services for API endpoint routes.
Allows dependency overrides during testing.
"""

import logging
from pathlib import Path
from typing import Optional

from src.document_processing.loader import DocumentLoader
from src.clause_segmentation.segmenter import ClauseSegmenter
from src.risk_analysis.analyzer import ContractRiskAnalyzer
from src.risk_analysis.scenario_predictor import FutureScenarioPredictor
from src.models.bert_predictor import get_bert_predictor, BERTClausePredictor
from src.embeddings.embedder import ClauseEmbedder
from src.embeddings.index import FAISSIndexManager
from src.rag.pipeline import RAGPipeline

logger = logging.getLogger(__name__)

_document_loader: Optional[DocumentLoader] = None
_clause_segmenter: Optional[ClauseSegmenter] = None
_risk_analyzer: Optional[ContractRiskAnalyzer] = None
_scenario_predictor: Optional[FutureScenarioPredictor] = None
_bert_predictor: Optional[BERTClausePredictor] = None
_rag_pipeline: Optional[RAGPipeline] = None
_faiss_manager: Optional[FAISSIndexManager] = None
_clause_embedder: Optional[ClauseEmbedder] = None


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


def get_bert_model() -> BERTClausePredictor:
    """Lazy loader for fine-tuned BERT clause classifier singleton."""
    global _bert_predictor
    if _bert_predictor is None:
        try:
            _bert_predictor = get_bert_predictor()
            logger.info("BERTClausePredictor loaded successfully into API dependencies.")
        except Exception as e:
            logger.error(f"Critical error loading fine-tuned BERT clause classifier: {e}")
            raise RuntimeError(f"Fine-tuned BERT checkpoint failed to load: {e}") from e
    return _bert_predictor


def get_rag_pipeline() -> Optional[RAGPipeline]:
    """Lazy loader for FAISS vector index and RAG pipeline singleton."""
    global _rag_pipeline, _faiss_manager, _clause_embedder
    if _rag_pipeline is None:
        try:
            faiss_dir = Path("models/faiss_index")
            if faiss_dir.exists() and (faiss_dir / "contract_clauses.faiss").exists():
                _faiss_manager = FAISSIndexManager()
                _faiss_manager.load(faiss_dir)
                _clause_embedder = ClauseEmbedder(batch_size=64)
                _clause_embedder._load_model()  # Preload embedding model weights during singleton initialization
                _rag_pipeline = RAGPipeline(
                    index_manager=_faiss_manager,
                    embedder=_clause_embedder,
                )
                _rag_pipeline.retriever.default_top_k = 3
                _rag_pipeline.retriever.default_threshold = 0.40
                logger.info(
                    f"RAGPipeline loaded successfully with {_faiss_manager.total_vectors} benchmark vectors."
                )
            else:
                logger.warning(
                    f"FAISS index missing at {faiss_dir}; RAG pipeline running in offline fallback mode."
                )
                _rag_pipeline = None
        except Exception as e:
            logger.warning(f"Failed to load RAGPipeline ({e}); running in fallback mode.")
            _rag_pipeline = None
    return _rag_pipeline


def get_risk_analyzer() -> ContractRiskAnalyzer:
    """Lazy loader for ContractRiskAnalyzer injected with BERT and RAG singletons."""
    global _risk_analyzer
    if _risk_analyzer is None:
        bert_model = get_bert_model()
        rag_pipe = get_rag_pipeline()
        _risk_analyzer = ContractRiskAnalyzer(
            bert_classifier=bert_model,
            rag_pipeline=rag_pipe,
        )
        logger.info(
            f"ContractRiskAnalyzer initialized with BERT={'CONNECTED' if bert_model else 'OFFLINE'} "
            f"and RAG={'CONNECTED' if rag_pipe else 'OFFLINE'}."
        )
    return _risk_analyzer


def get_scenario_predictor() -> FutureScenarioPredictor:
    global _scenario_predictor
    if _scenario_predictor is None:
        _scenario_predictor = FutureScenarioPredictor()
    return _scenario_predictor


def reset_dependencies() -> None:
    """Helper to reset singletons during test isolation if necessary."""
    global _document_loader, _clause_segmenter, _risk_analyzer
    global _scenario_predictor, _bert_predictor, _rag_pipeline
    global _faiss_manager, _clause_embedder
    _document_loader = None
    _clause_segmenter = None
    _risk_analyzer = None
    _scenario_predictor = None
    _bert_predictor = None
    _rag_pipeline = None
    _faiss_manager = None
    _clause_embedder = None
