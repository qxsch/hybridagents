"""
Filter: tax identifiers for DACH region (Germany, Austria, Switzerland).

Detected patterns:
- German Steuernummer (10-13 digits, slash-separated)
- German Steuer-ID (11-digit TIN)
- German USt-IdNr (DE + 9 digits)
- Austrian UID (ATU + 8 digits)
- Swiss UID (CHE-NNN.NNN.NNN)
"""

from __future__ import annotations

import re

from hybridagents.privacy.filters.base import Filter
from hybridagents.privacy.models import Detection

_PATTERNS: list[tuple[re.Pattern, str, float]] = [
    # German USt-IdNr: DE123456789
    (re.compile(r"\bDE\s?\d{9}\b"), "ust_id", 1.0),
    # Austrian UID: ATU12345678
    (re.compile(r"\bATU\d{8}\b"), "uid_at", 1.0),
    # Swiss UID: CHE-123.456.789 or CHE123456789
    (re.compile(r"\bCHE[\-]?\d{3}\.?\d{3}\.?\d{3}\b"), "uid_ch", 1.0),
    # German Steuer-ID (TIN): exactly 11 digits
    (re.compile(r"(?:Steuer[\-\s]?ID|IdNr|TIN)[:\s]*(\d{11})\b", re.IGNORECASE), "steuer_id", 0.95),
    # German Steuernummer: various formats like 12/345/67890 or 1234567890
    (re.compile(r"(?:Steuernummer|St[\.\-]?Nr)[:\s]*(\d{2,5}[/\s]\d{3,4}[/\s]\d{4,5})\b", re.IGNORECASE), "steuernummer", 0.90),
]


class TaxIdFilter(Filter):
    name = "tax_id"
    category = "financial"

    def scan(self, text: str) -> list[Detection]:
        detections: list[Detection] = []
        seen_spans: set[tuple[int, int]] = set()

        for pattern, label, confidence in _PATTERNS:
            for m in pattern.finditer(text):
                # Use the first group if one exists, else the whole match
                if m.lastindex:
                    original = m.group(1)
                    start = m.start(1)
                    end = m.end(1)
                else:
                    original = m.group()
                    start = m.start()
                    end = m.end()

                span = (start, end)
                if any(s[0] <= span[0] < s[1] for s in seen_spans):
                    continue
                seen_spans.add(span)

                detections.append(
                    Detection(
                        filter_name=self.name,
                        category=self.category,
                        start=start,
                        end=end,
                        original=original,
                        confidence=confidence,
                    )
                )

        detections.sort(key=lambda d: d.start)
        return detections
