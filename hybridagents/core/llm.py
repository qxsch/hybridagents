"""
LLM router – dispatches to the correct provider (Ollama or Azure AI Foundry).
"""

from __future__ import annotations

import json
import re
from typing import Any

from hybridagents.config import (
    DEFAULT_PROVIDER,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
)
from hybridagents.core.providers.base import LLMProvider
from hybridagents.core.providers.ollama_provider import OllamaProvider
from hybridagents.core.providers.aifoundry_provider import AIFoundryProvider
from hybridagents.core.providers.ghcopilot_provider import GHCopilotProvider

# Privacy auto-filter (lazy import to avoid circular deps)
_privacy_pipeline: Any = None  # None = not yet loaded, False = disabled, else PrivacyPipeline
_privacy_vault = None


def _get_privacy_pipeline() -> Any:
    """Lazily build the privacy pipeline from env config (only if enabled)."""
    global _privacy_pipeline
    if _privacy_pipeline is None:
        from hybridagents.privacy.config import PrivacyConfig
        from hybridagents.privacy.pipeline import PrivacyPipeline
        cfg = PrivacyConfig.from_env()
        if cfg.auto_filter_enabled:
            _privacy_pipeline = PrivacyPipeline.from_config(cfg)
        else:
            _privacy_pipeline = False  # sentinel: disabled
    return _privacy_pipeline if _privacy_pipeline is not False else None


# ── Singleton provider instances (created on first use) ───────

_providers: dict[str, LLMProvider] = {}


def _get_provider(name: str) -> LLMProvider:
    """Return (and lazily create) the provider instance for *name*."""
    if name not in _providers:
        if name == "ollama":
            _providers[name] = OllamaProvider()
        elif name == "aifoundry":
            _providers[name] = AIFoundryProvider()
        elif name == "ghcopilot":
            _providers[name] = GHCopilotProvider()
        else:
            raise ValueError(
                f"Unknown provider '{name}'. Must be 'ollama', 'aifoundry', or 'ghcopilot'."
            )
    return _providers[name]


def chat_completion(
    messages: list[dict[str, str]],
    provider: str = DEFAULT_PROVIDER,
    model: str = DEFAULT_MODEL,
    temperature: float | None = DEFAULT_TEMPERATURE,
    json_mode: bool = False,
) -> str:
    """Send *messages* to the selected provider and return the assistant reply."""
    prov = _get_provider(provider)

    # ── Privacy auto-filter (safety net for remote calls) ─────
    _remote_providers = {"aifoundry", "ghcopilot"}
    pipeline = _get_privacy_pipeline() if provider in _remote_providers else None
    vault = None
    if pipeline is not None:
        from hybridagents.privacy.vault import EntityVault
        vault = EntityVault()
        messages, vault = pipeline.scrub_messages(messages, vault=vault)

    raw = prov.chat(messages, model=model, temperature=temperature, json_mode=json_mode)

    if vault is not None and pipeline is not None:
        raw = pipeline.restore(raw, vault)

    return raw


def parse_json_response(text: str) -> dict[str, Any]:
    """
    Best-effort extraction of a JSON object from LLM output.
    Handles markdown code-fences and stray text around the JSON.
    """
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strip markdown fences
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Find first { … } block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return {}
