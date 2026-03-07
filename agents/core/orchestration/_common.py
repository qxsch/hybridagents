"""Shared imports and utilities for orchestration patterns."""

from __future__ import annotations

import json
import concurrent.futures as _cf
import threading
from typing import Any, Callable

from rich.console import Console
from rich.panel import Panel

from agents.config import VERBOSE, MAX_LOOP_ITERATIONS
from agents.core.agent import Agent
from agents.core.llm import chat_completion, parse_json_response
from agents.core.loop import run_agent

console = Console()

__all__ = [
    "json",
    "_cf",
    "threading",
    "Any",
    "Callable",
    "Console",
    "Panel",
    "VERBOSE",
    "MAX_LOOP_ITERATIONS",
    "Agent",
    "chat_completion",
    "parse_json_response",
    "run_agent",
    "console",
]
