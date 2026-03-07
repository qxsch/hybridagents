"""
RegexFilter – a user-configurable generic regex filter.

Use this when you want to add quick custom patterns without writing
a full Filter subclass.  Several instances can coexist with different
names.

Usage::

    from agents.privacy.filters.regex_filter import RegexFilter

    f = RegexFilter(
        name="project_id",
        category="internal",
        patterns=[r"PRJ-\\d{6}"],
        placeholder_prefix="PROJECT_ID",
    )
    detections = f.scan("Issue PRJ-123456 is open")
"""

from __future__ import annotations

import re

from agents.privacy.filters.base import Filter
from agents.privacy.models import Detection


class RegexFilter(Filter):
    """
    Generic regex-based filter.  Instantiate with one or more patterns
    and a category.
    """

    def __init__(
        self,
        name: str,
        category: str,
        patterns: list[str],
        *,
        placeholder_prefix: str | None = None,
        confidence: float = 1.0,
    ) -> None:
        self.name = name
        self.category = category
        self._compiled = [re.compile(p) for p in patterns]
        self._prefix = placeholder_prefix or name.upper()
        self._confidence = confidence

    @property
    def _placeholder_category(self) -> str:
        return self._prefix

    def scan(self, text: str) -> list[Detection]:
        detections: list[Detection] = []
        seen_spans: set[tuple[int, int]] = set()

        for pat in self._compiled:
            for m in pat.finditer(text):
                span = (m.start(), m.end())
                if any(s[0] <= span[0] < s[1] for s in seen_spans):
                    continue
                seen_spans.add(span)
                detections.append(
                    Detection(
                        filter_name=self.name,
                        category=self.category,
                        start=m.start(),
                        end=m.end(),
                        original=m.group(),
                        confidence=self._confidence,
                    )
                )

        detections.sort(key=lambda d: d.start)
        return detections
