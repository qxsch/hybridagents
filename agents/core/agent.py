"""
Agent base class.

Each agent has:
- a name & system instruction
- a list of tool names it can use
- a list of agent names it can hand tasks to
- an optional memory collection
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Agent:
    """Declarative agent definition."""

    name: str
    instruction: str  # system prompt
    tool_names: list[str] = field(default_factory=list)
    handover_agents: list[str] = field(default_factory=list)  # agent names this agent can call
    memory_collection: str | None = None  # ChromaDB collection for this agent's memory
    provider: str | None = None  # "ollama" | "aifoundry" – None → DEFAULT_PROVIDER
    model: str | None = None  # override global model per agent
    temperature: float | None = None  # override global temperature
    max_iterations: int | None = None  # override MAX_LOOP_ITERATIONS per agent

    def system_message(self) -> dict[str, str]:
        return {"role": "system", "content": self.instruction}
