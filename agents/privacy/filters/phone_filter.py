"""
Filter: phone numbers (international & DACH formats).
"""

from __future__ import annotations

import re

from agents.privacy.filters.base import Filter
from agents.privacy.models import Detection

# Matches international format (+49 ...), common DACH formats, and generic digit groups
_PHONE_PATTERNS = [
    # International: +49 170 1234567, +43-1-12345, +41 44 123 45 67
    re.compile(r"\+\d{1,3}[\s\-]?\(?\d{1,5}\)?[\s\-]?\d[\d\s\-]{4,15}\d"),
    # German local: 0170 1234567, 089/12345678, (089) 12345
    re.compile(r"\(?\b0\d{1,5}\)?[\s/\-]\d[\d\s/\-]{4,12}\d\b"),
]


class PhoneFilter(Filter):
    name = "phone"
    category = "pii"

    def scan(self, text: str) -> list[Detection]:
        detections: list[Detection] = []
        seen_spans: set[tuple[int, int]] = set()

        for pattern in _PHONE_PATTERNS:
            for m in pattern.finditer(text):
                span = (m.start(), m.end())
                # Avoid overlapping matches from different patterns
                if any(s[0] <= span[0] < s[1] or s[0] < span[1] <= s[1] for s in seen_spans):
                    continue
                seen_spans.add(span)
                detections.append(
                    Detection(
                        filter_name=self.name,
                        category=self.category,
                        start=m.start(),
                        end=m.end(),
                        original=m.group(),
                        confidence=0.90,
                    )
                )

        detections.sort(key=lambda d: d.start)
        return detections
