"""
Auction / Bid Orchestration
Agents bid confidence → highest bidder executes.
"""

from __future__ import annotations

from typing import Any

from agents.core.orchestration._common import (
    _cf, VERBOSE, Agent, chat_completion, parse_json_response, run_agent,
    console, Panel,
)


def auction(
    agents: list[Agent],
    task: str,
    *,
    max_workers: int | None = None,
) -> str:
    """
    Every agent bids a confidence score (0-100) for how well it can
    handle *task*.  The highest bidder executes the task.

    Agents respond with JSON: {"confidence": <int>, "reason": "<why>"}
    """
    if not agents:
        return "[ERROR] No agents provided for auction."

    bid_prompt = (
        "You are being asked to bid on a task. Rate your confidence "
        "(0-100) that you can handle it well.\n\n"
        f"**Task**: {task}\n\n"
        'Respond with JSON: {{"confidence": <0-100>, "reason": "<why>"}}\n'
        "IMPORTANT: Respond ONLY with JSON."
    )

    def _bid(agent: Agent) -> tuple[str, int, str]:
        bid_kwargs: dict[str, Any] = {"json_mode": True}
        if agent.provider:
            bid_kwargs["provider"] = agent.provider
        if agent.model:
            bid_kwargs["model"] = agent.model
        raw = chat_completion(
            [
                {"role": "system", "content": agent.instruction},
                {"role": "user", "content": bid_prompt},
            ],
            **bid_kwargs,
        )
        parsed = parse_json_response(raw)
        confidence = int(parsed.get("confidence", 0))
        reason = parsed.get("reason", "")
        return agent.name, confidence, reason

    bids: list[tuple[str, int, str]] = []
    with _cf.ThreadPoolExecutor(max_workers=max_workers or len(agents)) as pool:
        futures = {pool.submit(_bid, a): a for a in agents}
        for f in _cf.as_completed(futures):
            try:
                bids.append(f.result())
            except Exception:
                pass  # Agent failed to bid; skip

    if not bids:
        return "[ERROR] No valid bids received."

    bids.sort(key=lambda b: b[1], reverse=True)

    if VERBOSE:
        console.print(
            Panel("[bold]Auction[/bold] bids received", style="blue")
        )
        for name, conf, reason in bids:
            console.print(f"  {name}: {conf}/100 — {reason[:80]}")

    winner_name = bids[0][0]
    winner = next(a for a in agents if a.name == winner_name)

    if VERBOSE:
        console.print(
            f"  [green]Winner → {winner_name} ({bids[0][1]}/100)[/green]"
        )

    return run_agent(winner, task)
