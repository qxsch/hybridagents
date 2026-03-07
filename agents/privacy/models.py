"""
Data models for the privacy SDK.

These are plain dataclasses with no dependency on the agent framework,
so they can be used standalone in tests, scripts, and notebooks.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Detection:
    """A single detected sensitive entity in a text."""

    filter_name: str          # e.g. "email", "iban", "llm"
    category: str             # e.g. "pii", "financial", "credentials"
    start: int                # char offset in original text
    end: int                  # char offset (exclusive)
    original: str             # the matched substring
    placeholder: str = ""     # e.g. "<EMAIL_1>" – filled by the vault
    confidence: float = 1.0   # 1.0 for regex, 0–1 for LLM-based

    @property
    def length(self) -> int:
        return self.end - self.start

    def __repr__(self) -> str:
        return (
            f"Detection({self.filter_name!r}, {self.original!r} "
            f"→ {self.placeholder!r}, conf={self.confidence:.2f})"
        )


@dataclass
class ScanResult:
    """Aggregated result of scanning a text through the pipeline."""

    original_text: str
    detections: list[Detection] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.detections)

    @property
    def categories(self) -> set[str]:
        return {d.category for d in self.detections}

    @property
    def filter_names(self) -> set[str]:
        return {d.filter_name for d in self.detections}

    def by_category(self, category: str) -> list[Detection]:
        return [d for d in self.detections if d.category == category]

    def by_filter(self, name: str) -> list[Detection]:
        return [d for d in self.detections if d.filter_name == name]

    def above_confidence(self, threshold: float) -> list[Detection]:
        return [d for d in self.detections if d.confidence >= threshold]

    def summary(self) -> str:
        if not self.detections:
            return "No detections."
        lines = [f"Detections ({self.count} found):"]
        for d in self.detections:
            lines.append(
                f"  [{d.filter_name}] {d.original!r:30s} → {d.placeholder:16s} "
                f"confidence: {d.confidence:.2f}"
            )
        return "\n".join(lines)
