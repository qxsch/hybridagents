"""
Reusable interactive REPL for any agent.

Usage from an example script::

    from hybridagents import Agent, Runtime

    rt = Runtime()
    rt.register(Agent(name="assistant", instruction="..."))
    rt.repl("assistant")

(Also works with the module-level helper: ``run_repl(agent)``)
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from rich.console import Console
from rich.panel import Panel

from hybridagents.core.loop import run_agent

if TYPE_CHECKING:
    from hybridagents.core.agent import Agent
    from hybridagents.core.deterministic_agent import DeterministicAgent

console = Console()


def _with_max_iterations(agent: "Agent | DeterministicAgent", value: int) -> "Agent | DeterministicAgent":
    """Return a copy of *agent* with *max_iterations* set."""
    import dataclasses
    if dataclasses.is_dataclass(agent):
        return dataclasses.replace(agent, max_iterations=value)
    # DeterministicAgent is not a dataclass – set directly.
    agent.max_iterations = value
    return agent


def _ensure_runtime_active() -> None:
    """If no Runtime is active, auto-activate a default one.

    This lets the legacy ``run_repl(agent)`` call path work without
    requiring the caller to create a ``Runtime`` manually.
    """
    from hybridagents.core.runtime import current_runtime, Runtime
    if current_runtime() is None:
        rt = Runtime(load_defaults=True)
        rt.activate()  # stays active for the remainder of the process


def run_repl(agent: "Agent | DeterministicAgent", *, max_iterations: int | None = None) -> None:
    """Start an interactive REPL talking to *agent*.

    Parameters
    ----------
    agent:
        The agent to converse with.
    max_iterations:
        Per-turn iteration limit.  Overrides the agent's own
        ``max_iterations`` and the global ``MAX_LOOP_ITERATIONS``
        env-var for the duration of this REPL session.
    """
    if max_iterations is not None:
        agent = _with_max_iterations(agent, max_iterations)

    _ensure_runtime_active()

    console.print(
        Panel(
            f"[bold green]Agentic REPL[/bold green]  ·  agent: [cyan]{agent.name}[/cyan]\n"
            f"Tools: {agent.tool_names or '(none)'}\n"
            f"Can delegate to: {agent.handover_agents or '(none)'}\n\n"
            "Type [bold]quit[/bold] or [bold]exit[/bold] to leave.",
            title="Welcome",
        )
    )

    conversation: list[dict[str, str]] = []

    while True:
        try:
            user_input = console.input("[bold yellow]You › [/bold yellow]")
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Bye![/dim]")
            break

        if user_input.strip().lower() in ("quit", "exit", "q"):
            console.print("[dim]Bye![/dim]")
            break

        if not user_input.strip():
            continue

        answer = run_agent(agent, user_input, conversation=conversation)

        # Convert list to string for display (Rich Panel requires a string)
        display_answer = "\n".join(answer) if isinstance(answer, list) else answer

        conversation.append({"role": "user", "content": user_input})
        conversation.append({"role": "assistant", "content": display_answer})

        console.print(Panel(display_answer, title=f"{agent.name}", style="green"))
