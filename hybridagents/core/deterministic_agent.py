"""
Deterministic agent base class.

A ``DeterministicAgent`` runs user-defined code — no LLM, no tools.
Subclass it and implement :meth:`execute` to plug pure-Python logic
into the same ecosystem used by LLM agents: ``run_agent()``,
``Runtime.run()``, ``Runtime.repl()``, and all orchestration patterns.

Example::

    from hybridagents import DeterministicAgent, AgentResponse, HandoverRequest

    class Router(DeterministicAgent):
        def execute(self, message, conversation=None, context=None):
            if "urgent" in message.lower():
                return HandoverRequest(agent_name="escalation", task=message)
            return AgentResponse(answer=f"Handled: {message}")
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from hybridagents.core.results import AgentResponse, HandoverRequest


def _resolve_collection(memory_collection: str | None) -> str:
    """Return the effective ChromaDB collection name."""
    from hybridagents.config import CHROMA_COLLECTION
    return memory_collection or CHROMA_COLLECTION


class DeterministicAgent(ABC):
    """Agent that runs user-defined code — no LLM, no tools.

    Parameters
    ----------
    name:
        Unique agent name (used in registries and handovers).
    instruction:
        Human-readable description.  Shown to orchestrators and
        in the REPL welcome banner.
    handover_agents:
        Names of agents this agent is allowed to hand tasks to.
    memory_collection:
        ChromaDB collection name.  ``None`` → global default from config.
    """

    def __init__(
        self,
        name: str,
        instruction: str = "",
        handover_agents: list[str] | None = None,
        memory_collection: str | None = None,
    ) -> None:
        self.name = name
        self.instruction = instruction
        self.handover_agents: list[str] = handover_agents or []
        self.memory_collection: str | None = memory_collection

        # Stubs so orchestrator / registry code that reads these
        # attributes on a generic "agent" never raises AttributeError.
        self.tool_names: list[str] = []
        self.provider: str | None = None
        self.model: str | None = None
        self.temperature: float | None = None
        self.max_iterations: int | None = None

    # ── memory convenience methods ────────────────────────

    def memory_store(
        self,
        text: str,
        metadata: dict[str, Any] | None = None,
        doc_id: str | None = None,
        collection_name: str | None = None,
    ) -> str:
        """Store text into a memory collection.  Returns the doc id.

        Parameters
        ----------
        collection_name:
            Target collection.  ``None`` (default) → this agent's own
            ``memory_collection`` (or the global default).
        """
        from hybridagents.core import memory
        effective = collection_name or _resolve_collection(self.memory_collection)
        return memory.store(
            text,
            metadata=metadata,
            collection_name=effective,
            doc_id=doc_id,
        )

    def memory_query(
        self,
        query: str,
        n_results: int = 5,
        where: dict[str, Any] | None = None,
        collection_name: str | None = None,
    ) -> list[dict[str, Any]]:
        """Semantic search in a memory collection.

        Parameters
        ----------
        collection_name:
            Collection to search.  ``None`` (default) → this agent's own
            ``memory_collection`` (or the global default).
        """
        from hybridagents.core import memory
        effective = collection_name or _resolve_collection(self.memory_collection)
        return memory.query(
            query,
            n_results=n_results,
            collection_name=effective,
            where=where,
        )

    def memory_list_collections(self) -> list[str]:
        """List all ChromaDB collections."""
        from hybridagents.core import memory
        return memory.list_collections()

    # ── abstract entry point ──────────────────────────────

    @abstractmethod
    def execute(
        self,
        message: str,
        conversation: list[dict[str, str]] | None = None,
        context: dict[str, Any] | None = None,
    ) -> AgentResponse | HandoverRequest:
        """Override this with your deterministic logic.

        Parameters
        ----------
        message:
            The user (or upstream agent) message to process.
        conversation:
            Prior conversation turns, same format as the LLM loop
            (list of ``{"role": …, "content": …}`` dicts).
        context:
            Optional carry-over data from a previous deterministic
            agent's ``HandoverRequest.context``.

        Returns
        -------
        AgentResponse
            When the agent can answer directly.
        HandoverRequest
            When the agent wants to delegate to another agent.
        """
        ...

    # ── compatibility helpers ─────────────────────────────

    def system_message(self) -> dict[str, str]:
        """Return a system-message dict, matching ``Agent.system_message()``."""
        return {"role": "system", "content": self.instruction}

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(name={self.name!r}, "
            f"handover_agents={self.handover_agents!r})"
        )
