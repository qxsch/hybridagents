"""
Filter: credentials, secrets, and connection strings.

Catches common patterns for:
- API keys (OpenAI, Azure, AWS, generic)
- Bearer / Basic auth tokens
- Connection strings (postgresql://, mongodb://, etc.)
- Private keys
- Passwords in URLs or config-like text
"""

from __future__ import annotations

import re

from hybridagents.privacy.filters.base import Filter
from hybridagents.privacy.models import Detection

_PATTERNS: list[tuple[re.Pattern, str, float]] = [
    # OpenAI keys: sk-...
    (re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"), "openai_key", 1.0),
    # Azure keys (hex, 32+ chars)
    (re.compile(r"\b[0-9a-f]{32,}\b"), "azure_key", 0.60),
    # AWS access key ID
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "aws_key", 1.0),
    # Bearer / Basic tokens
    (re.compile(r"(?:Bearer|Basic)\s+[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE), "auth_token", 0.95),
    # Connection strings: scheme://user:pass@host
    (re.compile(r"\b(?:postgres(?:ql)?|mysql|mongodb|redis|amqp|mssql)://\S+", re.IGNORECASE), "connection_string", 1.0),
    # Generic password in key=value patterns
    (re.compile(r"(?:password|passwd|pwd|secret|token|api_key|apikey)[\s]*[=:]\s*['\"]?(\S{6,})['\"]?", re.IGNORECASE), "password_value", 0.85),
    # PEM private keys
    (re.compile(r"-----BEGIN (?:RSA |EC |DSA )?PRIVATE KEY-----"), "private_key", 1.0),
]


class CredentialFilter(Filter):
    name = "credential"
    category = "credentials"

    def scan(self, text: str) -> list[Detection]:
        detections: list[Detection] = []
        seen_spans: set[tuple[int, int]] = set()

        for pattern, label, confidence in _PATTERNS:
            for m in pattern.finditer(text):
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
