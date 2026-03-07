"""
Router Orchestration
Classifier inspects task → routes to exactly one specialist.
"""

from __future__ import annotations

from typing import Any

from agents.core.orchestration._common import (
    VERBOSE, Agent, chat_completion, parse_json_response, run_agent,
    console, Panel,
)


def router(
    agents: list[Agent],
    task: str,
    *,
    classifier: Agent | None = None,
) -> str:
    """
    A *classifier* agent inspects *task* and picks the single best
    specialist from *agents*.  The chosen specialist then handles the
    task.

    If no *classifier* is provided the first agent acts as the router.
    """
    if not agents:
        return "[ERROR] No agents provided for router."

    clf = classifier or agents[0]
    agent_map = {a.name: a for a in agents}
    agent_descriptions = [
        f"- **{a.name}**: {a.instruction[:120]}" for a in agents
    ]

    route_prompt = (
        "You are a task router. Given the task below, pick the single best "
        "agent to handle it.\n\n"
        f"**Task**: {task}\n\n"
        "Available agents:\n" + "\n".join(agent_descriptions) + "\n\n"
        'Respond with JSON: {"agent": "<name>", "reason": "<why>"}\n'
        "IMPORTANT: Respond ONLY with JSON."
    )

    clf_kwargs: dict[str, Any] = {"json_mode": True}
    if clf.provider:
        clf_kwargs["provider"] = clf.provider
    if clf.model:
        clf_kwargs["model"] = clf.model
    raw = chat_completion(
        [{"role": "user", "content": route_prompt}], **clf_kwargs
    )
    parsed = parse_json_response(raw)
    chosen_name = parsed.get("agent", "")

    if VERBOSE:
        console.print(
            Panel(
                f"[bold]Router[/bold] → [cyan]{chosen_name}[/cyan]: "
                f"{parsed.get('reason', '')[:100]}",
                style="blue",
            )
        )

    chosen = agent_map.get(chosen_name)
    if chosen is None:
        # Fallback: use the first agent
        if VERBOSE:
            console.print(
                f"  [red]Unknown agent '{chosen_name}', "
                f"falling back to {agents[0].name}[/red]"
            )
        chosen = agents[0]

    return run_agent(chosen, task)
