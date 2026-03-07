"""
Privacy SDK – anonymisation & filtering for remote LLM calls.

Usage::

    from agents.privacy import PrivacyPipeline, PrivacyConfig, EntityVault

    pipeline = PrivacyPipeline.from_config(PrivacyConfig.default())
    result   = pipeline.scan("max@firma.de, IBAN DE89370400440532013000")
    scrubbed, vault = pipeline.scrub("Send €5,000 to max@firma.de")
    restored = pipeline.restore("<EMAIL_1> confirmed", vault)
"""

from agents.privacy.config import PrivacyConfig, LLMFilterConfig, CustomPatternConfig
from agents.privacy.models import Detection, ScanResult
from agents.privacy.vault import EntityVault
from agents.privacy.pipeline import PrivacyPipeline
from agents.privacy.filters.base import Filter
from agents.privacy.filters.regex_filter import RegexFilter

__all__ = [
    "PrivacyPipeline",
    "PrivacyConfig",
    "LLMFilterConfig",
    "CustomPatternConfig",
    "Detection",
    "ScanResult",
    "EntityVault",
    "Filter",
    "RegexFilter",
]
