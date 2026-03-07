"""
Agent registry – keeps track of all agents and provides handover mechanics.

Provides two layers:

1. ``AgentRegistry`` – an instance that holds ``Agent`` objects.
2. Module-level helpers (``register_agent``, ``get_agent``, …) that
   resolve to the active ``Runtime`` via a context-var.  When no runtime
   is active they fall back to a module-level default registry.
"""

from __future__ import annotations

from typing import Union

from hybridagents.core.agent import Agent
from hybridagents.core.deterministic_agent import DeterministicAgent

#: Any agent type that can be registered in a runtime.
AnyAgent = Union[Agent, DeterministicAgent]


# ── Registry class ─────────────────────────────────────────

class AgentRegistry:
    """Instance-based agent store.  Each ``Runtime`` owns one."""

    def __init__(self) -> None:
        self._agents: dict[str, AnyAgent] = {}

    # -- mutators ------------------------------------------------

    def register(self, agent: AnyAgent) -> AnyAgent:
        """Register an agent. Returns the same agent for convenience."""
        self._agents[agent.name] = agent
        return agent

    def clear(self) -> None:
        self._agents.clear()

    # -- queries -------------------------------------------------

    def get(self, name: str) -> AnyAgent | None:
        return self._agents.get(name)

    def all(self) -> list[AnyAgent]:
        return list(self._agents.values())

    def names(self) -> list[str]:
        return list(self._agents.keys())

    def available_to(self, agent: AnyAgent) -> list[AnyAgent]:
        """Return Agent objects this agent is allowed to hand tasks to."""
        return [self._agents[n] for n in agent.handover_agents if n in self._agents]

    # -- copy helpers --------------------------------------------

    def copy_from(self, other: "AgentRegistry") -> None:
        self._agents.update(other._agents)

    def snapshot(self) -> "AgentRegistry":
        r = AgentRegistry()
        r._agents = dict(self._agents)
        return r


# ── Default (module-level) registry ────────────────────────

_default_registry = AgentRegistry()


def _active_registry() -> AgentRegistry:
    """Return the registry of the active runtime, or the default."""
    from hybridagents.core.runtime import current_runtime
    rt = current_runtime()
    return rt.agents if rt is not None else _default_registry


# ── Backward-compatible module-level functions ─────────────

def register_agent(agent: AnyAgent) -> AnyAgent:
    """Register an agent into the active runtime (or default registry)."""
    return _active_registry().register(agent)


def get_agent(name: str) -> AnyAgent | None:
    return _active_registry().get(name)


def all_agents() -> list[AnyAgent]:
    return _active_registry().all()


def all_agent_names() -> list[str]:
    return _active_registry().names()


def agents_available_to(agent: AnyAgent) -> list[AnyAgent]:
    return _active_registry().available_to(agent)


def clear_agents() -> None:
    """Clear the default registry (useful in tests)."""
    _default_registry.clear()
