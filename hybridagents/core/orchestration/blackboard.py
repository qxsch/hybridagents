"""
Blackboard Orchestration
Shared memory; agents contribute until goal is met.
"""

from __future__ import annotations

from typing import Callable

from hybridagents.core.orchestration._common import (
    threading, VERBOSE, Agent, run_agent, console, Panel,
)


def blackboard(
    agents: list[Agent],
    task: str,
    *,
    max_rounds: int = 10,
    goal_check: Callable[[list[dict[str, str]]], bool] | None = None,
) -> str:
    """
    A shared 'blackboard' (list of entries) is visible to all agents.
    Each round, every agent reads the board and decides whether to
    contribute.  The loop ends when *goal_check* returns True, an agent
    writes ``GOAL_REACHED``, or *max_rounds* is hit.

    Returns the full board as a formatted string.
    """
    if not agents:
        return "[ERROR] No agents provided for blackboard."

    board: list[dict[str, str]] = [{"author": "user", "content": task}]
    lock = threading.Lock()

    def _board_text() -> str:
        return "\n".join(
            f"[{e['author']}]: {e['content']}" for e in board
        )

    for round_num in range(1, max_rounds + 1):
        if VERBOSE:
            console.print(
                Panel(
                    f"[bold]Blackboard[/bold] round {round_num}/{max_rounds} "
                    f"({len(board)} entries)",
                    style="green",
                )
            )

        contributions = 0
        for agent in agents:
            prompt = (
                "You are participating in a blackboard problem-solving session. "
                "Read the board below and add your contribution. "
                "If you have nothing new to add, respond with exactly 'PASS'. "
                "If the task is fully solved, respond with exactly 'GOAL_REACHED'.\n\n"
                f"**Board:**\n{_board_text()}\n\n"
                "Your contribution:"
            )
            reply = run_agent(agent, prompt)

            if "GOAL_REACHED" in reply.upper():
                if VERBOSE:
                    console.print(f"  [green]{agent.name} → GOAL_REACHED[/green]")
                board.append({"author": agent.name, "content": reply})
                return _board_text()

            if reply.strip().upper() != "PASS":
                with lock:
                    board.append({"author": agent.name, "content": reply})
                contributions += 1
                if VERBOSE:
                    console.print(f"  [{agent.name}]: {reply[:100]}")
            else:
                if VERBOSE:
                    console.print(f"  [{agent.name}]: PASS")

        if goal_check and goal_check(board):
            if VERBOSE:
                console.print(f"  [green]Goal check passed[/green]")
            break

        if contributions == 0:
            if VERBOSE:
                console.print(f"  [yellow]No contributions — stopping[/yellow]")
            break

    return _board_text()
