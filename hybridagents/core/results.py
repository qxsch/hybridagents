"""
Structured result types for agent execution.

``AgentResponse`` represents a successful result; ``HandoverRequest``
signals that execution should be delegated to another agent.  Together
they form a discriminated union that deterministic agents return from
their ``execute()`` method.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentResponse:
    """Successful result produced by an agent.

    Parameters
    ----------
    answer:
        The textual answer (what ``run_agent`` ultimately returns as ``str``).
    metadata:
        Optional structured payload.  Orchestration patterns or
        downstream agents can inspect this for scores, classifications,
        intermediate objects, etc.
    """

    answer: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class HandoverRequest:
    """Signal: delegate execution to another agent.

    Parameters
    ----------
    agent_name:
        Name of the target agent (must be registered in the runtime).
    task:
        The message / task description forwarded to the target agent.
    context:
        Optional carry-over data (e.g. original input, intermediate
        state).  Passed to the target if it is also a deterministic
        agent; ignored when the target is an LLM agent.
    """

    agent_name: str
    task: str
    context: dict[str, Any] = field(default_factory=dict)
