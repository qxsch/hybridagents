"""
Filter: email addresses.
"""

from __future__ import annotations

import re

from agents.privacy.filters.base import Filter
from agents.privacy.models import Detection

# Broad but practical email regex
_EMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
)


class EmailFilter(Filter):
    name = "email"
    category = "pii"

    def scan(self, text: str) -> list[Detection]:
        detections: list[Detection] = []
        for m in _EMAIL_RE.finditer(text):
            detections.append(
                Detection(
                    filter_name=self.name,
                    category=self.category,
                    start=m.start(),
                    end=m.end(),
                    original=m.group(),
                    confidence=1.0,
                )
            )
        return detections
