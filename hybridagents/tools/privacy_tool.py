"""
Agent tools: privacy_scan, privacy_anonymize, privacy_deanonymize.

These tools let agents explicitly scan, scrub, and restore text.
They use a shared pipeline + vault instance per session so that
anonymize / deanonymize calls stay consistent.
"""

from __future__ import annotations

import json

from hybridagents.core.tool_registry import tool
from hybridagents.privacy.config import PrivacyConfig
from hybridagents.privacy.pipeline import PrivacyPipeline
from hybridagents.privacy.vault import EntityVault

# ── Module-level shared state (per process) ─────────────────

_pipeline: PrivacyPipeline | None = None
_vault: EntityVault = EntityVault()


def get_pipeline() -> PrivacyPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = PrivacyPipeline.from_config(PrivacyConfig.from_env())
    return _pipeline


def get_vault() -> EntityVault:
    return _vault


def reset() -> None:
    """Reset shared state (useful in tests)."""
    global _pipeline, _vault
    _pipeline = None
    _vault = EntityVault()


def _parse_filters(raw: str) -> list[str] | None:
    if not raw or not raw.strip():
        return None
    return [f.strip() for f in raw.split(",") if f.strip()]


# ── Tools ───────────────────────────────────────────────────

@tool(
    name="privacy_scan",
    description=(
        "Scan text for PII, financial data, and credentials. "
        "Returns a structured report of detections WITHOUT modifying the text. "
        "Use this to inspect what would be anonymised before actually scrubbing."
    ),
    parameters={
        "text": {"type": "string", "description": "The text to scan for sensitive data"},
        "filters": {
            "type": "string",
            "description": "Comma-separated filter names to use (default: all). Options: email, phone, iban, tax_id, credential, money",
        },
    },
)
def privacy_scan(text: str, filters: str = "") -> str:
    pipeline = get_pipeline()
    result = pipeline.scan(text, filter_names=_parse_filters(filters))

    if not result.detections:
        return "No sensitive data detected."

    lines = [f"Detections ({result.count}):"]
    for d in result.detections:
        lines.append(
            f"  [{d.filter_name}] '{d.original}' (confidence: {d.confidence:.2f})"
        )
    return "\n".join(lines)


@tool(
    name="privacy_anonymize",
    description=(
        "Anonymise text by replacing sensitive data (PII, financial, credentials) "
        "with safe placeholders like <EMAIL_1>, <IBAN_1>, <MONEY_1>. "
        "The mapping is stored in a vault so it can be reversed later with privacy_deanonymize. "
        "Use this BEFORE sending data to a remote/cloud LLM."
    ),
    parameters={
        "text": {"type": "string", "description": "The text to anonymise"},
        "filters": {
            "type": "string",
            "description": "Comma-separated filter names (default: all). Options: email, phone, iban, tax_id, credential, money",
        },
    },
)
def privacy_anonymize(text: str, filters: str = "") -> str:
    pipeline = get_pipeline()
    vault = get_vault()
    scrubbed, _ = pipeline.scrub(text, vault=vault, filter_names=_parse_filters(filters))
    return scrubbed


@tool(
    name="privacy_deanonymize",
    description=(
        "Restore placeholders in text back to their original values using the vault. "
        "Use this AFTER receiving a response from a remote/cloud LLM to put the real data back."
    ),
    parameters={
        "text": {"type": "string", "description": "Text containing placeholders (e.g. <EMAIL_1>) to restore"},
    },
)
def privacy_deanonymize(text: str) -> str:
    vault = get_vault()
    restored = vault.restore_text(text)
    return restored
