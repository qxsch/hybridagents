"""
LLM-based privacy filter – uses a LOCAL model (Ollama) to detect
entities that regex can't reliably catch: person names, company
names, addresses, etc.

**Key constraint:** This filter ALWAYS uses the local Ollama provider.
It never sends data to a remote endpoint – that would defeat the purpose.

Offset resolution strategy ("value is truth, offsets are hints"):
  1. The LLM's ``value`` field is the primary signal.
  2. ``start``/``end`` are treated as *hints* only.
  3. If the hint checks out (``text[start:end] == value``), use it.
  4. Otherwise find ALL occurrences of ``value`` in the text, pick the
     one closest to the hinted offset, and skip already-consumed spans.
  5. If no exact match, try case-insensitive / whitespace-normalised
     fuzzy matching.
  6. If still nothing, drop the detection and log it.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from hybridagents.privacy.filters.base import Filter
from hybridagents.privacy.models import Detection

log = logging.getLogger(__name__)


_SYSTEM_PROMPT = """\
You are a privacy-detection assistant.  Your ONLY job is to find personally
identifiable information (PII) and sensitive entities in the text the user gives you.

Return a JSON array of objects.  Each object MUST have:
  - "type": one of {categories}
  - "value": the exact substring from the text

Optionally include (but these are only hints - accuracy is not required):
  - "start": approximate character offset where the value starts (0-based)
  - "end": approximate character offset where the value ends (exclusive)

If you find nothing, return an empty array: []

Rules:
- Only report entities that actually appear as substrings.
- Do NOT invent entities.
- Do NOT report emails, phone numbers, IBANs, or monetary amounts —
  those are handled by other specialised filters.
