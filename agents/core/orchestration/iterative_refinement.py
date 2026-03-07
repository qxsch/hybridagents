"""
Iterative Refinement Orchestration
Single agent: draft → self-critique → revise → repeat.
"""

from __future__ import annotations

from typing import Callable

from agents.core.orchestration._common import (
    VERBOSE, Agent, run_agent, console, Panel,
)


def iterative_refinement(
    agent: Agent,
    task: str,
    *,
    max_rounds: int = 3,
    quality_check: Callable[[str], bool] | None = None,
) -> str:
    """
    A single *agent* drafts an answer, then self-critiques and revises
    in a loop.  Cheaper than reflection (no second agent needed).

    Stops when *quality_check(draft)* returns True, the agent says
    "FINAL", or *max_rounds* is exhausted.
    """
    draft = ""

    for round_num in range(1, max_rounds + 1):
        if VERBOSE:
            console.print(
                Panel(
                    f"[bold]Iterative Refinement[/bold] round {round_num}/{max_rounds}"
                    f" → [cyan]{agent.name}[/cyan]",
                    style="cyan",
                )
            )

        if round_num == 1:
            prompt = task
        else:
            prompt = (
                f"Original task: {task}\n\n"
                f"Your previous draft:\n{draft}\n\n"
                "Critically review your draft — identify weaknesses, inaccuracies, "
                "or missing details. Then produce an improved version.\n"
                "If your draft is already excellent, start your response with 'FINAL:' "
                "followed by the final version."
            )

        draft = run_agent(agent, prompt)

        if VERBOSE:
            console.print(f"  [cyan]Draft[/cyan]: {draft[:150]}")

        if draft.upper().startswith("FINAL:"):
            draft = draft[6:].strip()
            break

        if quality_check and quality_check(draft):
            break

    return draft
