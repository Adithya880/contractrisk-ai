"""
Unit Test Suite for LLMGenerator Module (Mocked HTTP API Requests)
"""

import json
from unittest.mock import MagicMock, patch
import pytest
import requests

from src.rag.generator import LLMGenerator, LLMGeneratorError, LMStudioConnectionError


@patch("requests.post")
@patch("requests.get")
def test_llm_generator_success_parsing(mock_get, mock_post):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "data": [{"id": "qwen3-4b-instruct-2507"}]
    }

    mock_resp_json = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "answer": "Tenant must maintain insurance.",
                        "citations": [{"clause_id": "doc1:clause:001", "source_pages": [1]}],
                        "insufficient_evidence": False,
                    })
                }
            }
        ]
    }
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = mock_resp_json

    generator = LLMGenerator(base_url="http://127.0.0.1:1234/v1")
    res = generator.generate("What is required?", "[Evidence 1]")

    assert res["answer"] == "Tenant must maintain insurance."
    assert res["insufficient_evidence"] is False
    assert len(res["citations"]) == 1


@patch("requests.post")
@patch("requests.get")
def test_llm_generator_markdown_backtick_json_stripping(mock_get, mock_post):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"data": [{"id": "qwen3"}]}

    raw_markdown = (
        "```json\n"
        "{\n"
        '  "answer": "Grounded answer.",\n'
        '  "citations": [],\n'
        '  "insufficient_evidence": false\n'
        "}\n"
        "```"
    )
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "choices": [{"message": {"content": raw_markdown}}]
    }

    generator = LLMGenerator(base_url="http://127.0.0.1:1234/v1")
    res = generator.generate("Query?", "Context")

    assert res["answer"] == "Grounded answer."


@patch("requests.post")
def test_llm_generator_connection_error(mock_post):
    mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")

    generator = LLMGenerator(base_url="http://127.0.0.1:1234/v1")
    with pytest.raises(LMStudioConnectionError):
        generator.generate("Query?", "Context")


@patch("requests.post")
def test_llm_generator_timeout_error(mock_post):
    mock_post.side_effect = requests.exceptions.Timeout("Request timed out")

    generator = LLMGenerator(base_url="http://127.0.0.1:1234/v1")
    with pytest.raises(LLMGeneratorError):
        generator.generate("Query?", "Context")
