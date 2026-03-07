"""
07 – Multiple Runtimes

Demonstrates runtime **isolation** and the ``__enter__`` / ``__exit__``
context-manager protocol.

Two runtimes are created — each with its own agents and tools.
They are completely independent: agents registered in one cannot be
seen by the other.

By design, just one runtime can be active at a time.
This example explains how to switch between runtimes.

This example shows:
  • Creating two isolated runtimes side-by-side
  • Using ``with rt:`` (context manager) to activate a runtime
  • Using ``rt.activate()`` / ``rt.deactivate()`` for manual control
  • Running orchestration patterns inside a specific runtime
  • Proving that registries don't leak between runtimes
  • ``tool(..., runtime=...)`` decorator — register a tool into a specific runtime
  • ``@tool`` inside a ``with rt:`` block — auto-targets the active runtime

Usage:
    python examples/07_multi_runtime/run.py
"""

import sys
from pathlib import Path

# ── Make SDK importable ────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agents import Agent, Runtime
from agents.core.orchestration import sequential
from agents import tool


# ── Helper ─────────────────────────────────────────────────

def separator(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


# ── Runtime A — "research" domain ──────────────────────────

rt_research = Runtime()

researcher: Agent = rt_research.register(
    Agent(
        name="researcher",
        instruction=(
            "You are a research assistant. Summarise topics concisely. "
            "Always mention that you belong to the RESEARCH runtime."
        ),
    )
)

reviewer: Agent = rt_research.register(
    Agent(
        name="reviewer",
        instruction=(
            "You are a critical reviewer. Evaluate the previous text for "
            "accuracy and completeness.  Be brief."
        ),
    )
)


# ── Runtime B — "coding" domain ────────────────────────────

rt_coding = Runtime()

coder: Agent = rt_coding.register(
    Agent(
        name="coder",
        instruction=(
            "You are a Python coding assistant. Write clean, idiomatic code. "
            "Always mention that you belong to the CODING runtime."
        ),
        tool_names=["calculator"],
    )
)

tester: Agent = rt_coding.register(
    Agent(
        name="tester",
        instruction=(
            "You are a test engineer. Review the previous code and suggest "
            "unit tests.  Be brief."
        ),
    )
)


# ── Runtime-scoped tools ───────────────────────────────────

# tool() — registers directly into rt_research
@tool(name="summarize_length", description="Return the word count of a text.", runtime=rt_research)
def summarize_length(text: str) -> str:
    return f"Word count: {len(text.split())}"


# @tool inside a with-block — auto-targets the active runtime
with rt_coding:
    @tool(name="reverse_string", description="Reverse a string.")
    def reverse_string(text: str) -> str:
        return text[::-1]


# ── Demo ───────────────────────────────────────────────────

if __name__ == "__main__":

    # ── 1. Show isolation ──────────────────────────────────
    separator("1. Registry isolation")

    print(f"Research runtime agents : {rt_research.agents.names()}")
    print(f"Coding   runtime agents : {rt_coding.agents.names()}")
    print()
    print("'researcher' visible in research runtime?", rt_research.agents.get("researcher") is not None)
    print("'researcher' visible in coding   runtime?", rt_coding.agents.get("researcher") is not None)
    print("'coder'      visible in coding   runtime?", rt_coding.agents.get("coder") is not None)
    print("'coder'      visible in research runtime?", rt_research.agents.get("coder") is not None)

    # ── 2. Tool isolation ──────────────────────────────────
    separator("2. Tool isolation (rt.tool & context-manager @tool)")

    print(f"Research runtime tools : {rt_research.tools.names()}")
    print(f"Coding   runtime tools : {rt_coding.tools.names()}")
    print()
    print("'summarize_length' in research?", rt_research.tools.get("summarize_length") is not None)
    print("'summarize_length' in coding?  ", rt_coding.tools.get("summarize_length") is not None)
    print("'reverse_string'   in coding?  ", rt_coding.tools.get("reverse_string") is not None)
    print("'reverse_string'   in research?", rt_research.tools.get("reverse_string") is not None)

    # ── 3. Context-manager: with rt: ───────────────────────
    separator("3. Context manager — with rt:")

    print("Running sequential(researcher → reviewer) inside rt_research …")
    with rt_research:
        result = sequential(
            agents=[researcher, reviewer],
            task="Explain the CAP theorem in two sentences.",
        )
    print(f"Result:\n{result}\n")

    print("Running sequential(coder → tester) inside rt_coding …")
    with rt_coding:
        result = sequential(
            agents=[coder, tester],
            task="Write a Python function that checks if a number is prime.",
        )
    print(f"Result:\n{result}\n")

    # ── 4. Manual activate / deactivate ────────────────────
    separator("4. Manual activate / deactivate")

    token = rt_research.activate()
    try:
        result = rt_research.run("researcher", "What is eventual consistency?")
        print(f"Research result:\n{result}\n")
    finally:
        rt_research.deactivate(token)

    token = rt_coding.activate()
    try:
        result = rt_coding.run("coder", "Write a fibonacci generator in Python.")
        print(f"Coding result:\n{result}\n")
    finally:
        rt_coding.deactivate(token)

    # ── 5. Switching between runtimes ──────────────────────
    separator("5. Switching between runtimes")

    print("Research runtime → ask researcher:")
    with rt_research:
        r1 = rt_research.run("researcher", "Briefly: what is CQRS?")
        print(f"  {r1}\n")

    print("Coding runtime → ask coder:")
    with rt_coding:
        r2 = rt_coding.run("coder", "Write a one-liner to flatten a nested list.")
        print(f"  {r2}\n")

    # ── 6. Interactive REPL ────────────────────────────────
    separator("6. Interactive REPL (research runtime)")
    print("Starting REPL with the researcher agent.")
    print("Type 'quit' to exit.\n")
    rt_research.repl("researcher")