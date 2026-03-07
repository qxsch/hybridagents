"""
Abstract base class for privacy filters.

Every filter detects one category of sensitive data and can replace
matches with placeholders.  Filters are usable standalone — no
dependency on the agent framework.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from hybridagents.privacy.models import Detection
from hybridagents.privacy.vault import EntityVault


class Filter(ABC):
    """
    Base class for all privacy filters.

    Subclasses must set ``name`` and ``category`` and implement
    :meth:`scan`.  The default :meth:`replace` uses :meth:`scan`
    to find detections and swaps them out via the vault.
    """

    name: str = ""          # e.g. "email"
    category: str = ""      # e.g. "pii", "financial", "credentials"

    @abstractmethod
    def scan(self, text: str) -> list[Detection]:
        """Return all detections in *text* (positions + original values)."""
        ...

    def replace(self, text: str, vault: EntityVault) -> tuple[str, list[Detection]]:
        """
        Scan *text*, replace every detection with its vault placeholder,
        and return ``(scrubbed_text, detections)``.

        Replacements are applied right-to-left so character offsets stay
        valid.
        """
        detections = self.scan(text)
        if not detections:
            return text, []

        # Sort by start position descending → replace from end to start
        detections.sort(key=lambda d: d.start, reverse=True)

        result = text
        for det in detections:
            placeholder = vault.store(det.original, category=self._placeholder_category)
            det.placeholder = placeholder
            result = result[: det.start] + placeholder + result[det.end :]

        # Re-sort ascending for consistent output order
        detections.sort(key=lambda d: d.start)
        return result, detections

    @property
    def _placeholder_category(self) -> str:
        """Category string used in placeholder tokens, e.g. 'EMAIL' for <EMAIL_1>."""
        return self.name.upper()

    def __repr__(self) -> str:
        return f"{type(self).__name__}(name={self.name!r})"
