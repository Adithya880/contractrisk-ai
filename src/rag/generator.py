"""
Local LLM Generator Module for ContractRisk AI RAG Pipeline

Queries local Qwen3 model running on LM Studio via OpenAI-compatible HTTP API (/v1/chat/completions)
with strict parameters (temperature=0.2, top_p=0.9, max_tokens=1500) and structured JSON parsing.
"""

import json
import logging
import os
import re
import time
from typing import Any, Dict, Optional
import requests

from src.rag.prompts import RAG_SYSTEM_PROMPT, build_user_prompt

logger = logging.getLogger(__name__)


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
    _availability_cache: Optional[Dict[str, Any]] = None

    def __init__(
        self,
        base_url: Optional[str] = None,
        model_id: Optional[str] = None,
        temperature: float = 0.2,
        top_p: float = 0.9,
        max_tokens: int = 1200,
        timeout: int = 30,
    ):
        self.base_url = (base_url or os.getenv("LM_STUDIO_BASE_URL") or self.DEFAULT_BASE_URL).rstrip("/")
        self._configured_model = model_id or os.getenv("LM_STUDIO_MODEL")
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens
        self.timeout = timeout

    @classmethod
    def reset_cache(cls) -> None:
        """Reset cached model discovery for test isolation."""
        cls._cached_active_model_id = None
        cls._availability_cache = None

    def is_available(self, timeout: float = 0.8) -> bool:
        """
        Verify whether the LM Studio server is reachable and active.
        Directly queries the live API endpoint so the status is never stale.
        """
        try:
            resp = requests.get(f"{self.base_url}/models", timeout=timeout)
            return resp.status_code == 200
        except Exception as e:
            logger.debug(f"LM Studio availability check failed: {e}")
            return False

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
            resp = requests.get(f"{self.base_url}/models", timeout=2)
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

    def generate(
        self,
        query: str,
        context: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Sends prompt to LM Studio and parses structured JSON output.

        Args:
            query: User question or task title.
            context: Formatted evidence string or context prompt.
            system_prompt: Optional system prompt instructions. Defaults to RAG_SYSTEM_PROMPT.
            max_tokens: Maximum tokens for response. Defaults to self.max_tokens.
            timeout: Request timeout in seconds. Defaults to self.timeout.

        Returns:
            Dict containing parsed JSON fields.

        Raises:
            LMStudioConnectionError: If server cannot be reached.
            LLMGeneratorError: If request times out or response is unparseable.
        """
        if not self.is_available(timeout=1.0):
            raise LMStudioConnectionError(
                f"LM Studio server is offline or unreachable at '{self.base_url}'."
            )

        effective_system_prompt = system_prompt if system_prompt is not None else RAG_SYSTEM_PROMPT
        if system_prompt is not None:
            # When explicit system instructions are passed, user content is the context/evidence
            user_prompt = f"{context}\n\nTask: {query}" if query else context
        else:
            user_prompt = build_user_prompt(query, context)

        model_id = self.get_active_model_id()
        req_max_tokens = max_tokens or self.max_tokens
        req_timeout = timeout or self.timeout

        payload = {
            "model": model_id,
            "messages": [
                {"role": "system", "content": effective_system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": req_max_tokens,
            "stream": False,
        }

        t_start = time.perf_counter()
        logger.info(f"[QWEN3 REQUEST] model={model_id} prompt_len={len(user_prompt)} max_tokens={req_max_tokens}")

        try:
            resp = requests.post(
                f"{self.base_url}/chat/completions",
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=req_timeout,
            )
        except requests.exceptions.ConnectionError as e:
            duration = time.perf_counter() - t_start
            logger.warning(f"[QWEN3 FAILURE] Connection error after {duration:.3f}s: {e}")
            raise LMStudioConnectionError(
                f"Failed to connect to LM Studio at '{self.base_url}'. Ensure LM Studio local server is running."
            ) from e
        except requests.exceptions.Timeout as e:
            duration = time.perf_counter() - t_start
            logger.warning(f"[QWEN3 FAILURE] Timeout after {duration:.3f}s: {e}")
            raise LLMGeneratorError(f"LM Studio generation request timed out after {req_timeout}s.") from e
        except Exception as e:
            duration = time.perf_counter() - t_start
            logger.warning(f"[QWEN3 FAILURE] HTTP error after {duration:.3f}s: {e}")
            raise LLMGeneratorError(f"HTTP request error during generation: {e}") from e

        duration = time.perf_counter() - t_start

        if resp.status_code != 200:
            logger.warning(f"[QWEN3 FAILURE] HTTP {resp.status_code} in {duration:.3f}s: {resp.text}")
            raise LLMGeneratorError(f"LM Studio API returned HTTP {resp.status_code}: {resp.text}")

        try:
            resp_data = resp.json()
            raw_content = resp_data["choices"][0]["message"]["content"].strip()
            logger.info(f"[QWEN3 RESPONSE] HTTP 200 in {duration:.3f}s, response_len={len(raw_content)}")
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            logger.warning(f"[QWEN3 FAILURE] Parse error in {duration:.3f}s: {e}")
            raise LLMGeneratorError(f"Failed to parse OpenAI response payload from LM Studio: {e}")

        # Strip reasoning tags emitted by reasoning / thinking models (Qwen 2.5/3, DeepSeek-R1)
        raw_content = re.sub(r"(?s)<thought>.*?</thought>", "", raw_content).strip()
        raw_content = re.sub(r"(?s)^<thought>.*", "", raw_content).strip()

        # Strip markdown JSON backtick wrappers if present
        clean_content = re.sub(r"^```(?:json)?\s*", "", raw_content, flags=re.MULTILINE)
        clean_content = re.sub(r"\s*```$", "", clean_content, flags=re.MULTILINE).strip()

        try:
            parsed_json = json.loads(clean_content)
        except json.JSONDecodeError:
            # Fallback parsing if JSON contains surrounding explanatory text
            json_match = re.search(r"\{.*\}", clean_content, re.DOTALL)
            if json_match:
                try:
                    parsed_json = json.loads(json_match.group(0))
                except json.JSONDecodeError as e:
                    raise LLMGeneratorError(f"Qwen response could not be parsed as JSON: {e}\nRaw output: {raw_content}")
            else:
                raise LLMGeneratorError(f"Qwen response did not contain JSON: {raw_content}")

        return parsed_json
