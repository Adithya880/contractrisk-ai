"""
Local LLM Generator Module for ContractRisk AI RAG Pipeline

Queries local Qwen3 model running on LM Studio via OpenAI-compatible HTTP API (/v1/chat/completions)
with strict parameters (temperature=0.2, top_p=0.9, max_tokens=1500) and structured JSON parsing.
"""

import json
import os
import re
from typing import Any, Dict, Optional
import requests

from src.rag.prompts import RAG_SYSTEM_PROMPT, build_user_prompt


class LLMGeneratorError(Exception):
    """Base exception for LLM generation failures."""
    pass


class LMStudioConnectionError(LLMGeneratorError):
    """Raised when LM Studio server is unreachable or offline."""
    pass


class LLMGenerator:
    """
    Generator abstraction connecting to local LM Studio server for grounded Qwen3 inference.
    """

    DEFAULT_BASE_URL: str = "http://127.0.0.1:1234/v1"
    DEFAULT_MODEL_ID: str = "qwen3-4b-instruct-2507"
    _cached_active_model_id: Optional[str] = None

    def __init__(
        self,
        base_url: Optional[str] = None,
        model_id: Optional[str] = None,
        temperature: float = 0.2,
        top_p: float = 0.9,
        max_tokens: int = 1000,
        timeout: int = 60,
    ):
        self.base_url = (base_url or os.getenv("LM_STUDIO_BASE_URL") or self.DEFAULT_BASE_URL).rstrip("/")
        self._configured_model = model_id or os.getenv("LM_STUDIO_MODEL")
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens
        self.timeout = timeout

    def get_active_model_id(self) -> str:
        """
        Queries LM Studio /v1/models endpoint to discover the active model ID.
        Caches the discovered model ID to avoid repeated GET /v1/models calls.
        Falls back to configured model ID or default.
        """
        if self._configured_model:
            return self._configured_model
        if LLMGenerator._cached_active_model_id:
            return LLMGenerator._cached_active_model_id

        try:
            resp = requests.get(f"{self.base_url}/models", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                models = data.get("data", [])
                if models and "id" in models[0]:
                    # Find Qwen model or first model in active list
                    for m in models:
                        m_id = m.get("id", "")
                        if "qwen" in m_id.lower() or "instruct" in m_id.lower():
                            LLMGenerator._cached_active_model_id = m_id
                            self._configured_model = m_id
                            return m_id
                    active_id = models[0]["id"]
                    LLMGenerator._cached_active_model_id = active_id
                    self._configured_model = active_id
                    return active_id
        except Exception:
            pass

        return self.DEFAULT_MODEL_ID

    def generate(self, query: str, context: str) -> Dict[str, Any]:
        """
        Sends grounded RAG prompt to LM Studio and parses structured JSON output.

        Args:
            query: User question.
            context: Formatted evidence string from ContextBuilder.

        Returns:
            Dict containing 'answer', 'citations', and 'insufficient_evidence'.

        Raises:
            LMStudioConnectionError: If server cannot be reached.
            LLMGeneratorError: If request times out or response is unparseable.
        """
        user_prompt = build_user_prompt(query, context)
        model_id = self.get_active_model_id()

        payload = {
            "model": model_id,
            "messages": [
                {"role": "system", "content": RAG_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
            "stream": False,
        }

        try:
            resp = requests.post(
                f"{self.base_url}/chat/completions",
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=self.timeout,
            )
        except requests.exceptions.ConnectionError as e:
            raise LMStudioConnectionError(
                f"Failed to connect to LM Studio at '{self.base_url}'. Ensure LM Studio local server is running."
            ) from e
        except requests.exceptions.Timeout as e:
            raise LLMGeneratorError(f"LM Studio generation request timed out after {self.timeout}s.") from e
        except Exception as e:
            raise LLMGeneratorError(f"HTTP request error during generation: {e}") from e

        if resp.status_code != 200:
            raise LLMGeneratorError(f"LM Studio API returned HTTP {resp.status_code}: {resp.text}")

        try:
            resp_data = resp.json()
            raw_content = resp_data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            raise LLMGeneratorError(f"Failed to parse OpenAI response payload from LM Studio: {e}")

        # Strip markdown JSON backtick wrappers if present
        clean_content = re.sub(r"^```(?:json)?\s*", "", raw_content, flags=re.MULTILINE)
        clean_content = re.sub(r"\s*```$", "", clean_content, flags=re.MULTILINE).strip()

        try:
            parsed_json = json.loads(clean_content)
        except json.JSONDecodeError:
            # Fallback parsing if JSON contains trailing text
            json_match = re.search(r"\{.*\}", clean_content, re.DOTALL)
            if json_match:
                try:
                    parsed_json = json.loads(json_match.group(0))
                except json.JSONDecodeError as e:
                    raise LLMGeneratorError(f"Qwen response could not be parsed as JSON: {e}\nRaw output: {raw_content}")
            else:
                raise LLMGeneratorError(f"Qwen response did not contain JSON: {raw_content}")

        return parsed_json
