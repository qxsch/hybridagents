"""
Filter: monetary amounts and currency values.

Catches patterns like:
- €1.234,56 / EUR 1234.56 / 1.234,56 €
- $100,000.00 / USD 500 / CHF 1'200.00
- Written forms: 12.500 Euro, 500 Franken
"""

from __future__ import annotations

import re

from hybridagents.privacy.filters.base import Filter
from hybridagents.privacy.models import Detection

_PATTERNS: list[tuple[re.Pattern, float]] = [
    # €1.234,56 or € 1.234,56 or 1.234,56 € (German format)
    (re.compile(r"€\s?\d{1,3}(?:\.\d{3})*(?:,\d{1,2})?\b"), 1.0),
    (re.compile(r"\b\d{1,3}(?:\.\d{3})*(?:,\d{1,2})?\s?€"), 1.0),
    # $1,234.56 or $ 1,234.56 or 1,234.56 $ (US/intl format)
    (re.compile(r"\$\s?\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?\b"), 1.0),
    (re.compile(r"\b\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?\s?\$"), 1.0),
    # EUR/USD/CHF/GBP + amount
    (re.compile(r"\b(?:EUR|USD|CHF|GBP)\s?\d{1,3}(?:[.,'\s]\d{3})*(?:[.,]\d{1,2})?\b"), 1.0),
    # amount + EUR/USD/CHF/GBP
    (re.compile(r"\b\d{1,3}(?:[.,'\s]\d{3})*(?:[.,]\d{1,2})?\s?(?:EUR|USD|CHF|GBP)\b"), 1.0),
    # amount + Euro/Dollar/Franken (written)
    (re.compile(r"\b\d{1,3}(?:[.,'\s]\d{3})*(?:[.,]\d{1,2})?\s?(?:Euro|Dollar|Franken|Pfund)\b", re.IGNORECASE), 0.90),
]


class MoneyFilter(Filter):
    name = "money"
    category = "financial"

    def scan(self, text: str) -> list[Detection]:
        detections: list[Detection] = []
        seen_spans: set[tuple[int, int]] = set()

        for pattern, confidence in _PATTERNS:
            for m in pattern.finditer(text):
                span = (m.start(), m.end())
                # Skip if overlapping
                if any(
                    s[0] <= span[0] < s[1] or s[0] < span[1] <= s[1]
                    for s in seen_spans
                ):
                    continue
                seen_spans.add(span)
                detections.append(
                    Detection(
                        filter_name=self.name,
                        category=self.category,
                        start=m.start(),
                        end=m.end(),
                        original=m.group(),
                        confidence=confidence,
                    )
                )

        detections.sort(key=lambda d: d.start)
        return detections
