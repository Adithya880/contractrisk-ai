"""
API Client Module for ContractRisk AI Frontend.
Encapsulates RESTful HTTP requests to the FastAPI backend service.
Handles connection timeouts, error responses, and JSON deserialization gracefully.
"""

import requests
from typing import Dict, Any, Optional, List
from frontend.config import API_BASE_URL


class APIClientError(Exception):
    """Custom exception raised when backend API request fails."""
    pass


class ContractRiskAPIClient:
    """HTTP Client connecting Streamlit frontend to FastAPI backend endpoints."""

    def __init__(self, base_url: str = API_BASE_URL, timeout: int = 600):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def check_health(self) -> Dict[str, Any]:
        """Query GET /api/v1/health endpoint."""
        url = f"{self.base_url}/health"
        try:
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                return res.json()
            return {"status": "unhealthy", "detail": f"HTTP {res.status_code}"}
        except Exception as e:
            return {"status": "offline", "detail": str(e)}

    def get_model_info(self) -> Dict[str, Any]:
        """Query GET /api/v1/models endpoint."""
        url = f"{self.base_url}/models"
        try:
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                return res.json()
            raise APIClientError(f"Failed to fetch model info (HTTP {res.status_code})")
        except Exception as e:
            raise APIClientError(f"Model status query failed: {e}")

    def analyze_contract(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Post contract PDF/DOCX bytes to POST /api/v1/analyze endpoint."""
        url = f"{self.base_url}/analyze"
        files = {"file": (filename, file_bytes, "application/octet-stream")}
        try:
            res = requests.post(url, files=files, timeout=self.timeout)
            if res.status_code == 200:
                return res.json()
            else:
                err_detail = "Analysis request failed."
                try:
                    err_json = res.json()
                    err_detail = err_json.get("detail", res.text)
                except Exception:
                    err_detail = res.text
                raise APIClientError(f"API Error (HTTP {res.status_code}): {err_detail}")
        except requests.exceptions.Timeout:
            raise APIClientError(f"API Request Timed Out: Pipeline analysis took longer than {self.timeout}s.")
        except requests.exceptions.ConnectionError:
            raise APIClientError(f"API Connection Failed: Cannot reach FastAPI server at {self.base_url}.")
        except Exception as e:
            if isinstance(e, APIClientError):
                raise
            raise APIClientError(f"Unexpected error during analysis API call: {e}")

    def get_documents_history(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Query GET /api/v1/documents endpoint."""
        url = f"{self.base_url}/documents?limit={limit}&offset={offset}"
        try:
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                return res.json()
            return []
        except Exception:
            return []

    def get_document_detail(self, document_id: str) -> Dict[str, Any]:
        """Query GET /api/v1/documents/{document_id} endpoint."""
        url = f"{self.base_url}/documents/{document_id}"
        try:
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                return res.json()
            raise APIClientError(f"Document ID '{document_id}' not found (HTTP {res.status_code})")
        except Exception as e:
            if isinstance(e, APIClientError):
                raise
            raise APIClientError(f"Failed to retrieve document details: {e}")


api_client = ContractRiskAPIClient()
