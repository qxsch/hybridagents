"""
Debate / Adversarial Orchestration
Pro → Con → Pro → Con → … → Judge synthesizes.
"""

from __future__ import annotations

from hybridagents.core.orchestration._common import (
    VERBOSE, Agent, run_agent, console, Panel,
)


def debate(
    agents: list[Agent],
    task: str,
    *,
    judge: Agent | None = None,
    max_rounds: int = 3,
) -> str:
    """
    Two or more agents argue opposing positions on *task*.

    Each round, every agent sees the full debate transcript and adds its
    rebuttal.  After *max_rounds* the *judge* (default: first agent)
    synthesizes a final, balanced answer.
    """
    if len(agents) < 2:
        return "[ERROR] Debate requires at least 2 agents."

    judge_agent = judge or agents[0]
    roles = {a.name: f"Position {i+1}" for i, a in enumerate(agents)}

    transcript: list[str] = [f"**Topic**: {task}\n"]

    for round_num in range(1, max_rounds + 1):
        if VERBOSE:
            console.print(
                Panel(
                    f"[bold]Debate[/bold] round {round_num}/{max_rounds}",
                    style="magenta",
                )
            )
        for agent in agents:
            prompt = (
                f"You are debating the following topic. "
                f"Your role is '{roles[agent.name]}'. "
                f"Argue your position convincingly.\n\n"
                + "\n".join(transcript)
                + "\n\nProvide your argument for this round."
            )
            reply = run_agent(agent, prompt)
            transcript.append(f"**[{agent.name} – {roles[agent.name]}]**: {reply}")

            if VERBOSE:
                console.print(
                    f"  [{agent.name}] {reply[:120]}"
                )

    # Judge synthesizes
    judge_prompt = (
        "You are the judge of a structured debate. "
        "Read the full transcript below and produce a balanced, final answer "
        "that incorporates the strongest arguments from each side.\n\n"
        + "\n".join(transcript)
        + "\n\nProvide your final ruling."
    )
    if VERBOSE:
        console.print(
            Panel(
                f"[bold]Debate[/bold] → Judge [cyan]{judge_agent.name}[/cyan] ruling",
                style="green",
            )
        )
    return run_agent(judge_agent, judge_prompt)
