"""
Azure AI Foundry provider – uses the OpenAI-compatible inference endpoint.

Works with any model deployed in Foundry (GPT-4o, Claude, Mistral, Llama, …).
"""

from __future__ import annotations

import json

from openai import OpenAI

from agents.config import AZURE_FOUNDRY_ENDPOINT, AZURE_FOUNDRY_API_KEY
from agents.core.providers.base import LLMProvider


class AIFoundryProvider(LLMProvider):
    """Talks to Azure AI Foundry via its OpenAI-compatible endpoint."""

    def __init__(self) -> None:
        self._client: OpenAI | None = None

    def _get_client(self) -> OpenAI:
        if self._client is None:
            if not AZURE_FOUNDRY_ENDPOINT:
                raise RuntimeError(
                    "AZURE_FOUNDRY_ENDPOINT is not set. "
                    "Add it to your .env file (see .env.example)."
                )
            if not AZURE_FOUNDRY_API_KEY:
                raise RuntimeError(
                    "AZURE_FOUNDRY_API_KEY is not set. "
                    "Add it to your .env file (see .env.example)."
                )
            self._client = OpenAI(
                base_url=AZURE_FOUNDRY_ENDPOINT,
                api_key=AZURE_FOUNDRY_API_KEY,
            )
        return self._client

    def chat(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float | None = None,
        json_mode: bool = False,
    ) -> str:
        client = self._get_client()

        kwargs: dict = dict(
            model=model,
            messages=messages,
        )
        if temperature is not None:
            kwargs["temperature"] = temperature
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        resp = client.chat.completions.create(**kwargs)
        return resp.choices[0].message.content or ""
