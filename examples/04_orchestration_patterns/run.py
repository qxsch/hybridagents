"""
04 – Orchestration Patterns

Demonstrates several orchestration strategies from the SDK:
  • Sequential  – agents run in a pipeline
  • Debate      – adversarial agents argue, a judge synthesizes
  • Voting      – agents answer independently, judge picks the best

Run it and choose a pattern interactively, or pass --pattern on the CLI.

Usage:
    python examples/04_orchestration_patterns/run.py
    python examples/04_orchestration_patterns/run.py --pattern debate
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import argparse

from hybridagents import Agent, Runtime
from hybridagents.core.orchestration import sequential, debate, voting

from rich.console import Console
from rich.panel import Panel

console = Console()

# ── Build runtime ──────────────────────────────────────────
rt = Runtime()

# ── Agents used across patterns ────────────────────────────

drafter = rt.register(
    Agent(
        name="drafter",
        instruction=(
            "You draft clear, concise text. "
            "When given a topic, produce a well-structured first draft."
        ),
        tool_names=["calculator"],
    )
)

critic = rt.register(
    Agent(
        name="critic",
        instruction=(
            "You are a constructive critic. "
            "Review the text you receive, point out weaknesses, "
            "and suggest concrete improvements."
            "Also include the original text in the beginning of your response, so the editor can easily compare and apply your suggestions."
        ),
    )
)

editor = rt.register(
    Agent(
        name="editor",
        instruction=(
            "You are a professional editor. "
            "Take the draft and critic, then produce a polished final version to what the user asked for. "
            "Don't just apply the critic, use your judgement to decide what to keep. And never quote or mention the critic or drafter (like 'the critic said ...'). "
            "The final version should be a standalone piece that doesn't reference the drafting process at all."
        ),
    )
)

optimist = rt.register(
    Agent(
        name="optimist",
        instruction="You analyse topics with an optimistic, opportunity-focused lens.",
    )
)

pessimist = rt.register(
    Agent(
        name="pessimist",
        instruction="You analyse topics with a cautious, risk-focused lens.",
    )
)

judge = rt.register(
    Agent(
        name="judge",
        instruction=(
            "You are a fair, balanced judge. "
            "Synthesise arguments into a well-rounded conclusion."
        ),
    )
)

# ── Pattern runners ────────────────────────────────────────

PATTERNS = {}


def _pattern(name: str):
    """Decorator to register a pattern runner."""
    def deco(fn):
        PATTERNS[name] = fn
        return fn
    return deco


@_pattern("sequential")
def run_sequential(task: str) -> str:
    """Draft → Critique → Edit pipeline."""
    console.print("[bold blue]Running sequential:[/bold blue] drafter → critic → editor\n")
    return sequential([drafter, critic, editor], task)


@_pattern("debate")
def run_debate(task: str) -> str:
    """Optimist vs pessimist, judge synthesizes."""
    console.print("[bold magenta]Running debate:[/bold magenta] optimist vs pessimist (judge decides)\n")
    return debate([optimist, pessimist], task, judge=judge, max_rounds=2)


@_pattern("voting")
def run_voting(task: str) -> str:
    """All agents vote independently, judge picks best."""
    voters = [drafter, optimist, pessimist]
    console.print(f"[bold cyan]Running voting:[/bold cyan] {[a.name for a in voters]} → judge\n")
    return voting(voters, task, judge=judge)


# ── Interactive loop ───────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Orchestration-pattern demo")
    parser.add_argument(
        "--pattern",
        choices=list(PATTERNS.keys()),
        default=None,
        help="Run a specific pattern (default: choose interactively)",
    )
    args = parser.parse_args()

    pattern_names = list(PATTERNS.keys())
    console.print(
        Panel(
            "[bold green]Orchestration Patterns Demo[/bold green]\n\n"
            f"Available patterns: {', '.join(pattern_names)}\n"
            "Type [bold]quit[/bold] to leave.",
            title="04 – Orchestration Patterns",
        )
    )

    with rt:  # activate runtime context for orchestration helpers
        while True:
            # Pick pattern
            if args.pattern:
                choice = args.pattern
                args.pattern = None  # only use CLI arg the first time
            else:
                choice = console.input(
                    f"[bold yellow]Pattern ({'/'.join(pattern_names)}) › [/bold yellow]"
                ).strip().lower()

            if choice in ("quit", "exit", "q"):
                break
            if choice not in PATTERNS:
                console.print(f"[red]Unknown pattern '{choice}'. Choose from: {pattern_names}[/red]")
                continue

            task = console.input("[bold yellow]Task › [/bold yellow]").strip()
            if not task:
                continue

            result = PATTERNS[choice](task)
            console.print(Panel(result, title="Result", style="green"))


if __name__ == "__main__":
    main()
