"""
Privacy SDK – anonymisation & filtering for remote LLM calls.

Usage::

    from hybridagents.privacy import PrivacyPipeline, PrivacyConfig, EntityVault

    pipeline = PrivacyPipeline.from_config(PrivacyConfig.default())
    result   = pipeline.scan("max@firma.de, IBAN DE89370400440532013000")
    scrubbed, vault = pipeline.scrub("Send €5,000 to max@firma.de")
    restored = pipeline.restore("<EMAIL_1> confirmed", vault)
"""

from hybridagents.privacy.config import PrivacyConfig, LLMFilterConfig, CustomPatternConfig
from hybridagents.privacy.models import Detection, ScanResult
from hybridagents.privacy.vault import EntityVault
from hybridagents.privacy.pipeline import PrivacyPipeline
from hybridagents.privacy.filters.base import Filter
from hybridagents.privacy.filters.regex_filter import RegexFilter

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
