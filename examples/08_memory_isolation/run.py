"""
08 – Memory Isolation (ChromaDB Collections)

Demonstrates how ``memory_collection`` controls which ChromaDB collection
each agent reads from and writes to.

Use case: **Competitive Intelligence Briefing**

You track three fictional startups:

    NovaMind AI      – enterprise LLM platform
    QuantumLeap Labs – quantum computing hardware
    FusionScale Energy – clean-energy / battery tech

Each startup has a dedicated LLM analyst that stores intel in its own
**private** ChromaDB collection.  A shared **briefing board** holds
cross-cutting notes.  A deterministic **Strategist** agent queries
*all* collections at once to produce landscape summaries.

Supports two modes:

  **Pipe mode** — feed a news event directly from the shell::

      echo "NovaMind closed a $50M Series B" | python examples/08_memory_isolation/run.py --agent analyst_alpha

  **Interactive mode** — start a REPL for a conversation::

      python examples/08_memory_isolation/run.py --agent analyst_alpha

Usage:
    python examples/08_memory_isolation/run.py                        # strategist REPL
    python examples/08_memory_isolation/run.py --agent analyst_alpha  # analyst REPL
    echo "news …" | python examples/08_memory_isolation/run.py --agent analyst_alpha
"""

import sys
from pathlib import Path

# ── Make SDK importable ────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from hybridagents import (
    Agent,
    AgentResponse,
    DeterministicAgent,
    Runtime,
)


# ── Deterministic strategist ──────────────────────────────


class Strategist(DeterministicAgent):
    """Queries every analyst's private memory + the shared briefing
    collection and produces a merged competitive landscape summary."""

    ANALYST_COLLECTIONS = {
        "intel_novamind":    "NovaMind AI",
        "intel_quantumleap": "QuantumLeap Labs",
        "intel_fusionscale":  "FusionScale Energy",
    }
    SHARED_COLLECTION = "briefing_board"

    def execute(self, message, conversation=None, context=None):
        sections: list[str] = []

        # 1. Pull top findings from each analyst's private collection
        for coll, label in self.ANALYST_COLLECTIONS.items():
            hits = self.memory_query(
                message,
                n_results=3,
                collection_name=coll,
            )
            if hits:
                findings = "\n".join(
                    f"  - {h['document']}" for h in hits
                )
                sections.append(f"**{label}**\n{findings}")

        # 2. Pull shared briefing notes
        shared_hits = self.memory_query(
            message,
            n_results=3,
            collection_name=self.SHARED_COLLECTION,
        )
        if shared_hits:
            notes = "\n".join(f"  - {h['document']}" for h in shared_hits)
            sections.append(f"**Shared Briefing Notes**\n{notes}")

        if not sections:
            return AgentResponse(
                answer=(
                    "No intelligence gathered yet. "
                    "Feed some news to the analysts first!\n\n"
                    "Example:\n"
                    '  echo "NovaMind closed a $50M Series B" '
                    "| python examples/08_memory_isolation/run.py "
                    "--agent analyst_novamind"
                )
            )

        body = "\n\n".join(sections)
        summary = (
            f"=== Competitive Intelligence Briefing ===\n\n"
            f"Query: {message}\n\n{body}\n\n"
            f"--- end of briefing ---"
        )

        # Store the briefing itself into the shared collection
        self.memory_store(
            summary,
            metadata={"type": "briefing", "query": message},
            collection_name=self.SHARED_COLLECTION,
        )

        return AgentResponse(
            answer=summary,
            metadata={
                "collections_queried": list(self.ANALYST_COLLECTIONS) + [self.SHARED_COLLECTION],
            },
        )


# ── Deterministic note-taker (briefing board) ─────────────


class NoteTaker(DeterministicAgent):
    """Stores the incoming message verbatim into briefing_board.
    No LLM involved — avoids hallucination for simple note filing."""

    def execute(self, message, conversation=None, context=None):
        doc_id = self.memory_store(message, metadata={"type": "note"})
        return AgentResponse(
            answer=(
                f"Note stored in briefing_board "
                f"({len(message)} chars, id={doc_id})."
            )
        )


# ── Build runtime ──────────────────────────────────────────

