"""
PrivacyConfig – declarative configuration for the privacy pipeline.

Supports construction from code, environment variables, or a YAML/JSON file.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CustomPatternConfig:
    """Quick-add regex pattern without writing a full Filter subclass."""

    name: str
    pattern: str                          # regex
    category: str = "custom"
    placeholder_prefix: str | None = None  # defaults to NAME.upper()
    confidence: float = 1.0


@dataclass
class LLMFilterConfig:
    """Settings for the optional local-LLM filter."""

    enabled: bool = False
    provider: str = "ollama"              # always local
    model: str = "phi4"
    categories: list[str] = field(default_factory=lambda: ["person_name", "company_name", "address"])
    confidence: float = 0.80
    extra_prompt: str = ""                # additional user-supplied instructions
    use_llm_confidence: bool = False      # blend LLM's per-entity confidence score


@dataclass
class PrivacyConfig:
    """
    Top-level configuration for the privacy pipeline.

    Create via:
    - ``PrivacyConfig(...)``           – from code
    - ``PrivacyConfig.from_env()``     – from environment / .env
    - ``PrivacyConfig.from_file(p)``   – from JSON or YAML
    - ``PrivacyConfig.default()``      – all built-in filters, sane defaults
    """

    # Which built-in filters to activate (empty → all)
    filters: list[str] = field(default_factory=list)

    # Minimum confidence to keep a detection
    confidence_threshold: float = 0.0

    # "redact" → <PLACEHOLDER>, "mask" → ****, "summarize" → (future)
    mode: str = "redact"

    # Auto-filter on remote provider calls (safety net in llm.py)
    auto_filter_enabled: bool = False

    # LLM-based filter (local only)
    llm_filter: LLMFilterConfig = field(default_factory=LLMFilterConfig)

    # Quick custom patterns
    custom_patterns: list[CustomPatternConfig] = field(default_factory=list)

    # ── Factory methods ────────────────────────────────────────

    @classmethod
    def default(cls) -> "PrivacyConfig":
        """All built-in filters enabled, sane defaults."""
        return cls(filters=[])  # empty = all

    @classmethod
    def from_env(cls) -> "PrivacyConfig":
        """Read configuration from environment variables."""
        filters_str = os.getenv("PRIVACY_FILTERS", "")
        filters = [f.strip() for f in filters_str.split(",") if f.strip()] if filters_str else []
        threshold = float(os.getenv("PRIVACY_CONFIDENCE_THRESHOLD", "0.0"))
        mode = os.getenv("PRIVACY_MODE", "redact")
        auto = os.getenv("PRIVACY_AUTO_FILTER", "false").lower() in ("1", "true", "yes")

        llm_enabled = os.getenv("PRIVACY_LLM_FILTER", "false").lower() in ("1", "true", "yes")
        llm_model = os.getenv("PRIVACY_LLM_MODEL", "phi4")
        llm_cats_str = os.getenv("PRIVACY_LLM_CATEGORIES", "person_name,company_name,address")
        llm_cats = [c.strip() for c in llm_cats_str.split(",") if c.strip()]
        llm_extra = os.getenv("PRIVACY_LLM_EXTRA_PROMPT", "")
        llm_use_conf = os.getenv("PRIVACY_LLM_USE_LLM_CONFIDENCE", "false").lower() in ("1", "true", "yes")

        return cls(
            filters=filters,
            confidence_threshold=threshold,
            mode=mode,
            auto_filter_enabled=auto,
            llm_filter=LLMFilterConfig(
                enabled=llm_enabled,
                model=llm_model,
                categories=llm_cats,
                extra_prompt=llm_extra,
                use_llm_confidence=llm_use_conf,
            ),
        )

    @classmethod
    def from_file(cls, path: str | Path) -> "PrivacyConfig":
        """Load configuration from a JSON or YAML file."""
        path = Path(path)
        text = path.read_text(encoding="utf-8")

        if path.suffix in (".yaml", ".yml"):
            try:
                import yaml  # type: ignore
                data = yaml.safe_load(text)
            except ImportError:
                raise ImportError("PyYAML is required to load .yaml config files: pip install pyyaml")
        else:
            data = json.loads(text)

        return cls._from_dict(data)

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> "PrivacyConfig":
        llm_data = data.get("llm_filter", {})
        llm_cfg = LLMFilterConfig(
            enabled=llm_data.get("enabled", False),
            provider=llm_data.get("provider", "ollama"),
            model=llm_data.get("model", "phi4"),
            categories=llm_data.get("categories", ["person_name", "company_name", "address"]),
            confidence=llm_data.get("confidence", 0.80),
            extra_prompt=llm_data.get("extra_prompt", ""),
            use_llm_confidence=llm_data.get("use_llm_confidence", False),
        )

        custom_raw = data.get("custom_patterns", [])
        customs = [
            CustomPatternConfig(
                name=c["name"],
                pattern=c["pattern"],
                category=c.get("category", "custom"),
                placeholder_prefix=c.get("placeholder_prefix"),
                confidence=c.get("confidence", 1.0),
            )
            for c in custom_raw
        ]

        return cls(
            filters=data.get("filters", []),
            confidence_threshold=data.get("confidence_threshold", 0.0),
            mode=data.get("mode", "redact"),
            auto_filter_enabled=data.get("auto_filter_enabled", False),
            llm_filter=llm_cfg,
            custom_patterns=customs,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "filters": self.filters,
            "confidence_threshold": self.confidence_threshold,
            "mode": self.mode,
            "auto_filter_enabled": self.auto_filter_enabled,
            "llm_filter": {
                "enabled": self.llm_filter.enabled,
                "provider": self.llm_filter.provider,
                "model": self.llm_filter.model,
                "categories": self.llm_filter.categories,
                "confidence": self.llm_filter.confidence,
                "extra_prompt": self.llm_filter.extra_prompt,
                "use_llm_confidence": self.llm_filter.use_llm_confidence,
            },
            "custom_patterns": [
                {
                    "name": c.name,
                    "pattern": c.pattern,
                    "category": c.category,
                    "placeholder_prefix": c.placeholder_prefix,
                    "confidence": c.confidence,
                }
                for c in self.custom_patterns
            ],
        }
