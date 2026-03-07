"""
Filter: IBAN (International Bank Account Numbers).

Validates structure and checksum for common DACH + EU countries.
"""

from __future__ import annotations

import re

from agents.privacy.filters.base import Filter
from agents.privacy.models import Detection

# IBAN: 2 uppercase letters + 2 check digits + up to 30 alphanumeric
# Accepts both compact and space-separated formats
_IBAN_RE = re.compile(
    r"\b([A-Z]{2}\d{2})\s?(\d{4})\s?(\d{4})\s?(\d{4})\s?(\d{4})\s?(\d{0,4})\s?(\d{0,4})\s?(\d{0,2})\b"
)

# Simpler fallback: any string that looks like an IBAN with spaces
_IBAN_SIMPLE_RE = re.compile(
    r"\b[A-Z]{2}\d{2}\s?[\dA-Z]{4}[\s]?[\dA-Z]{4}[\s]?[\dA-Z\s]{4,26}\b"
)


def _validate_iban_checksum(iban: str) -> bool:
    """Validate IBAN using MOD-97 (ISO 7064)."""
    cleaned = iban.replace(" ", "").upper()
    if len(cleaned) < 15 or len(cleaned) > 34:
        return False
    # Move first 4 chars to end
    rearranged = cleaned[4:] + cleaned[:4]
    # Convert letters to numbers (A=10, B=11, …)
    numeric = ""
    for ch in rearranged:
        if ch.isdigit():
            numeric += ch
        else:
            numeric += str(ord(ch) - ord("A") + 10)
    try:
        return int(numeric) % 97 == 1
    except ValueError:
        return False


class IbanFilter(Filter):
    name = "iban"
    category = "financial"

    def scan(self, text: str) -> list[Detection]:
        detections: list[Detection] = []
        seen_spans: set[tuple[int, int]] = set()

        # Try strict regex first
        for m in _IBAN_RE.finditer(text):
            raw = m.group().replace(" ", "")
            if len(raw) < 15:
                continue
            valid = _validate_iban_checksum(raw)
            span = (m.start(), m.end())
            seen_spans.add(span)
            detections.append(
                Detection(
                    filter_name=self.name,
                    category=self.category,
                    start=m.start(),
                    end=m.end(),
                    original=m.group(),
                    confidence=1.0 if valid else 0.80,
                )
            )

        # Fallback for formats the strict regex misses
        for m in _IBAN_SIMPLE_RE.finditer(text):
            span = (m.start(), m.end())
            if any(s[0] <= span[0] < s[1] for s in seen_spans):
                continue
            raw = m.group().replace(" ", "")
            if len(raw) < 15:
                continue
            valid = _validate_iban_checksum(raw)
            detections.append(
                Detection(
                    filter_name=self.name,
                    category=self.category,
                    start=m.start(),
                    end=m.end(),
                    original=m.group(),
                    confidence=1.0 if valid else 0.70,
                )
            )

        detections.sort(key=lambda d: d.start)
        return detections