rt = Runtime()

# ── LLM analysts — each writes to a private collection ────

rt.register(
    Agent(
        name="analyst_novamind",
        instruction=(
            "You are a competitive-intelligence analyst tracking NovaMind AI, "
            "an enterprise LLM-platform startup. "
            "When you receive news or a research request, always store the "
            "key facts with memory_store (product names, funding, partnerships, "
            "strengths, weaknesses). "
            "Use memory_search first to avoid duplicating what you already know. "
            "ONLY use facts explicitly stated in the user's message or returned "
            "by memory_search. NEVER add, infer, or invent facts from your own knowledge."
        ),
        tool_names=["memory_search", "memory_store"],
        memory_collection="intel_novamind",
    )
)

rt.register(
    Agent(
        name="analyst_quantumleap",
        instruction=(
            "You are a competitive-intelligence analyst tracking QuantumLeap Labs, "
            "a quantum-computing hardware startup. "
            "When you receive news or a research request, always store the "
            "key facts with memory_store (chip specs, partnerships, funding, "
            "competitive positioning). "
            "Use memory_search first to avoid duplicating what you already know. "
            "ONLY use facts explicitly stated in the user's message or returned "
            "by memory_search. NEVER add, infer, or invent facts from your own knowledge."
        ),
        tool_names=["memory_search", "memory_store"],
        memory_collection="intel_quantumleap",
    )
)

rt.register(
    Agent(
        name="analyst_fusionscale",
        instruction=(
            "You are a competitive-intelligence analyst tracking FusionScale Energy, "
            "a cleantech startup focused on battery storage and renewables. "
            "When you receive news or a research request, always store the "
            "key facts with memory_store (battery specs, partnerships, funding, "
            "regulatory wins). "
            "Use memory_search first to avoid duplicating what you already know. "
            "ONLY use facts explicitly stated in the user's message or returned "
            "by memory_search. NEVER add, infer, or invent facts from your own knowledge."
        ),
        tool_names=["memory_search", "memory_store"],
        memory_collection="intel_fusionscale",
    )
)

# ── Shared briefing board (deterministic — no LLM) ───────

rt.register(
    NoteTaker(
        name="briefing_writer",
        instruction="Stores cross-cutting briefing notes verbatim.",
        memory_collection="briefing_board",
    )
)

# ── Deterministic strategist — reads ALL collections ──────

rt.register(
    Strategist(
        name="strategist",
        instruction=(
            "Cross-references all analyst collections and the shared "
            "briefing board to produce competitive landscape summaries."
        ),
        memory_collection="briefing_board",
    )
)

# ── Entry point ────────────────────────────────────────────

BANNER = """\

 08 - Memory Isolation: Competitive Intelligence

 Startups tracked:
   NovaMind AI       -> analyst_novamind    (intel_novamind)
   QuantumLeap Labs  -> analyst_quantumleap (intel_quantumleap)
   FusionScale Energy -> analyst_fusionscale  (intel_fusionscale)
   (shared board)    -> briefing_writer     (briefing_board)
   (cross-query)     -> strategist          (reads all)

 Pipe mode:
   echo "some news" | python examples/08_memory_isolation/run.py --agent analyst_novamind

 Interactive mode (current):
   Type your messages below. Press Ctrl+C to quit.
"""


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Memory isolation demo")
    parser.add_argument(
        "--agent",
        default="strategist",
        help=f"Agent to talk to. Available: {rt.agents.names()}",
    )
    args = parser.parse_args()

    agent = rt.agents.get(args.agent)
    if agent is None:
        print(f"Unknown agent '{args.agent}'. Available: {rt.agents.names()}")
        sys.exit(1)

    # ── Pipe mode: stdin is not a terminal ─────────────────
    if not sys.stdin.isatty():
        message = sys.stdin.read().strip()
        if not message:
            print("Empty input on stdin — nothing to do.")
            sys.exit(0)
        print(f"[pipe → {agent.name}] {message}\n")
        answer = rt.run(agent, message)
        print(answer)
        return

    # ── Interactive mode: start the REPL ───────────────────
    print(BANNER)
    rt.repl(agent)


if __name__ == "__main__":
    main()
