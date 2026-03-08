"""
Agentic loop – ReAct-style (Reason → Act → Observe).

The loop builds a structured prompt that tells the LLM which tools and
handover-agents are available, then parses the LLM's JSON response to
either call a tool, hand over to another agent, or return a final answer.
"""

from __future__ import annotations

import json
from typing import Any

from rich.console import Console
from rich.panel import Panel

from hybridagents.config import MAX_LOOP_ITERATIONS, VERBOSE
from hybridagents.core.agent import Agent
from hybridagents.core.agent_context import current_agent
from hybridagents.core.agent_registry import agents_available_to, get_agent
from hybridagents.core.deterministic_agent import DeterministicAgent
from hybridagents.core.llm import chat_completion, parse_json_response
from hybridagents.core.results import AgentResponse, HandoverRequest
from hybridagents.core.tool_registry import call_tool, get_tools

console = Console()


# ── Prompt construction ────────────────────────────────────────


def _build_system_prompt(agent: Agent) -> str:
    """Build the system prompt including tool/agent descriptions."""
    parts: list[str] = [agent.instruction, ""]

    # Tools
    tools = get_tools(agent.tool_names or None)
    assigned_tools = [t for t in tools if t.name in (agent.tool_names or [])]
    if assigned_tools:
        parts.append("# Available tools")
        for t in assigned_tools:
            params_desc = json.dumps(t.parameters, indent=2)
            parts.append(f"- **{t.name}**: {t.description}\n  Parameters: {params_desc}")
        parts.append("")

    # Handover agents
    handover = agents_available_to(agent)
    if handover:
        parts.append("# Agents you can delegate to")
        for a in handover:
            parts.append(f"- **{a.name}**: {a.instruction[:120]}...")
        parts.append("")

    # Response format instructions
    parts.append(
        "# How to respond\n"
        "Always respond with a JSON object with exactly ONE of these shapes:\n\n"
        '1. To use a tool:\n   {"action": "tool", "tool_name": "<name>", "arguments": {<args>}, "thought": "<reasoning>"}\n\n'
        '2. To delegate to another agent:\n   {"action": "handover", "agent_name": "<name>", "task": "<task description>", "thought": "<reasoning>"}\n\n'
        '3. To give the final answer:\n   {"action": "answer", "answer": "<your answer>", "thought": "<reasoning>"}\n\n'
        "IMPORTANT: Respond ONLY with the JSON object, no extra text."
    )

    return "\n".join(parts)


# ── Single agent turn ─────────────────────────────────────────


# ── Deterministic agent dispatch ──────────────────────────────


def _run_deterministic(
    agent: DeterministicAgent,
    message: str,
    conversation: list[dict[str, str]] | None,
    depth: int,
) -> str:
    """Execute a deterministic agent, handling handovers recursively."""
    if depth > 10:
        return "[ERROR] Maximum handover depth reached."

    result = agent.execute(
        message,
        conversation=conversation,
        context={"depth": depth},
    )

    if isinstance(result, HandoverRequest):
        target = get_agent(result.agent_name)
        if target is None:
            return f"[ERROR] Agent '{result.agent_name}' not found."
        if VERBOSE:
            console.print(
                f"  [red]Handover → {result.agent_name}[/red]: {result.task[:120]}"
            )
        return run_agent(target, result.task, conversation, depth=depth + 1)

    if isinstance(result, AgentResponse):
        if VERBOSE:
            console.print(f"  [green]Answer:[/green] {result.answer[:300]}")
        return result.answer

    # Fallback: if someone returns a plain str (shouldn't, but be lenient)
    return str(result)


# ── Single agent turn ─────────────────────────────────────────


