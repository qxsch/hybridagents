"""
Handoff Orchestration
Agents transfer control to each other based on context.
"""

from __future__ import annotations

from agents.core.orchestration._common import (
    VERBOSE, Agent, run_agent, console, Panel,
)


def handoff(
    agents: list[Agent],
    task: str,
    *,
    entry_agent: Agent | None = None,
    max_handoffs: int = 10,
) -> str:
    """
    Start with *entry_agent* (default: first in list).  Each agent can
    either return a final answer or hand off to another agent with a new
    sub-task.  The chain continues until a final answer or *max_handoffs*.

    Agents decide to handoff via the existing ReAct loop's "handover"
    action.  This helper just enforces the boundary and tracks the trail.
    """
    if not agents:
        return "[ERROR] No agents provided for handoff orchestration."

    agent_map = {a.name: a for a in agents}
    current = entry_agent or agents[0]

    # Ensure every agent in the pool knows about the others
    peer_names = [a.name for a in agents]

    trail: list[str] = []
    current_task = task

    for step in range(1, max_handoffs + 1):
        if VERBOSE:
            console.print(
                Panel(
                    f"[bold]Handoff[/bold] step {step} → [cyan]{current.name}[/cyan]",
                    style="red",
                )
            )

        trail.append(current.name)

        # Temporarily allow this agent to handover to all peers
        original_handover = current.handover_agents
        current.handover_agents = [n for n in peer_names if n != current.name]

        result = run_agent(current, current_task)

        # Restore
        current.handover_agents = original_handover

        # Check if the result is a handoff marker (set by loop.py)
        # If run_agent returned normally, it's a final answer
        if VERBOSE:
            console.print(f"  [green]{current.name} answered[/green]: {result[:150]}")

        return result  # run_agent already handles internal handovers

    return f"[WARNING] Handoff chain reached limit ({max_handoffs}). Last agent: {trail[-1]}"
