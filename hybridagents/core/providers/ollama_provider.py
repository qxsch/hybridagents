"""
Ollama provider – local inference via the Ollama Python SDK.
"""

from __future__ import annotations

import ollama

from hybridagents.config import OLLAMA_BASE_URL, OLLAMA_NUM_CTX
from hybridagents.core.providers.base import LLMProvider


class OllamaProvider(LLMProvider):
    """Talks to a locally-running Ollama server."""

    def __init__(self) -> None:
        self._client: ollama.Client | None = None

    def _get_client(self) -> ollama.Client:
        if self._client is None:
            self._client = ollama.Client(host=OLLAMA_BASE_URL)
        return self._client

    def chat(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float | None = None,
        json_mode: bool = False,
    ) -> str:
        client = self._get_client()
        fmt = "json" if json_mode else ""
        options: dict = {"num_ctx": OLLAMA_NUM_CTX}
        if temperature is not None:
            options["temperature"] = temperature
        resp = client.chat(
            model=model,
            messages=messages,
            options=options,
            format=fmt or None,
        )
        return resp["message"]["content"]
