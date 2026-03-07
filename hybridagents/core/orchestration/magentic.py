"""
Magentic Orchestration
Lead agent plans, then delegates steps to specialists.
"""

from __future__ import annotations

from typing import Any

from hybridagents.core.orchestration._common import (
    VERBOSE, Agent, chat_completion, parse_json_response, run_agent,
    console, Panel,
)


def magentic(
    agents: list[Agent],
    task: str,
    *,
    lead: Agent | None = None,
    max_plan_steps: int = 10,
) -> str:
    """
    A *lead* agent (planner) creates a step-by-step plan, then delegates
    each step to the most suitable specialist agent.  The lead can revise
    the plan based on intermediate results.

    Plan format expected from the lead:
        {"plan": [{"step": "...", "agent": "<name>"}, ...]}
    """
    if not agents:
        return "[ERROR] No agents provided for magentic orchestration."

    planner = lead or agents[0]
    specialists = {a.name: a for a in agents if a.name != planner.name}
    specialist_names = list(specialists.keys())

    # ── Phase 1: ask the lead to create a plan ────────────────
    plan_prompt = (
        f"You are the lead planner. Your job is to create a step-by-step plan "
        f"for the following task, then assign each step to a specialist agent.\n\n"
        f"Task: {task}\n\n"
        f"Available specialist agents: {specialist_names}\n"
        f"(If you need to do a step yourself, use your own name: '{planner.name}')\n\n"
        f"Respond with JSON:\n"
        f'{{"plan": [{{"step": "<description>", "agent": "<agent_name>"}}, ...]}}\n'
        f"Maximum {max_plan_steps} steps. Respond ONLY with JSON."
    )

    if VERBOSE:
        console.print(
            Panel(
                f"[bold]Magentic[/bold] → [cyan]{planner.name}[/cyan] creating plan",
                style="yellow",
            )
        )

    plan_kwargs: dict[str, Any] = {"json_mode": True}
    if planner.provider:
        plan_kwargs["provider"] = planner.provider
    if planner.model:
        plan_kwargs["model"] = planner.model
    plan_raw = chat_completion(
        [{"role": "user", "content": plan_prompt}], **plan_kwargs
    )
    plan_parsed = parse_json_response(plan_raw)
    steps = plan_parsed.get("plan", [])

    if not steps:
        return f"[ERROR] Lead agent produced no plan. Raw: {plan_raw[:300]}"

    if VERBOSE:
        console.print(f"  [yellow]Plan ({len(steps)} steps):[/yellow]")
        for i, s in enumerate(steps, 1):
            console.print(f"    {i}. [{s.get('agent', '?')}] {s.get('step', '?')}")

    # ── Phase 2: execute each step ────────────────────────────
    ledger: list[dict[str, str]] = []  # tracks step → result

    for i, step_info in enumerate(steps[:max_plan_steps], 1):
        step_desc = step_info.get("step", "")
        agent_name = step_info.get("agent", planner.name)
        executor = specialists.get(agent_name) or (
            planner if agent_name == planner.name else None
        )

        if executor is None:
            if VERBOSE:
                console.print(
                    f"  [red]Step {i}: unknown agent '{agent_name}', "
                    f"falling back to lead[/red]"
                )
            executor = planner

        if VERBOSE:
            console.print(
                Panel(
                    f"[bold]Magentic[/bold] step {i}/{len(steps)} → "
                    f"[cyan]{executor.name}[/cyan]: {step_desc[:100]}",
                    style="yellow",
                )
            )

        # Give the executor context of the plan + prior results
        context_lines = [f"Overall task: {task}", ""]
        if ledger:
            context_lines.append("Results from previous steps:")
            for entry in ledger:
                context_lines.append(
                    f"  - Step '{entry['step']}' ({entry['agent']}): "
                    f"{entry['result'][:200]}"
                )
            context_lines.append("")
        context_lines.append(f"Your current step: {step_desc}")
        context_lines.append("Complete this step and provide your result.")

        step_input = "\n".join(context_lines)
        step_result = run_agent(executor, step_input)

        ledger.append({
            "step": step_desc,
            "agent": executor.name,
            "result": step_result,
        })

    # ── Phase 3: ask the lead to synthesize ───────────────────
    synthesis_prompt = (
        f"You are the lead planner. The following steps have been completed:\n\n"
    )
    for entry in ledger:
        synthesis_prompt += (
            f"- Step: {entry['step']}  (by {entry['agent']})\n"
            f"  Result: {entry['result'][:500]}\n\n"
        )
    synthesis_prompt += (
        f"Original task: {task}\n\n"
        "Synthesize all results into a final, coherent answer."
    )

    if VERBOSE:
        console.print(
            Panel(
                f"[bold]Magentic[/bold] → [cyan]{planner.name}[/cyan] synthesizing",
                style="yellow",
            )
        )

    final_answer = run_agent(planner, synthesis_prompt)
    return final_answer
