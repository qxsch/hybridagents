"""
Abstract base class for LLM providers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """
    Every provider must implement a single `chat` method that accepts
    a standard messages list and returns the assistant reply as a string.
    """

    @abstractmethod
    def chat(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float | None = None,
        json_mode: bool = False,
    ) -> str:
        """Send messages to the LLM and return the assistant reply."""
        ...
