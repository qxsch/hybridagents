"""
Voting / Ensemble Orchestration
All agents answer independently → tally / pick consensus.
"""

from __future__ import annotations

from hybridagents.core.orchestration._common import (
    _cf, VERBOSE, Agent, run_agent, console, Panel,
)


def voting(
    agents: list[Agent],
    task: str,
    *,
    judge: Agent | None = None,
    max_workers: int | None = None,
) -> str:
    """
    Every agent independently answers *task* (in parallel).  A *judge*
    agent then reviews all answers and selects or merges the best one.

    If no *judge* is given the first agent is used as the tie-breaker.
    """
    if not agents:
        return "[ERROR] No agents provided for voting."

    judge_agent = judge or agents[0]

    # Collect independent answers
    def _vote(agent: Agent) -> tuple[str, str]:
        return agent.name, run_agent(agent, task)

    ballots: list[tuple[str, str]] = []
    with _cf.ThreadPoolExecutor(max_workers=max_workers or len(agents)) as pool:
        futures = {pool.submit(_vote, a): a for a in agents}
        for f in _cf.as_completed(futures):
            ballots.append(f.result())

    # Preserve order
    order = {a.name: i for i, a in enumerate(agents)}
    ballots.sort(key=lambda b: order.get(b[0], 0))

    if VERBOSE:
        console.print(
            Panel(
                f"[bold]Voting[/bold] collected {len(ballots)} ballots",
                style="blue",
            )
        )
        for name, ans in ballots:
            console.print(f"  [{name}]: {ans[:100]}")

    # Judge selects / merges
    judge_prompt = (
        "You are the judge in a voting round. Multiple agents have independently "
        "answered the same question. Review their answers and produce the best "
        "possible answer — pick the most accurate one, or merge insights from "
        "several.\n\n"
        f"**Question**: {task}\n\n"
    )
    for name, answer in ballots:
        judge_prompt += f"**{name}**:\n{answer}\n\n"
    judge_prompt += "Provide your final, authoritative answer."

    return run_agent(judge_agent, judge_prompt)
