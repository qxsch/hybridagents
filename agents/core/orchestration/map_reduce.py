"""
Map-Reduce Orchestration
Splitter → parallel agent runs → Reducer merges.
"""

from __future__ import annotations

from typing import Any, Callable

from agents.core.orchestration._common import (
    _cf, VERBOSE, Agent, chat_completion, parse_json_response, run_agent,
    console, Panel,
)


def map_reduce(
    agents: list[Agent],
    task: str,
    *,
    splitter: Callable[[str], list[str]] | None = None,
    reducer: Agent | None = None,
    max_workers: int | None = None,
) -> str:
    """
    *splitter* breaks *task* into N chunks (default: one chunk per agent
    by asking the first agent to split).  Each agent processes one chunk
    in parallel.  *reducer* (default: first agent) merges all results.
    """
    if not agents:
        return "[ERROR] No agents provided for map_reduce."

    reduce_agent = reducer or agents[0]

    # ── Split phase ───────────────────────────────────────────
    if splitter:
        chunks = splitter(task)
    else:
        # Ask the reduce_agent to split
        split_prompt = (
            f"Split the following task into {len(agents)} independent sub-tasks "
            f"that can be processed in parallel.\n\n"
            f"Task: {task}\n\n"
            f'Respond with JSON: {{"chunks": ["sub-task 1", "sub-task 2", ...]}}\n'
            "IMPORTANT: Respond ONLY with JSON."
        )
        split_kwargs: dict[str, Any] = {"json_mode": True}
        if reduce_agent.provider:
            split_kwargs["provider"] = reduce_agent.provider
        if reduce_agent.model:
            split_kwargs["model"] = reduce_agent.model
        split_raw = chat_completion(
            [{"role": "user", "content": split_prompt}], **split_kwargs
        )
        split_parsed = parse_json_response(split_raw)
        chunks = split_parsed.get("chunks", [task])

    if VERBOSE:
        console.print(
            Panel(
                f"[bold]Map-Reduce[/bold] split into {len(chunks)} chunks",
                style="blue",
            )
        )

    # ── Map phase (parallel) ──────────────────────────────────
    assignments = list(zip(agents * ((len(chunks) // len(agents)) + 1), chunks))
    assignments = assignments[: len(chunks)]

    def _map(pair: tuple[Agent, str]) -> tuple[str, str, str]:
        agent, chunk = pair
        result = run_agent(agent, chunk)
        return agent.name, chunk, result

    map_results: list[tuple[str, str, str]] = []
    with _cf.ThreadPoolExecutor(max_workers=max_workers or len(chunks)) as pool:
        futures = [pool.submit(_map, pair) for pair in assignments]
        for f in _cf.as_completed(futures):
            map_results.append(f.result())

    if VERBOSE:
        for name, chunk, result in map_results:
            console.print(f"  [blue]{name}[/blue] → {chunk[:60]} → {result[:80]}")

    # ── Reduce phase ──────────────────────────────────────────
    reduce_prompt = (
        "You are the reducer. Merge the following partial results into a single, "
        "coherent answer.\n\n"
        f"**Original task**: {task}\n\n"
    )
    for name, chunk, result in map_results:
        reduce_prompt += f"**Chunk** ({name}): {chunk}\n**Result**: {result}\n\n"
    reduce_prompt += "Provide the merged final answer."

    return run_agent(reduce_agent, reduce_prompt)
