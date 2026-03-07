"""
05 – Custom Tools

Shows how to create and register your own tools, then wire them
to an agent.

The tools are defined in ``tools.py`` (same directory). Importing
that module automatically registers them via the @tool decorator.

Usage:
    python examples/05_custom_tools/run.py
"""

import sys
from pathlib import Path

# ── Make SDK + this example dir importable ─────────────────
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from agents import Agent, Runtime

# ── Build runtime, then import custom tools ────────────────
rt = Runtime()

# Import custom tools inside a `with rt:` block so that @tool()
# decorators automatically register into this runtime.
with rt:
    import tools as _custom_tools  # noqa: F401

# ── Agent that uses the custom tools ───────────────────────
rt.register(
    Agent(
        name="helper",
        instruction=(
            "You are a helpful assistant with custom tools. "
            "Use 'current_time' to tell the time, 'dice_roll' for "
            "rolling dice, and 'word_count' to analyse text length. "
            "Always use the right tool for the job."
        ),
        tool_names=["current_time", "dice_roll", "word_count"],
    )
)

if __name__ == "__main__":
    rt.repl("helper")
