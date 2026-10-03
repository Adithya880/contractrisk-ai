"""
FastAPI API Unit Tests for ContractRisk AI.
Tests GET /api/v1/health, GET /api/v1/models, and POST /api/v1/analyze file upload routes using TestClient.
"""

import io
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.dependencies import (
    get_document_loader,
    get_clause_segmenter,
    get_risk_analyzer,
    get_scenario_predictor
)
from src.document_processing.models import ExtractedDocument, SourceType, DocumentMetadata
from src.clause_segmentation.models import SegmentedClause, SegmentationResult
from src.risk_analysis.models import (
    RiskAssessment,
    RiskLevel,
    RiskCategory,
    RiskScoreBreakdown,
    ContractRiskSummary
)
from src.risk_analysis.scenario_models import FutureScenario


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_dependencies():
    # Synthetic Extracted Document
    mock_metadata = DocumentMetadata(
        filename="test_contract.pdf",
        file_path="/tmp/test_contract.pdf",
        file_type=SourceType.PDF,
        file_size_bytes=150,
        page_count=2
    )
    mock_extracted_doc = ExtractedDocument(
        document_id="doc_api_001",
        source_filename="test_contract.pdf",
        source_path="/tmp/test_contract.pdf",
        source_type=SourceType.PDF,
        metadata=mock_metadata,
        elements=[],
        full_cleaned_text="Vendor shall have unlimited liability for gross negligence."
    )

    # Synthetic Clause & Segmentation Result
    c1_text = "Vendor shall have unlimited liability for gross negligence."
    mock_clause = SegmentedClause(
        clause_id="c_001",
        document_id="doc_api_001",
        clause_number="12.1",
        clause_heading="Liability",
        clause_text=c1_text,
        source_type=SourceType.PDF,
        source_pages=[1],
        character_count=len(c1_text),
        word_count=len(c1_text.split())
    )

    mock_seg_result = SegmentationResult(
        document_id="doc_api_001",
        source_filename="test_contract.pdf",
        clauses=[mock_clause],
        total_clauses=1,
        source_character_count=150,
        segmented_character_count=len(c1_text),
        text_coverage_ratio=1.0
    )

    # Synthetic Risk Assessment & Contract Summary
    mock_assessment = RiskAssessment(
        assessment_id="assess_api_01",
        document_id="doc_api_001",
        clause_id="c_001",
        clause_number="12.1",
        clause_heading="Liability",
        clause_text=c1_text,
        clause_type="Uncapped Liability",
        bert_confidence=0.95,
        risk_category=RiskCategory.LIABILITY,
        risk_score=78.74,
        risk_level=RiskLevel.HIGH,
        score_breakdown=RiskScoreBreakdown(
            bert_component=90.0,
            rule_component=95.0,
            rag_component=0.0,
            llm_component=85.0,
            final_score=78.74
        ),
        detected_rules=[],
        risk_explanation="Uncapped liability exposure.",
        evidence_summary="No evidence.",
        key_risk_factors=["Uncapped financial exposure"],
        evidence=[],
        source_pages=[1],
        uncertainty="Low uncertainty."
    )

    mock_summary = ContractRiskSummary(
        document_id="doc_api_001",
        source_filename="test_contract.pdf",
        contract_risk_score=78.74,
        contract_risk_level=RiskLevel.HIGH,
        analyzed_clauses_count=1,
        high_risk_clauses_count=1,
        medium_risk_clauses_count=0,
        low_risk_clauses_count=0,
        highest_risk_assessments=[mock_assessment]
    )

    # Synthetic Future Scenario
    mock_scenario = FutureScenario(
        scenario_id="scen_api_01",
        clause_id="c_001",
        clause_number="12.1",
        scenario_title="Potential Financial Exposure Scenario",
        trigger_condition="If a breach claim occurs.",
        scenario_description="Customer could face unmitigated financial liability.",
        possible_consequence="Severe financial loss.",
        supporting_evidence=[],
        assumptions=["Contract enforced as written"],
        uncertainty="Low uncertainty.",
        fallback_active=False
    )

    # Mock Loader, Segmenter, Analyzer, Predictor Services
    loader = MagicMock()
    loader.load_document.return_value = mock_extracted_doc

    segmenter = MagicMock()
    segmenter.segment.return_value = mock_seg_result

    analyzer = MagicMock()
    analyzer.analyze_document.return_value = mock_summary

    predictor = MagicMock()
    predictor.predict_scenario.return_value = mock_scenario

    return {
        "loader": loader,
        "segmenter": segmenter,
        "analyzer": analyzer,
        "predictor": predictor
    }


def test_health_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "ContractRisk AI"
    assert data["version"] == "1.0.0"


def test_models_endpoint(client):
    response = client.get("/api/v1/models")
    assert response.status_code == 200
    data = response.json()
    assert "bert_classifier" in data
    assert "embedding_model" in data
    assert "vector_store" in data
    assert "local_llm" in data
    assert "scenario_predictor" in data
    assert data["bert_classifier"]["name"] == "bert-base-uncased"
    assert data["local_llm"]["details"]["provider"] == "LM Studio (Local Server)"


