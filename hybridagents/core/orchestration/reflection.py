"""
Reflection / Critic Orchestration
Producer → Critic → Producer → Critic → … until quality bar.
"""

from __future__ import annotations

from typing import Callable

from hybridagents.core.orchestration._common import (
    VERBOSE, Agent, run_agent, console, Panel,
)


def reflection(
    producer: Agent,
    critic: Agent,
    task: str,
    *,
    max_rounds: int = 3,
    quality_check: Callable[[str, str], bool] | None = None,
) -> str:
    """
    *producer* generates output, *critic* reviews it and suggests
    improvements.  The loop continues until *quality_check(draft, feedback)*
    returns ``True``, the critic says "APPROVED", or *max_rounds* is
    exhausted.

    Default quality gate: critic response contains the word "APPROVED".
    """
    draft = ""
    feedback = ""

    for round_num in range(1, max_rounds + 1):
        if VERBOSE:
            console.print(
                Panel(
                    f"[bold]Reflection[/bold] round {round_num}/{max_rounds}",
                    style="cyan",
                )
            )

        # Producer creates / revises
        if round_num == 1:
            producer_prompt = task
        else:
            producer_prompt = (
                f"Original task: {task}\n\n"
                f"Your previous draft:\n{draft}\n\n"
                f"Critic feedback:\n{feedback}\n\n"
                "Revise your draft to address the feedback."
            )
        draft = run_agent(producer, producer_prompt)

        if VERBOSE:
            console.print(f"  [blue]Producer draft[/blue]: {draft[:150]}")

        # Critic reviews
        critic_prompt = (
            f"Original task: {task}\n\n"
            f"Draft to review:\n{draft}\n\n"
            "Provide specific, actionable feedback. "
            "If the draft is excellent and needs no changes, respond with exactly 'APPROVED'."
        )
        feedback = run_agent(critic, critic_prompt)

        if VERBOSE:
            console.print(f"  [yellow]Critic feedback[/yellow]: {feedback[:150]}")

        # Quality gate
        if quality_check and quality_check(draft, feedback):
            break
        if "APPROVED" in feedback.upper():
            break

    return draft
