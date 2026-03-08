"""
Context variable that tracks the currently executing agent.

Set by ``loop.run_agent()`` before each agent turn so that tools
(e.g. ``memory_search``, ``memory_store``) can resolve the agent's
``memory_collection`` without requiring extra parameters in the
tool schema.

Usage inside a tool::

    from hybridagents.core.agent_context import current_agent
    agent = current_agent.get(None)
    collection = agent.memory_collection if agent else None
"""

from __future__ import annotations

import contextvars
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from hybridagents.core.agent import Agent
    from hybridagents.core.deterministic_agent import DeterministicAgent

current_agent: contextvars.ContextVar[Union["Agent", "DeterministicAgent", None]] = (
    contextvars.ContextVar("current_agent", default=None)
)
