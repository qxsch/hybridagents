"""
Concurrent Orchestration
Task → [Agent A, Agent B, Agent C] → Aggregate → Output
"""

from __future__ import annotations

from typing import Callable

from hybridagents.core.orchestration._common import (
    _cf, VERBOSE, Agent, run_agent, console, Panel,
)


def concurrent(
    agents: list[Agent],
    task: str,
    *,
    aggregate: Callable[[list[str]], str] | None = None,
    max_workers: int | None = None,
) -> str:
    """
    Broadcast *task* to all *agents* in parallel.  Collect every result,
    then merge with *aggregate* (default: numbered list).

    Uses threads – safe because each agent call is I/O-bound (LLM API).
    """
    if not agents:
        return "[ERROR] No agents provided for concurrent orchestration."

    if VERBOSE:
        names = [a.name for a in agents]
        console.print(
            Panel(
                f"[bold]Concurrent[/bold] → broadcasting to {names}",
                style="blue",
            )
        )

    def _run(agent: Agent) -> tuple[str, str]:
        result = run_agent(agent, task)
        return agent.name, result

    results: list[tuple[str, str]] = []
    with _cf.ThreadPoolExecutor(
        max_workers=max_workers or len(agents)
    ) as pool:
        futures = {pool.submit(_run, a): a for a in agents}
        for future in _cf.as_completed(futures):
            results.append(future.result())

    # Preserve original agent order
    order = {a.name: idx for idx, a in enumerate(agents)}
    results.sort(key=lambda r: order.get(r[0], 0))

    if aggregate:
        return aggregate([r for _, r in results])

    # Default: numbered summary
    parts = [f"## {name}\n{text}" for name, text in results]
    return "\n\n".join(parts)
