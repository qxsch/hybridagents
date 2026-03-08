"""
PrivacyPipeline – chains filters, runs scan / scrub / restore.

This is the main entry point for the privacy SDK.  It is completely
independent of the agent framework and can be used from scripts,
tests, or notebooks.
"""

from __future__ import annotations

from typing import Any

from hybridagents.privacy.config import PrivacyConfig
from hybridagents.privacy.filters import (
    Filter,
    BUILTIN_FILTERS,
    RegexFilter,
)
from hybridagents.privacy.models import Detection, ScanResult
from hybridagents.privacy.vault import EntityVault


class PrivacyPipeline:
    """
    Chains one or more :class:`Filter` instances and provides
    ``scan``, ``scrub``, and ``restore`` operations.

    Usage::

        pipeline = PrivacyPipeline.from_config(PrivacyConfig.default())

        # Scan only (inspect detections)
        result = pipeline.scan("Email max@firma.de, IBAN DE89370400440532013000")

        # Scrub (anonymise)
        scrubbed, vault = pipeline.scrub("Email max@firma.de")

        # Restore (de-anonymise)
        restored = pipeline.restore("<EMAIL_1> is the address", vault)
    """

    def __init__(self, filters: list[Filter] | None = None, config: PrivacyConfig | None = None) -> None:
        self._filters: list[Filter] = filters or []
        self._config = config or PrivacyConfig.default()

    # ── Construction ───────────────────────────────────────────

    @classmethod
    def from_config(cls, config: PrivacyConfig) -> "PrivacyPipeline":
        """Build a pipeline from a :class:`PrivacyConfig`."""
        filters: list[Filter] = []

        # Determine which built-in filters to enable
        names = config.filters if config.filters else list(BUILTIN_FILTERS.keys())
        for name in names:
            filt_cls = BUILTIN_FILTERS.get(name)
            if filt_cls is not None:
                filters.append(filt_cls())

        # Custom regex patterns
        for cp in config.custom_patterns:
            filters.append(
                RegexFilter(
                    name=cp.name,
                    category=cp.category,
                    patterns=[cp.pattern],
                    placeholder_prefix=cp.placeholder_prefix or cp.name.upper(),
                    confidence=cp.confidence,
                )
            )

        # LLM filter is added lazily (see add_llm_filter / pipeline.py keeps it optional)
        pipeline = cls(filters=filters, config=config)

        if config.llm_filter.enabled:
            pipeline._add_llm_filter(config)

        return pipeline

    def _add_llm_filter(self, config: PrivacyConfig) -> None:
        """Add the local-LLM filter (import lazily to avoid hard dep)."""
        try:
            from hybridagents.privacy.filters.llm_filter import LLMFilter

            self._filters.append(
                LLMFilter(
                    provider=config.llm_filter.provider,
                    model=config.llm_filter.model,
                    categories=config.llm_filter.categories,
                    confidence=config.llm_filter.confidence,
                    extra_prompt=config.llm_filter.extra_prompt,
                    use_llm_confidence=config.llm_filter.use_llm_confidence,
                )
            )
        except ImportError:
            pass  # LLM filter not available – skip silently

    # ── Public API: filter management ──────────────────────────

    def add_filter(self, filt: Filter) -> None:
        """Add a custom filter to the pipeline."""
        self._filters.append(filt)

    def add_regex_filter(
        self,
        name: str,
        patterns: list[str],
        *,
        category: str = "custom",
        placeholder_prefix: str | None = None,
        confidence: float = 1.0,
    ) -> RegexFilter:
        """
        Convenience: create and add a :class:`RegexFilter` in one call.

        Returns the newly created filter so callers can keep a reference.

        Usage::

            pipeline.add_regex_filter(
                name="order_id",
                patterns=[r"ORD-\\d{6,10}"],
                category="internal",
                placeholder_prefix="ORDER_ID",
            )
        """
        filt = RegexFilter(
            name=name,
            category=category,
            patterns=patterns,
            placeholder_prefix=placeholder_prefix or name.upper(),
            confidence=confidence,
        )
        self._filters.append(filt)
        return filt

    def remove_filter(self, name: str) -> None:
        """Remove a filter by name."""
        self._filters = [f for f in self._filters if f.name != name]

    @property
    def filter_names(self) -> list[str]:
        return [f.name for f in self._filters]

    # ── Public API: scan / scrub / restore ─────────────────────

    def scan(self, text: str, *, filter_names: list[str] | None = None) -> ScanResult:
        """
        Scan *text* through all (or selected) filters and return
        detections without modifying the text.
        """
        filters = self._select_filters(filter_names)
        all_detections: list[Detection] = []

        for filt in filters:
            dets = filt.scan(text)
            all_detections.extend(dets)

        # Apply confidence threshold
        threshold = self._config.confidence_threshold
        if threshold > 0:
            all_detections = [d for d in all_detections if d.confidence >= threshold]

        # De-duplicate overlapping detections (keep higher confidence)
        all_detections = self._deduplicate(all_detections)
        all_detections.sort(key=lambda d: d.start)

        return ScanResult(original_text=text, detections=all_detections)

    def scrub(
        self,
        text: str,
        *,
        vault: EntityVault | None = None,
        filter_names: list[str] | None = None,
    ) -> tuple[str, EntityVault]:
        """
        Scan and replace all detections with placeholders.
        Returns ``(scrubbed_text, vault)``.
        """
        if vault is None:
            vault = EntityVault()

        # First collect all detections
        scan_result = self.scan(text, filter_names=filter_names)

        if not scan_result.detections:
            return text, vault

        # Replace from end to start so offsets stay valid
        detections = sorted(scan_result.detections, key=lambda d: d.start, reverse=True)
        result = text
        for det in detections:
            placeholder = vault.store(det.original, category=det.filter_name.upper())
            det.placeholder = placeholder
            result = result[: det.start] + placeholder + result[det.end :]

        return result, vault

    def restore(self, text: str, vault: EntityVault) -> str:
        """Replace all placeholders in *text* with their original values."""
        return vault.restore_text(text)

    def scrub_messages(
        self,
        messages: list[dict[str, str]],
        *,
        vault: EntityVault | None = None,
    ) -> tuple[list[dict[str, str]], EntityVault]:
        """
        Scrub every message in an OpenAI-style messages list.
        Returns ``(scrubbed_messages, vault)``.
        """
        if vault is None:
            vault = EntityVault()

        scrubbed: list[dict[str, str]] = []
        for msg in messages:
            content = msg.get("content", "")
            new_content, vault = self.scrub(content, vault=vault)
            scrubbed.append({**msg, "content": new_content})

        return scrubbed, vault

    # ── Helpers ─────────────────────────────────────────────────

    def _select_filters(self, names: list[str] | None) -> list[Filter]:
        if names is None:
            return self._filters
        return [f for f in self._filters if f.name in names]

    @staticmethod
    def _deduplicate(detections: list[Detection]) -> list[Detection]:
        """Remove overlapping detections, keeping the one with highest confidence."""
        if not detections:
            return []

        # Sort by start, then by confidence descending
        detections.sort(key=lambda d: (d.start, -d.confidence))
        result: list[Detection] = []
        last_end = -1

        for det in detections:
            if det.start >= last_end:
                result.append(det)
                last_end = det.end
            else:
                # Overlapping – keep the one with higher confidence
                # (the current `result[-1]` was added first, with higher or equal conf)
                pass

        return result

    def __repr__(self) -> str:
        return f"PrivacyPipeline(filters={self.filter_names})"
