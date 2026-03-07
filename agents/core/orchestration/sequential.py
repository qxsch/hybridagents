"""
Sequential Orchestration
Task → Agent A → Agent B → Agent C → Final Output
"""

from __future__ import annotations

from typing import Callable

from agents.core.orchestration._common import (
    VERBOSE, Agent, run_agent, console, Panel,
)


def sequential(
    agents: list[Agent],
    task: str,
    *,
    input_transform: Callable[[str], str] | None = None,
    output_transform: Callable[[str], str] | None = None,
) -> str:
    """
    Run *agents* one after another.  Each agent receives the previous
    agent's output as its input.  The first agent receives *task*.

    Optional transforms can pre-/post-process the data flowing through
    the pipeline.
    """
    if not agents:
        return "[ERROR] No agents provided for sequential orchestration."

    current_input = input_transform(task) if input_transform else task

    for i, agent in enumerate(agents, 1):
        if VERBOSE:
            console.print(
                Panel(
                    f"[bold]Sequential[/bold] step {i}/{len(agents)} → "
                    f"[cyan]{agent.name}[/cyan]",
                    style="blue",
                )
            )
        current_input = run_agent(agent, current_input)

    result = output_transform(current_input) if output_transform else current_input
    return result
