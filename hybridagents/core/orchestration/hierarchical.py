"""
Hierarchical / Tree Orchestration
Manager → Sub-managers → Workers → results bubble up.
"""

from __future__ import annotations

from typing import Any

from hybridagents.core.orchestration._common import (
    VERBOSE, Agent, chat_completion, parse_json_response, run_agent,
    console, Panel,
)


def hierarchical(
    agents: list[Agent],
    task: str,
    *,
    manager: Agent | None = None,
    max_depth: int = 3,
) -> str:
    """
    Recursive tree delegation.  A *manager* breaks the task into
    sub-tasks and assigns each to a specialist.  Specialists may
    themselves be managers of sub-groups (up to *max_depth*).

    The manager receives all sub-results and synthesizes a final answer.
    """
    if not agents:
        return "[ERROR] No agents provided for hierarchical orchestration."

    mgr = manager or agents[0]
    workers = [a for a in agents if a.name != mgr.name]
    worker_names = [a.name for a in workers]
    worker_map = {a.name: a for a in workers}

    if not workers or max_depth <= 0:
        # Leaf: manager does it alone
        return run_agent(mgr, task)

    # Ask manager to decompose
    decompose_prompt = (
        "You are a manager. Break the following task into sub-tasks and "
        "assign each to a worker.\n\n"
        f"**Task**: {task}\n\n"
        f"Available workers: {worker_names}\n\n"
        'Respond with JSON: {{"subtasks": [{{"task": "...", "agent": "<name>"}}, ...]}}\n'
        "IMPORTANT: Respond ONLY with JSON."
    )

    mgr_kwargs: dict[str, Any] = {"json_mode": True}
    if mgr.provider:
        mgr_kwargs["provider"] = mgr.provider
    if mgr.model:
        mgr_kwargs["model"] = mgr.model
    raw = chat_completion(
        [{"role": "user", "content": decompose_prompt}], **mgr_kwargs
    )
    parsed = parse_json_response(raw)
    subtasks = parsed.get("subtasks", [])

    if VERBOSE:
        console.print(
            Panel(
                f"[bold]Hierarchical[/bold] depth={max_depth} → "
                f"[cyan]{mgr.name}[/cyan] split into {len(subtasks)} subtasks",
                style="yellow",
            )
        )

    if not subtasks:
        return run_agent(mgr, task)

    # Execute subtasks (optionally recursive)
    sub_results: list[dict[str, str]] = []
    for st in subtasks:
        st_task = st.get("task", "")
        st_agent_name = st.get("agent", "")
        worker = worker_map.get(st_agent_name)

        if worker is None:
            worker = workers[0] if workers else mgr

        if VERBOSE:
            console.print(
                f"  [yellow]Subtask → {worker.name}[/yellow]: {st_task[:100]}"
            )

        # Recurse: the worker can itself decompose if depth allows
        result = hierarchical(
            agents=[worker] + [w for w in workers if w.name != worker.name],
            task=st_task,
            manager=worker,
            max_depth=max_depth - 1,
        )
        sub_results.append({"task": st_task, "agent": worker.name, "result": result})

    # Synthesize
    synth_prompt = "You are the manager. Your workers completed these sub-tasks:\n\n"
    for sr in sub_results:
        synth_prompt += (
            f"- **{sr['agent']}** — {sr['task']}\n"
            f"  Result: {sr['result'][:500]}\n\n"
        )
    synth_prompt += f"Original task: {task}\n\nSynthesize a final answer."

    return run_agent(mgr, synth_prompt)