- Respond ONLY with the JSON array, no extra text.
"""


# ── Helpers for robust offset resolution ──────────────────────


def _find_all(text: str, value: str) -> list[int]:
    """Return start indices of every non-overlapping occurrence of *value* in *text*."""
    positions: list[int] = []
    start = 0
    while True:
        idx = text.find(value, start)
        if idx == -1:
            break
        positions.append(idx)
        start = idx + len(value)
    return positions


def _find_all_casefold(text: str, value: str) -> list[tuple[int, str]]:
    """Case-insensitive search. Returns ``[(start, actual_substring), ...]``."""
    lower_text = text.casefold()
    lower_val = value.casefold()
    results: list[tuple[int, str]] = []
    start = 0
    while True:
        idx = lower_text.find(lower_val, start)
        if idx == -1:
            break
        # Grab the *original-case* substring so Detection.original is faithful
        results.append((idx, text[idx : idx + len(value)]))
        start = idx + len(value)
    return results


def _normalise_ws(s: str) -> str:
    """Collapse all whitespace runs into a single space and strip."""
    return re.sub(r"\s+", " ", s).strip()


def _find_fuzzy_ws(text: str, value: str) -> list[tuple[int, int, str]]:
    """
    Whitespace-normalised search.  Returns ``[(start, end, actual_substring), ...]``.
    Handles the case where the LLM returns ``"Max  Mustermann"`` but the text
    contains ``"Max Mustermann"`` (or vice-versa).
    """
    norm_val = _normalise_ws(value)
    if not norm_val:
        return []

    # Build a regex that allows flexible whitespace between the words
    words = norm_val.split(" ")
    if len(words) < 2:
        return []  # single word – exact/casefold match is enough
    pattern = r"\s+".join(re.escape(w) for w in words)
    results: list[tuple[int, int, str]] = []
    for m in re.finditer(pattern, text, re.IGNORECASE):
        results.append((m.start(), m.end(), m.group()))
    return results


def _safe_int(val: Any) -> int | None:
    """Coerce to int, return None on failure."""
    if val is None:
        return None
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def _closest(positions: list[int], hint: int) -> int:
    """Return the position closest to *hint*."""
    return min(positions, key=lambda p: abs(p - hint))


def _resolve_offset(
    source_text: str,
    value: str,
    hint_start: int | None,
    hint_end: int | None,
    consumed: set[tuple[int, int]],
) -> tuple[int, int, str, float] | None:
    """
    Resolve the actual ``(start, end, matched_value, confidence_modifier)``
    for *value* inside *source_text*.

    *consumed* tracks spans already claimed by earlier entities so the
    same occurrence isn't matched twice.

    Returns ``None`` if the value cannot be located at all.
    """

    def _span_free(s: int, e: int) -> bool:
        return not any(cs <= s < ce or cs < e <= ce for cs, ce in consumed)

    vlen = len(value)

    # ── 1. Exact match at hinted position ─────────────────────
    if hint_start is not None and hint_end is not None:
        if 0 <= hint_start < len(source_text) and hint_end <= len(source_text):
            if source_text[hint_start:hint_end] == value and _span_free(hint_start, hint_end):
                return hint_start, hint_end, value, 0.0  # full confidence

    # ── 2. Exact substring – all occurrences, pick closest to hint ─
    positions = _find_all(source_text, value)
    free = [p for p in positions if _span_free(p, p + vlen)]
    if free:
        best = _closest(free, hint_start) if hint_start is not None else free[0]
        return best, best + vlen, value, 0.0

    # ── 3. Case-insensitive match ─────────────────────────────
    ci_hits = _find_all_casefold(source_text, value)
    ci_free = [(p, actual) for p, actual in ci_hits if _span_free(p, p + len(actual))]
    if ci_free:
        if hint_start is not None:
            best_p, best_actual = min(ci_free, key=lambda x: abs(x[0] - hint_start))
        else:
            best_p, best_actual = ci_free[0]
        return best_p, best_p + len(best_actual), best_actual, -0.05  # slight penalty

    # ── 4. Whitespace-normalised fuzzy match ──────────────────
    ws_hits = _find_fuzzy_ws(source_text, value)
    ws_free = [(s, e, actual) for s, e, actual in ws_hits if _span_free(s, e)]
    if ws_free:
        if hint_start is not None:
            best_s, best_e, best_actual = min(ws_free, key=lambda x: abs(x[0] - hint_start))
        else:
            best_s, best_e, best_actual = ws_free[0]
        return best_s, best_e, best_actual, -0.10  # larger penalty

    # ── 5. Nothing found ──────────────────────────────────────
    return None


class LLMFilter(Filter):
    """
    Uses a local LLM to detect fuzzy PII (names, companies, addresses).

    This filter calls Ollama directly (never a remote provider).
    """

    name = "llm"
    category = "pii"

    def __init__(
        self,
        provider: str = "ollama",
        model: str = "phi4",
        categories: list[str] | None = None,
        confidence: float = 0.80,
    ) -> None:
        self._provider = provider  # kept for forward compat, but forced to local
        self._model = model
        self._categories = categories or ["person_name", "company_name", "address"]
        self._confidence = confidence

    @property
    def _placeholder_category(self) -> str:
        return "LLM_ENTITY"

    def scan(self, text: str) -> list[Detection]:
        # Import locally to avoid hard dependency when LLM filter is not used
        try:
            from hybridagents.core.providers.ollama_provider import OllamaProvider
        except ImportError:
            return []

        provider = OllamaProvider()
        system = _SYSTEM_PROMPT.format(categories=", ".join(self._categories))

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": text},
        ]

        try:
            raw = provider.chat(
                messages=messages,
                model=self._model,
                temperature=0.0,
                json_mode=True,
            )
        except Exception:
            return []  # fail open – don't block the pipeline

        return self._parse_response(raw, text)

    def _parse_response(self, raw: str, source_text: str) -> list[Detection]:
        """
        Parse the LLM JSON response into Detection objects.

        Strategy: "value is truth, offsets are hints".
        See module docstring for the full resolution logic.
        """
        # ── Extract JSON array from raw response ──────────────
        try:
            entities = json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r"\[.*\]", raw, re.DOTALL)
            if match:
                try:
                    entities = json.loads(match.group(0))
                except json.JSONDecodeError:
                    log.debug("LLMFilter: could not parse JSON from response")
                    return []
            else:
                log.debug("LLMFilter: no JSON array found in response")
                return []

        if not isinstance(entities, list):
            log.debug("LLMFilter: response is not a JSON array")
            return []

        # ── Resolve each entity ───────────────────────────────
        detections: list[Detection] = []
        consumed: set[tuple[int, int]] = set()

        for ent in entities:
            if not isinstance(ent, dict):
                continue

            value = ent.get("value", "")
            ent_type = ent.get("type", "unknown")
            if not value:
                continue

            # Safely coerce offsets (handles str/"10", float, None, …)
            hint_start = _safe_int(ent.get("start"))
            hint_end = _safe_int(ent.get("end"))

            resolved = _resolve_offset(
                source_text, value, hint_start, hint_end, consumed,
            )

            if resolved is None:
                log.debug(
                    "LLMFilter: could not locate %r (type=%s) in text – dropped",
                    value, ent_type,
                )
                continue

            start, end, matched_value, conf_modifier = resolved
            consumed.add((start, end))

            detections.append(
                Detection(
                    filter_name=self.name,
                    category=self.category,
                    start=start,
                    end=end,
                    original=matched_value,
                    confidence=max(0.0, self._confidence + conf_modifier),
                )
            )

        return detections

    def __repr__(self) -> str:
        return f"LLMFilter(model={self._model!r}, categories={self._categories})"
