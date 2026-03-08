# 08 – Memory Isolation (Competitive Intelligence)

Demonstrates `memory_collection` — controlling which ChromaDB collection
each agent reads from and writes to.

## Scenario

You are tracking three fictional tech startups:

| Startup               | Analyst agent         | Private collection    |
|-----------------------|-----------------------|-----------------------|
| **NovaMind AI**       | `analyst_novamind`    | `intel_novamind`      |
| **QuantumLeap Labs**  | `analyst_quantumleap` | `intel_quantumleap`   |
| **FusionScale Energy** | `analyst_fusionscale`  | `intel_fusionscale`    |

Each analyst stores intel in its own **private** ChromaDB collection —
completely isolated from the others.  A deterministic `briefing_writer`
(NoteTaker) stores cross-cutting notes **verbatim** in a **shared**
`briefing_board` collection — no LLM involved, so no hallucination risk.

A deterministic **Strategist** agent queries **all four collections** at
once and synthesises a landscape briefing.

## What's shown

- **Private collections** — each analyst only sees its own data via `memory_search` / `memory_store`.
- **Grounding guardrail** — analyst prompts forbid inventing facts beyond the user message and memory hits.
- **Deterministic note-taker** — `briefing_writer` files notes verbatim (no LLM, no hallucination).
- **Shared collection** — `briefing_writer` and `strategist` both use `briefing_board`.
- **Cross-collection query** — `Strategist.execute()` passes `collection_name=` to `self.memory_query()` to read from any collection.
- **Pipe mode** — feed a news event from the shell; the agent processes it once and exits.
- **Interactive mode** — start a REPL for a full conversation.

## Run (pipe mode — non-interactive)

Feed news events one at a time.  Each command processes the input and exits:

```bash
# NovaMind news → stored in intel_novamind
echo 'NovaMind AI closed a $50M Series B led by Sequoia. They will expand their enterprise LLM platform into healthcare and finance.' | python examples/08_memory_isolation/run.py --agent analyst_novamind

# QuantumLeap news → stored in intel_quantumleap
echo 'QuantumLeap Labs unveiled SingularityQ, a 1000-qubit quantum processor with zero error rate. IBM, Microsoft and Google are reportedly in licensing talks.' | python examples/08_memory_isolation/run.py --agent analyst_quantumleap

# FusionScale news → stored in intel_fusionscale
echo 'FusionScale Energy partnered with Tesla for grid-scale battery storage. Their new solid-state cells hit 500 Wh/kg — double the industry average.' | python examples/08_memory_isolation/run.py --agent analyst_fusionscale

# Shared briefing note → stored in briefing_board
echo 'Board meeting next Tuesday — need competitive positioning across AI, quantum, and energy sectors.' | python examples/08_memory_isolation/run.py --agent briefing_writer

# Ask the strategist to synthesise everything
echo 'Compare all three competitors on recent funding and product launches' | python examples/08_memory_isolation/run.py --agent strategist
```

## Run (interactive mode)

Without a pipe, the agent starts an interactive REPL:

```bash
# Chat with the strategist (default)
python examples/08_memory_isolation/run.py

# Chat with a specific analyst
python examples/08_memory_isolation/run.py --agent analyst_novamind
```

## Suggested workflow

1. Pipe a few news events into the three analysts (see above).
2. Optionally add a team note via `briefing_writer`.
3. Ask the strategist — either piped or interactively — e.g. *"Compare all competitors on funding and partnerships"*.
4. The strategist queries across all four collections and returns a merged briefing.
