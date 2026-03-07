"""
Supervisor / Monitor Orchestration
Agents run; supervisor watches and can veto/redirect.
"""

from __future__ import annotations

from hybridagents.core.orchestration._common import (
    VERBOSE, Agent, run_agent, console, Panel,
)


def supervisor(
    agents: list[Agent],
    task: str,
    *,
    monitor: Agent | None = None,
    max_rounds: int = 10,
) -> str:
    """
    Each round a *monitor* agent reviews the latest agent output and
    decides: ``APPROVE`` (accept), ``REDIRECT <agent_name>`` (re-route),
    or ``OVERRIDE <new_instruction>`` (force a correction).

    This pattern is ideal for safety-critical or compliance workflows.
    """
    if not agents:
        return "[ERROR] No agents provided for supervisor."

    sup = monitor or agents[0]
    agent_map = {a.name: a for a in agents}
    agent_names = [a.name for a in agents]

    current_agent = agents[0]
    current_task = task
    last_result = ""

    for round_num in range(1, max_rounds + 1):
        if VERBOSE:
            console.print(
                Panel(
                    f"[bold]Supervisor[/bold] round {round_num}/{max_rounds} → "
                    f"[cyan]{current_agent.name}[/cyan]",
                    style="red",
                )
            )

        # Agent executes
        last_result = run_agent(current_agent, current_task)

        if VERBOSE:
            console.print(f"  [blue]{current_agent.name}[/blue]: {last_result[:120]}")

        # Supervisor reviews
        review_prompt = (
            "You are a supervisor monitoring agent outputs. "
            "Review the output below and decide:\n"
            "- 'APPROVE' if the answer is correct, safe, and complete.\n"
            f"- 'REDIRECT <agent_name>' to re-route to another agent ({agent_names}).\n"
            "- 'OVERRIDE <instruction>' to ask the agent to redo with new guidance.\n\n"
            f"**Task**: {task}\n"
            f"**Agent**: {current_agent.name}\n"
            f"**Output**: {last_result}\n\n"
            "Respond with one of: APPROVE / REDIRECT <name> / OVERRIDE <instruction>"
        )
        verdict = run_agent(sup, review_prompt).strip()

        if VERBOSE:
            console.print(f"  [yellow]Supervisor[/yellow]: {verdict[:120]}")

        upper_verdict = verdict.upper()
        if upper_verdict.startswith("APPROVE"):
            return last_result
        elif upper_verdict.startswith("REDIRECT"):
            parts = verdict.split(maxsplit=1)
            target_name = parts[1].strip() if len(parts) > 1 else ""
            next_agent = agent_map.get(target_name)
            if next_agent:
                current_agent = next_agent
            else:
                if VERBOSE:
                    console.print(
                        f"  [red]Unknown redirect target '{target_name}', "
                        f"keeping {current_agent.name}[/red]"
                    )
        elif upper_verdict.startswith("OVERRIDE"):
            parts = verdict.split(maxsplit=1)
            override_instruction = parts[1].strip() if len(parts) > 1 else task
            current_task = (
                f"Original task: {task}\n\n"
                f"Supervisor override: {override_instruction}\n\n"
                f"Your previous answer was: {last_result}\n\n"
                "Please redo your answer following the supervisor's guidance."
            )
        else:
            # Ambiguous — treat as approve
            return last_result

    return last_result
