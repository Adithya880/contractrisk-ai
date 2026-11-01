"""
Models info route module for GET /api/v1/models.
"""

from fastapi import APIRouter
from src.api.schemas import ModelInfoResponse, ComponentMetadataSchema
from src.rag.generator import LLMGenerator

router = APIRouter()


@router.get(
    "/models",
    response_model=ModelInfoResponse,
    summary="Pipeline Models & Components Metadata",
    description="Returns configuration and load status of active ContractRisk AI pipeline models without exposing sensitive paths or credentials."
)
async def get_models_info() -> ModelInfoResponse:
    """Return configured model metadata with live availability probe for Qwen3 / LM Studio."""
    llm = LLMGenerator()
    llm_online = llm.is_available(timeout=0.5)

    return ModelInfoResponse(
        bert_classifier=ComponentMetadataSchema(
            name="bert-base-uncased",
            status="active",
            details={
                "num_classes": 41,
                "fine_tuned_checkpoint": "models/bert_clause_classifier/best",
                "task": "Multi-class legal clause assignment"
            }
        ),
        embedding_model=ComponentMetadataSchema(
            name="all-MiniLM-L6-v2",
            status="active",
            details={
                "embedding_dimension": 384,
                "normalization": "L2 unit vector",
                "framework": "SentenceTransformers"
            }
        ),
        vector_store=ComponentMetadataSchema(
            name="FAISS Index",
            status="active",
            details={
                "metric": "Cosine Similarity / Inner Product",
                "index_type": "IndexFlatIP"
            }
        ),
        local_llm=ComponentMetadataSchema(
            name="qwen3-4b-instruct-2507",
            status="active" if llm_online else "unavailable",
            details={
                "provider": "LM Studio (Local Server)",
                "base_url": llm.base_url,
                "model_id": llm.get_active_model_id() if llm_online else "qwen3-4b-instruct-2507",
                "temperature": 0.2,
                "server_status": "online" if llm_online else "offline"
            }
        ),
        scenario_predictor=ComponentMetadataSchema(
            name="FutureScenarioPredictor",
            status="active" if llm_online else "offline",
            details={
                "grounding_pass": "Phase 7.2.1 Anti-Hallucination",
                "llm_backend": "online" if llm_online else "offline"
            }
        )
    )
