"""
06 – Deterministic Agents

Shows how to create ``DeterministicAgent`` subclasses — agents that
run pure-Python logic instead of calling an LLM.  They integrate
seamlessly with ``run_agent()``, ``Runtime.run()``, the REPL, and
all orchestration patterns.

This example demonstrates:
  • A deterministic **input validator** that cleans & checks messages
  • A deterministic **language router** that delegates to the right agent
  • Handover from deterministic → LLM agent (and vice-versa)

Usage:
    python examples/06_deterministic/run.py
"""

import sys
from pathlib import Path

# ── Make SDK importable ────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from hybridagents import (
    Agent,
    AgentResponse,
    DeterministicAgent,
    HandoverRequest,
    Runtime,
)


# ── Deterministic agents ───────────────────────────────────


class InputValidator(DeterministicAgent):
    """Cleans and validates user input, then delegates to a researcher."""

    def execute(self, message, conversation=None, context=None):
        cleaned = message.strip()
        if len(cleaned) < 3:
            return AgentResponse(
                answer="Please provide a longer message (at least 3 characters)."
            )
        if cleaned.startswith("/"):
            return AgentResponse(
                answer=f"Unknown command: {cleaned.split()[0]}"
            )
        # Everything ok → hand over to the researcher
        return HandoverRequest(agent_name="researcher", task=cleaned)


class KeywordRouter(DeterministicAgent):
    """Routes messages to specialist agents based on keywords."""

    ROUTES = {
        "math": "calculator_agent",
        "calculate": "calculator_agent",
        "compute": "calculator_agent",
        "search": "researcher",
        "find": "researcher",
        "look up": "researcher",
    }

    def execute(self, message, conversation=None, context=None):
        lower = message.lower()
        for keyword, agent_name in self.ROUTES.items():
            if keyword in lower:
                return HandoverRequest(agent_name=agent_name, task=message)
        # Default: answer directly
        return AgentResponse(
            answer=f"I couldn't route your message to a specialist. You said: {message}",
            metadata={"routed": False},
        )


# ── Build runtime ──────────────────────────────────────────

rt = Runtime()

# Deterministic agents
rt.register(
    InputValidator(
        name="validator",
        instruction="Validates and cleans user input before forwarding.",
        handover_agents=["researcher"],
    )
)

rt.register(
    KeywordRouter(
        name="router",
        instruction="Routes messages to the right specialist based on keywords.",
        handover_agents=["calculator_agent", "researcher"],
    )
)

# LLM agents (targets for handovers)
rt.register(
    Agent(
        name="researcher",
        instruction=(
            "You are a research assistant. Answer questions thoroughly "
            "and cite your reasoning."
        ),
        tool_names=["search"],
    )
)

rt.register(
    Agent(
        name="calculator_agent",
        instruction=(
            "You are a math assistant. Use the calculator tool to "
            "evaluate expressions and explain results clearly."
        ),
        tool_names=["calculator"],
    )
)

if __name__ == "__main__":
    # Quick demo: run the validator directly
    print("=== Direct run through validator ===")
    result = rt.run("validator", "  Tell me about quantum computing in 3 bullet points.only")
    print(f"Result: {result}\n")

    print("=== Keyword router ===")
    result = rt.run("router", "calculate 2 + 2")
    print(f"Result: {result}\n")

    print("=== Starting REPL with the router ===")
    rt.repl("router")
