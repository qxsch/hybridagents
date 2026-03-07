"""
Group Chat Orchestration
Agents converse in a shared chat; a manager picks next speaker.
"""

from __future__ import annotations

from typing import Any

from hybridagents.core.orchestration._common import (
    VERBOSE, Agent, chat_completion, parse_json_response, run_agent,
    console, Panel,
)


def group_chat(
    agents: list[Agent],
    task: str,
    *,
    manager: Agent | None = None,
    max_rounds: int = 10,
) -> str:
    """
    Multi-agent group conversation.

    A *manager* agent (can be one of the participants or a separate agent)
    decides which agent speaks next.  The conversation continues until the
    manager says "DONE" or *max_rounds* is reached.

    If no *manager* is provided, the first agent in the list acts as manager.
    """
    if not agents:
        return "[ERROR] No agents provided for group chat."

    mgr = manager or agents[0]
    agent_map = {a.name: a for a in agents}
    agent_names = [a.name for a in agents]

    # Shared conversation visible to everyone
    shared_messages: list[dict[str, str]] = [
        {"role": "user", "content": task},
    ]

    manager_instruction = (
        f"You are the manager of a group chat between these agents: {agent_names}.\n"
        f"The task is: {task}\n\n"
        "After each agent speaks, decide who should speak next.\n"
        "Respond with JSON: {\"next_agent\": \"<name>\", \"reason\": \"<why>\"}\n"
        "When the task is fully answered, respond with: {\"next_agent\": \"DONE\", \"final_answer\": \"<summary>\"}\n"
        "IMPORTANT: Respond ONLY with JSON."
    )

    last_answer = ""

    for round_num in range(1, max_rounds + 1):
        if VERBOSE:
            console.print(
                Panel(
                    f"[bold]Group Chat[/bold] round {round_num}/{max_rounds}",
                    style="magenta",
                )
            )

        # Ask manager who speaks next
        mgr_messages = [
            {"role": "system", "content": manager_instruction},
            *shared_messages,
        ]
        mgr_kwargs: dict[str, Any] = {"json_mode": True}
        if mgr.provider:
            mgr_kwargs["provider"] = mgr.provider
        if mgr.model:
            mgr_kwargs["model"] = mgr.model
        mgr_raw = chat_completion(mgr_messages, **mgr_kwargs)
        mgr_parsed = parse_json_response(mgr_raw)
        next_name = mgr_parsed.get("next_agent", "")

        if next_name == "DONE":
            last_answer = mgr_parsed.get("final_answer", last_answer)
            if VERBOSE:
                console.print(f"  [green]Manager → DONE[/green]")
            break

        next_agent = agent_map.get(next_name)
        if next_agent is None:
            if VERBOSE:
                console.print(
                    f"  [red]Manager picked unknown agent '{next_name}', "
                    f"available: {agent_names}[/red]"
                )
            shared_messages.append({
                "role": "user",
                "content": f"[System] Agent '{next_name}' not found. Choose from {agent_names}.",
            })
            continue

        if VERBOSE:
            console.print(
                f"  [yellow]Manager → {next_name}[/yellow]: "
                f"{mgr_parsed.get('reason', '')[:100]}"
            )

        # Run the selected agent with the shared conversation so far
        agent_input = (
            f"You are participating in a group chat. The conversation so far:\n\n"
            + "\n".join(
                f"[{m['role']}]: {m['content'][:200]}" for m in shared_messages
            )
            + "\n\nIt is your turn. Provide your contribution."
        )
        agent_reply = run_agent(next_agent, agent_input)
        last_answer = agent_reply

        shared_messages.append({
            "role": "assistant",
            "content": f"[{next_name}]: {agent_reply}",
        })

    return last_answer
