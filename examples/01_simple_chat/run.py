"""
01 – Simple Chat

Minimal example: one agent, no tools, no delegation.
Just a conversational agent you can talk to via the REPL.

Usage:
    python examples/01_simple_chat/run.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from hybridagents import Agent, Runtime

# ── Create a runtime and register one agent ────────────────
rt = Runtime()

rt.register(
    Agent(
        name="assistant",
        instruction=(
            "You are a friendly, helpful assistant. "
            "Answer questions clearly and concisely. "
            "You have no tools — just your knowledge."
        ),
    )
)

if __name__ == "__main__":
    rt.repl("assistant")
