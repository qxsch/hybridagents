"""
EntityVault – bidirectional, reversible mapping between real values and placeholders.

The vault lives locally and is never sent to a remote LLM.
It supports JSON serialisation for debugging, persistence, and testing.
"""

from __future__ import annotations

import json
from collections import defaultdict
from typing import Any


class EntityVault:
    """
    Stores the mapping  placeholder ↔ original_value  so that anonymised
    text can be restored after the remote LLM responds.

    Usage::

        vault = EntityVault()
        p = vault.store("max@firma.de", category="email")   # → "<EMAIL_1>"
        vault.resolve("<EMAIL_1>")                            # → "max@firma.de"
    """

    def __init__(self) -> None:
        # placeholder → original
        self._forward: dict[str, str] = {}
        # original   → placeholder  (for dedup)
        self._reverse: dict[str, str] = {}
        # category   → running counter
        self._counters: dict[str, int] = defaultdict(int)

    # ── public API ─────────────────────────────────────────────

    def store(self, original: str, category: str) -> str:
        """
        Register an original value and return its placeholder.
        If the same *original* was already stored, return the existing
        placeholder (stable mapping).
        """
        if original in self._reverse:
            return self._reverse[original]

        self._counters[category] += 1
        idx = self._counters[category]
        placeholder = f"<{category.upper()}_{idx}>"

        self._forward[placeholder] = original
        self._reverse[original] = placeholder
        return placeholder

    def resolve(self, placeholder: str) -> str | None:
        """Return the original value for a placeholder, or *None*."""
        return self._forward.get(placeholder)

    def has_original(self, original: str) -> bool:
        return original in self._reverse

    def placeholder_for(self, original: str) -> str | None:
        return self._reverse.get(original)

    @property
    def size(self) -> int:
        return len(self._forward)

    @property
    def placeholders(self) -> list[str]:
        return list(self._forward.keys())

    def items(self) -> list[tuple[str, str]]:
        """Return list of (placeholder, original) pairs."""
        return list(self._forward.items())

    # ── serialisation ──────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        return {
            "mappings": dict(self._forward),
            "counters": dict(self._counters),
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EntityVault":
        vault = cls()
        for placeholder, original in data.get("mappings", {}).items():
            vault._forward[placeholder] = original
            vault._reverse[original] = placeholder
        for cat, count in data.get("counters", {}).items():
            vault._counters[cat] = count
        return vault

    @classmethod
    def from_json(cls, text: str) -> "EntityVault":
        return cls.from_dict(json.loads(text))

    # ── restore helper ─────────────────────────────────────────

    def restore_text(self, text: str) -> str:
        """Replace all known placeholders in *text* with originals."""
        result = text
        # Sort by length descending to avoid partial replacements
        for placeholder in sorted(self._forward, key=len, reverse=True):
            result = result.replace(placeholder, self._forward[placeholder])
        return result

    def clear(self) -> None:
        self._forward.clear()
        self._reverse.clear()
        self._counters.clear()

    def __repr__(self) -> str:
        return f"EntityVault({self.size} entries)"
