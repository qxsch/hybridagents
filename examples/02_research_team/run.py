"""
02 – Research Team

Shows the classic three-agent setup: orchestrator delegates to
researcher (search/files) and coder (calculator/files).

This is equivalent to what was previously in ``agents_config/``.

Usage:
    python examples/02_research_team/run.py
    python examples/02_research_team/run.py --agent researcher
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import argparse

from agents import Agent, Runtime

# ── Build runtime (default tools auto-loaded) ──────────────
rt = Runtime()

# ── Agents ─────────────────────────────────────────────────

rt.register(
    Agent(
        name="researcher",
        instruction=(
            "You are a meticulous research assistant. "
            "Your job is to find relevant information using your tools, "
            "synthesise it clearly, and present concise answers. "
            "Always cite which tool/source provided the data. "
            "If you cannot find an answer, say so honestly."
        ),
        tool_names=["memory_search", "memory_store", "read_file", "list_dir"],
        handover_agents=[],
        memory_collection="researcher_memory",
    )
)

rt.register(
    Agent(
        name="coder",
        instruction=(
            "You are an expert software engineer. "
            "You write clean, well-documented code. "
            "Use the calculator for math, and file tools for reading/writing code. "
            "Always explain your reasoning before presenting code."
        ),
        tool_names=["calculator", "read_file", "write_file", "list_dir"],
        handover_agents=[],
    )
)

rt.register(
    Agent(
        name="orchestrator",
        instruction=(
            "You are a helpful project orchestrator. "
            "You can answer questions directly if they are simple, "
            "but for research tasks delegate to the 'researcher' agent, "
            "and for coding tasks delegate to the 'coder' agent. "
            "You also have access to memory tools for storing/retrieving context. "
            "When delegating, provide a clear, self-contained task description."
        ),
        tool_names=["memory_search", "memory_store", "calculator"],
        handover_agents=["researcher", "coder"],
    )
)

# ── Entry point ────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Research-team REPL")
    parser.add_argument(
        "--agent",
        default="orchestrator",
        help=f"Agent to talk to. Available: {rt.agents.names()}",
    )
    args = parser.parse_args()

    agent = rt.agents.get(args.agent)
    if agent is None:
        print(f"Unknown agent '{args.agent}'. Available: {rt.agents.names()}")
        sys.exit(1)

    rt.repl(agent)


if __name__ == "__main__":
    main()