def run_agent(
    agent: Agent | DeterministicAgent,
    user_message: str,
    conversation: list[dict[str, str]] | None = None,
    depth: int = 0,
) -> str:
    """
    Execute one full agentic turn (may loop internally).
    *depth* guards against infinite handover recursion.

    Supports both LLM-backed ``Agent`` and code-only
    ``DeterministicAgent`` instances.
    """
    # ── Set current agent context (tools read this) ───────
    current_agent.set(agent)

    # ── Deterministic fast-path ────────────────────────────
    if isinstance(agent, DeterministicAgent):
        return _run_deterministic(agent, user_message, conversation, depth)

    # ── LLM ReAct loop ────────────────────────────────────
    if depth == 0:
        # Ensure a runtime context is active for the global helpers
        from hybridagents.core.runtime import current_runtime, Runtime
        if current_runtime() is None:
            _rt = Runtime(load_defaults=True)
            _rt.activate()

    if depth > 10:
        return "[ERROR] Maximum handover depth reached."

    system_prompt = _build_system_prompt(agent)
    messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]

    # Carry over prior conversation if supplied
    if conversation:
        messages.extend(conversation)

    messages.append({"role": "user", "content": user_message})

    limit = agent.max_iterations if agent.max_iterations is not None else MAX_LOOP_ITERATIONS
    for iteration in range(1, limit + 1):
        if VERBOSE:
            console.print(
                Panel(
                    f"[bold]{agent.name}[/bold]  iteration {iteration}",
                    style="cyan",
                )
            )

        llm_kwargs: dict[str, Any] = {"json_mode": True}
        if agent.provider:
            llm_kwargs["provider"] = agent.provider
        if agent.model:
            llm_kwargs["model"] = agent.model
        if agent.temperature is not None:
            llm_kwargs["temperature"] = agent.temperature
        raw = chat_completion(messages, **llm_kwargs)

        if VERBOSE:
            console.print(f"[dim]LLM raw:[/dim] {raw[:300]}")

        parsed = parse_json_response(raw)
        action = parsed.get("action", "")
        thought = parsed.get("thought", "")

        # Normalise: if the LLM put the tool name in "action" instead
        # of the literal word "tool", detect it and fix up.
        if action not in ("tool", "answer", "handover", ""):
            known_tools = {t.name for t in get_tools(agent.tool_names or None)}
            if action in known_tools:
                # Treat the action value as the tool name
                parsed.setdefault("tool_name", action)
                action = "tool"

        if VERBOSE and thought:
            console.print(f"  [yellow]Thought:[/yellow] {thought}")

        # ── Final answer ──────────────────────────────────────
        if action == "answer":
            answer = parsed.get("answer", raw)
            if VERBOSE:
                console.print(f"  [green]Answer:[/green] {answer}")
            return answer

        # ── Tool call ─────────────────────────────────────────
        elif action == "tool":
            tool_name = parsed.get("tool_name", "")
            arguments = parsed.get("arguments", {})
            if VERBOSE:
                console.print(f"  [blue]Tool:[/blue] {tool_name}({arguments})")

            result = call_tool(tool_name, arguments)

            if VERBOSE:
                console.print(f"  [magenta]Result:[/magenta] {result[:300]}")

            # Feed observation back
            messages.append({"role": "assistant", "content": raw})
            messages.append(
                {
                    "role": "user",
                    "content": f"[Tool result for {tool_name}]: {result}",
                }
            )

        # ── Handover ──────────────────────────────────────────
        elif action == "handover":
            target_name = parsed.get("agent_name", "")
            task = parsed.get("task", user_message)
            target_agent = get_agent(target_name)

            if target_agent is None:
                messages.append({"role": "assistant", "content": raw})
                messages.append(
                    {
                        "role": "user",
                        "content": f"[ERROR] Agent '{target_name}' not found. Available: {[a.name for a in agents_available_to(agent)]}",
                    }
                )
                continue

            if VERBOSE:
                console.print(
                    f"  [red]Handover → {target_name}[/red]: {task[:120]}"
                )

            sub_result = run_agent(target_agent, task, depth=depth + 1)

            # Return sub-result as observation
            messages.append({"role": "assistant", "content": raw})
            messages.append(
                {
                    "role": "user",
                    "content": f"[Handover result from {target_name}]: {sub_result}",
                }
            )

        # ── Unknown / malformed ───────────────────────────────
        else:
            messages.append({"role": "assistant", "content": raw})
            messages.append(
                {
                    "role": "user",
                    "content": (
                        '[System] Your response was not valid. The "action" field must be '
                        'exactly one of: "tool", "handover", or "answer". '
                        'For tool calls use: {"action": "tool", "tool_name": "<name>", "arguments": {...}, "thought": "..."}. '
                        "Please respond with the correct JSON format."
                    ),
                }
            )

    return "[WARNING] Agent hit the iteration limit without a final answer."