def test_analyze_pdf_success(client, mock_dependencies):
    app.dependency_overrides[get_document_loader] = lambda: mock_dependencies["loader"]
    app.dependency_overrides[get_clause_segmenter] = lambda: mock_dependencies["segmenter"]
    app.dependency_overrides[get_risk_analyzer] = lambda: mock_dependencies["analyzer"]
    app.dependency_overrides[get_scenario_predictor] = lambda: mock_dependencies["predictor"]

    pdf_bytes = b"%PDF-1.4 sample pdf content for testing..."
    files = {"file": ("test_contract.pdf", io.BytesIO(pdf_bytes), "application/pdf")}

    response = client.post("/api/v1/analyze", files=files)
    assert response.status_code == 200
    data = response.json()

    assert data["document"]["filename"] == "test_contract.pdf"
    assert data["document"]["document_type"] == "PDF"
    assert data["contract_summary"]["risk_score"] == 78.74
    assert data["contract_summary"]["risk_level"] == "HIGH"
    assert len(data["clause_assessments"]) == 1

    c_assess = data["clause_assessments"][0]
    assert c_assess["clause_id"] == "c_001"
    assert c_assess["risk_score"] == 78.74
    assert c_assess["future_scenario"]["scenario_title"] == "Potential Financial Exposure Scenario"

    app.dependency_overrides.clear()


def test_analyze_docx_success(client, mock_dependencies):
    app.dependency_overrides[get_document_loader] = lambda: mock_dependencies["loader"]
    app.dependency_overrides[get_clause_segmenter] = lambda: mock_dependencies["segmenter"]
    app.dependency_overrides[get_risk_analyzer] = lambda: mock_dependencies["analyzer"]
    app.dependency_overrides[get_scenario_predictor] = lambda: mock_dependencies["predictor"]

    docx_bytes = b"PK\x03\x04 sample docx content..."
    files = {"file": ("agreement.docx", io.BytesIO(docx_bytes), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}

    response = client.post("/api/v1/analyze", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["document"]["document_type"] == "DOCX"

    app.dependency_overrides.clear()


def test_analyze_unsupported_file_type(client):
    file_bytes = b"hello world plain text"
    files = {"file": ("notes.txt", io.BytesIO(file_bytes), "text/plain")}

    response = client.post("/api/v1/analyze", files=files)
    assert response.status_code in [400, 415]
    assert "Unsupported file format" in response.json()["detail"]


def test_analyze_empty_file(client):
    files = {"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")}

    response = client.post("/api/v1/analyze", files=files)
    assert response.status_code == 400
    assert "Uploaded file is empty" in response.json()["detail"]


def test_analyze_scenario_fallback_handling(client, mock_dependencies):
    # Predictor returning fallback scenario
    fallback_scen = FutureScenario(
        scenario_id="scen_fallback_01",
        clause_id="c_001",
        scenario_title="Fallback Liability Scenario",
        trigger_condition="If a breach occurs",
        scenario_description="Fallback narrative",
        possible_consequence="Impact",
        supporting_evidence=[],
        assumptions=[],
        uncertainty="Fallback mode active due to offline LLM",
        fallback_active=True
    )
    mock_dependencies["predictor"].predict_scenario.return_value = fallback_scen

    app.dependency_overrides[get_document_loader] = lambda: mock_dependencies["loader"]
    app.dependency_overrides[get_clause_segmenter] = lambda: mock_dependencies["segmenter"]
    app.dependency_overrides[get_risk_analyzer] = lambda: mock_dependencies["analyzer"]
    app.dependency_overrides[get_scenario_predictor] = lambda: mock_dependencies["predictor"]

    pdf_bytes = b"%PDF-1.4 sample..."
    files = {"file": ("contract.pdf", io.BytesIO(pdf_bytes), "application/pdf")}

    response = client.post("/api/v1/analyze", files=files)
    assert response.status_code == 200
    data = response.json()
    scen_data = data["clause_assessments"][0]["future_scenario"]
    assert scen_data["fallback_active"] is True
    assert "Fallback" in scen_data["scenario_title"]

    app.dependency_overrides.clear()


def test_analyze_lm_studio_unavailable_handling(client, mock_dependencies):
    # Analyzer handling LM Studio connection error smoothly
    app.dependency_overrides[get_document_loader] = lambda: mock_dependencies["loader"]
    app.dependency_overrides[get_clause_segmenter] = lambda: mock_dependencies["segmenter"]
    app.dependency_overrides[get_risk_analyzer] = lambda: mock_dependencies["analyzer"]
    app.dependency_overrides[get_scenario_predictor] = lambda: mock_dependencies["predictor"]

    pdf_bytes = b"%PDF-1.4 sample..."
    files = {"file": ("contract.pdf", io.BytesIO(pdf_bytes), "application/pdf")}

    response = client.post("/api/v1/analyze", files=files)
    assert response.status_code == 200

    app.dependency_overrides.clear()
