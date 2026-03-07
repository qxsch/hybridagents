# hybridagents – Hybrid LLM Agentic Framework (Ollama + Azure AI Foundry + GitHub Copilot)

This is a works-for-me project used for educational purposes.

A modular Python agentic loop with **hybrid LLM routing** — run models locally via **Ollama** or in the cloud via **Azure AI Foundry** (GPT-4o, Claude, Mistral, and more) or **GitHub Copilot** (via the official Copilot SDK). Uses **ChromaDB** for vector memory.

## Prerequisites

- **Python 3.10+**
- **Ollama** — local LLM runtime. Download & install from [https://ollama.com/download](https://ollama.com/download)
- **Azure AI Foundry** (optional) — for cloud models. Set up an endpoint in the [Azure AI Foundry portal](https://ai.azure.com)
- **GitHub Copilot CLI** (optional, **⚠️ highly experimental**) — for Copilot SDK models. This is highly experimental and may break agent functionality due to the SDK's opinionated architecture. Install & authenticate via [Copilot CLI guide](https://docs.github.com/en/copilot/how-tos/set-up/install-copilot-cli)

## Quick Start

```bash
# 1. Install Ollama (see Prerequisites above), then pull a model
ollama pull phi4
ollama serve          # if not already running

# 2. Activate the virtual environment
.\.venv\Scripts\Activate.ps1

# 3. Install the SDK in editable mode (one-time)
pip install hybridagents
# or from source use:   pip install -e .

# 4. Configure environment (copy and edit)
cp .env.example .env    # then fill in your values

# 5. Run an example
python examples/01_simple_chat/run.py           # minimal single-agent REPL
python examples/02_research_team/run.py          # orchestrator + researcher + coder
python examples/03_privacy_demo/run.py           # privacy scan/anonymise/restore
python examples/04_orchestration_patterns/run.py # sequential, debate, voting
python examples/05_custom_tools/run.py           # custom @tool decorator
python examples/06_deterministic/run.py          # deterministic (code-only) agents
python examples/07_multi_runtime/run.py          # multiple isolated runtimes, enter/exit
```

> **No install?** Each example also works without `pip install -e .` — it adds
> the repo root to `sys.path` automatically.

### Examples Overview

| #  | Directory                         | What it shows |
|----|-----------------------------------|---------------|
| 01 | `examples/01_simple_chat/`        | Minimal single-agent REPL — no tools, no delegation |
| 02 | `examples/02_research_team/`      | Orchestrator delegates to researcher & coder |
| 03 | `examples/03_privacy_demo/`       | Privacy pipeline: scan, anonymise, de-anonymise |
| 04 | `examples/04_orchestration_patterns/` | Sequential, debate, voting patterns |
| 05 | `examples/05_custom_tools/`       | Writing and registering custom tools |
| 06 | `examples/06_deterministic/`      | Deterministic (code-only) agents with handovers |
| 07 | `examples/07_multi_runtime/`      | Multiple isolated runtimes, context-manager enter/exit |

## Environment Configuration

All secrets and tunables live in a **`.env`** file (never committed to git).  
Copy `.env.example` to `.env` and edit:

```env
# ── Provider: "ollama" (default), "aifoundry", or "ghcopilot" ──
DEFAULT_PROVIDER=ollama
DEFAULT_MODEL=phi4
DEFAULT_TEMPERATURE=0.3

# ── Ollama (local inference) ──
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_NUM_CTX=8192

# ── Azure AI Foundry ──
AZURE_FOUNDRY_ENDPOINT=https://<your-resource>.services.ai.azure.com/v1
AZURE_FOUNDRY_API_KEY=<your-api-key>
AZURE_FOUNDRY_MODEL=gpt-4o

# ── GitHub Copilot (via Copilot SDK) — ⚠️ HIGHLY EXPERIMENTAL ──
GHCOPILOT_MODEL=claude-opus-4.6
#GHCOPILOT_CLI_URL=localhost:4321   # optional: external CLI in headless mode
```

| Variable                 | Default   | Description                                     |
|--------------------------|-----------|-------------------------------------------------|
| `DEFAULT_PROVIDER`       | `ollama`  | `"ollama"`, `"aifoundry"`, or `"ghcopilot"`      |
| `DEFAULT_MODEL`          | `phi4`    | Default model name (used when agent doesn't override) |
| `DEFAULT_TEMPERATURE`    | `0.3`     | Default LLM temperature                         |
| `OLLAMA_BASE_URL`        | `http://localhost:11434` | Ollama server address            |
| `OLLAMA_NUM_CTX`         | `8192`    | Context window size for Ollama                  |
| `AZURE_FOUNDRY_ENDPOINT` |           | Azure AI Foundry OpenAI-compatible endpoint URL |
| `AZURE_FOUNDRY_API_KEY`  |           | API key for Azure AI Foundry                    |
| `AZURE_FOUNDRY_MODEL`    | `gpt-4o`  | Default Foundry model                           |
| `GHCOPILOT_MODEL`        | `claude-opus-4.6` | Default model for GitHub Copilot provider |
| `GHCOPILOT_CLI_URL`      |           | Optional URL of an external Copilot CLI server (e.g. `localhost:4321`) |

## Hybrid LLM Providers

Each agent can target a different **provider + model**. The framework currently supports three providers:

| Provider              | Value          | Backend                                   | Models                                    |
|-----------------------|----------------|-------------------------------------------|-------------------------------------------|
| **Ollama**            | `"ollama"`     | Local inference via Ollama                | phi4, llama3, qwen2.5-coder, mistral, ... |
| **Azure AI Foundry**  | `"aifoundry"`  | Cloud inference via OpenAI-compatible API | OpenAI GPT, Claude, Mistral Large, ...    |
| **GitHub Copilot** ⚠️ | `"ghcopilot"`  | Cloud inference via Copilot SDK           | gpt-4.1, and other Copilot-hosted models  |

> **⚠️ GitHub Copilot provider — highly experimental.**
> This is highly experimental and may break agent functionality due to the SDK's opinionated architecture.
> Use at your own risk; prefer `ollama` or `aifoundry` for production workloads.

> **Privacy guardrail:** Both remote providers (`aifoundry` and `ghcopilot`) automatically run outgoing
> messages through the privacy pipeline when `PRIVACY_AUTO_FILTER=true`.
> Local `ollama` calls skip the filter.

### Per-Agent Routing

```python
# Uses global defaults (ollama + phi4) — nothing to change
Agent(name="orchestrator", instruction="...", ...)

# Explicitly uses local Ollama with a specific model
Agent(name="coder", provider="ollama", model="qwen2.5-coder", ...)

# Routes to Azure AI Foundry (any deployed model)
Agent(name="researcher", provider="aifoundry", model="gpt-4o", ...)

# Routes to GitHub Copilot via the SDK
Agent(name="copilot_helper", provider="ghcopilot", model="gpt-4.1", ...)

# Claude via Foundry
Agent(name="analyst", provider="aifoundry", model="claude-sonnet", ...)
```

When `provider` or `model` is `None`, the agent falls back to `DEFAULT_PROVIDER` / `DEFAULT_MODEL` from `.env`.

## Orchestration Patterns

The framework includes **15 ready-to-use orchestration helpers** inspired by
[Azure AI Agent Design Patterns](https://learn.microsoft.com/azure/architecture/ai-ml/guide/ai-agent-design-patterns).
Import them from `agents.core.orchestration`:

```python
from hybridagents.core.orchestration import (
    sequential, concurrent, group_chat, handoff, magentic,
    debate, voting, reflection, router, hierarchical,
    map_reduce, blackboard, supervisor, iterative_refinement, auction,
)
```

### 1. Sequential

Agents process a task in order — each receives the previous agent's output.

```
Task → Agent A → Agent B → Agent C → Final Output
```

```python
result = sequential(
    agents=[researcher, coder],
    task="Find the best sorting algorithm, then implement it in Python.",
)
```

### 2. Concurrent

All agents work in parallel on the same task. Results are aggregated.

```
Task → [Agent A, Agent B, Agent C] → Aggregate → Final Output
```

```python
result = concurrent(
    agents=[researcher, coder, analyst],
    task="Evaluate the pros and cons of microservices.",
    aggregate=lambda results: "\n---\n".join(results),  # custom merge
)
```

### 3. Group Chat

Agents converse in a shared chat. A manager agent decides who speaks next.

```
User → Manager picks Agent A → Agent A speaks → Manager picks Agent B → …
```

```python
result = group_chat(
    agents=[researcher, coder, analyst],
    task="Design a REST API for a todo app.",
    manager=orchestrator,   # optional – defaults to first agent
    max_rounds=8,
)
```

### 4. Handoff

Agents dynamically transfer control to each other based on context.

```
Task → Agent A → (handoff) → Agent B → (handoff) → Agent C → Final Output
```

```python
result = handoff(
    agents=[orchestrator, researcher, coder],
    task="Research Python async patterns, then write an example.",
    entry_agent=orchestrator,
)
```

### 5. Magentic

A lead agent creates a plan, then delegates each step to the best specialist.
After all steps complete, the lead synthesizes a final answer.

```
Task → Lead creates plan → Step 1 (Agent B) → Step 2 (Agent C) → … → Lead synthesizes
```

```python
result = magentic(
    agents=[orchestrator, researcher, coder],
    task="Build a CLI weather app: research APIs, write code, add tests.",
    lead=orchestrator,
)
```

### 6. Debate / Adversarial

Two+ agents argue opposing positions. A judge synthesizes the best answer.

```
Task → Agent A argues → Agent B rebuts → … (N rounds) → Judge rules
```

```python
result = debate(
    agents=[optimist, pessimist],
    task="Should we adopt microservices for our startup?",
    judge=architect,
    max_rounds=3,
)
```

### 7. Voting / Ensemble

All agents answer independently → a judge picks or merges the best answer.

```
Task → [Agent A, Agent B, Agent C] (parallel) → Judge picks best → Final Output
```

```python
result = voting(
    agents=[researcher, coder, analyst],
    task="What's the most efficient way to parse large JSON files in Python?",
    judge=orchestrator,
)
```

### 8. Reflection / Critic

A producer creates output, a critic reviews it. Loop until quality is met.

```
Task → Producer drafts → Critic reviews → Producer revises → … → APPROVED
```

```python
result = reflection(
    producer=coder,
    critic=reviewer,
    task="Write a thread-safe singleton in Python.",
    max_rounds=3,
)
```

### 9. Router

A classifier agent inspects the task and routes to exactly one specialist.

```
Task → Classifier → picks Agent B → Agent B handles it → Final Output
```

```python
result = router(
    agents=[researcher, coder, analyst],
    task="Help me fix this segfault in my C code.",
    classifier=orchestrator,
)
```

### 10. Hierarchical / Tree

Recursive manager→worker tree. Managers decompose, workers execute, results bubble up.

```
Task → Manager splits → [Worker A, Worker B] → Workers may split further → Synthesize
```

```python
result = hierarchical(
    agents=[orchestrator, researcher, coder],
    task="Build a complete documentation site for our API.",
    manager=orchestrator,
    max_depth=2,
)
```

### 11. Map-Reduce

Split task into chunks → agents process in parallel → reducer merges.

```
Task → Splitter → [Chunk 1 (A), Chunk 2 (B), Chunk 3 (C)] → Reducer → Final Output
```

```python
result = map_reduce(
    agents=[researcher, analyst],
    task="Summarize each chapter of this 100-page report.",
    splitter=lambda t: t.split("\n---\n"),  # custom split logic
    reducer=orchestrator,
)
```

### 12. Blackboard

Shared memory space — agents read/write until the goal is reached.

```
Board ← Agent A contributes → Board ← Agent B contributes → … → GOAL_REACHED
```

```python
result = blackboard(
    agents=[researcher, coder, analyst],
    task="Collaboratively design a database schema for an e-commerce platform.",
    max_rounds=8,
    goal_check=lambda board: len(board) > 10,  # custom goal
)
```

### 13. Supervisor / Monitor

Agents run freely; a supervisor watches outputs and can approve, redirect, or override.

```
Task → Agent A → Supervisor reviews → APPROVE / REDIRECT Agent B / OVERRIDE instruction
```

```python
result = supervisor(
    agents=[coder, researcher],
    task="Write a secure login endpoint.",
    monitor=security_reviewer,
    max_rounds=5,
)
```

### 14. Iterative Refinement

A single agent drafts, self-critiques, and revises in a loop. Cheaper than reflection.

```
Task → Agent drafts → Agent self-critiques → Agent revises → … → FINAL
```

```python
result = iterative_refinement(
    agent=coder,
    task="Write a production-ready retry decorator with exponential backoff.",
    max_rounds=3,
)
```

### 15. Auction / Bid

Agents bid confidence scores. The highest bidder executes the task.

```
Task → [Agent A bids 85, Agent B bids 60, Agent C bids 92] → Agent C executes → Output
```

```python
result = auction(
    agents=[researcher, coder, analyst],
    task="Optimize this SQL query for performance.",
)
```

### Pattern Comparison

| # | Pattern | Flow | Best for |
|---|---------|------|----------|
| 1 | **Sequential** | A → B → C | Pipelines, step-by-step refinement |
| 2 | **Concurrent** | [A, B, C] → merge | Parallel analysis, ensemble answers |
| 3 | **Group Chat** | Manager-directed conversation | Brainstorming, collaborative problem solving |
| 4 | **Handoff** | Dynamic agent-to-agent transfer | Escalation, context-dependent routing |
| 5 | **Magentic** | Lead plans → specialists execute | Complex open-ended tasks, SRE automation |
| 6 | **Debate** | Pro ↔ Con → Judge | Critical decisions, reducing hallucination |
| 7 | **Voting** | All answer → Judge picks best | High-stakes reliability, consensus |
| 8 | **Reflection** | Producer ↔ Critic loop | Code gen, writing, iterative polish |
| 9 | **Router** | Classifier → 1-of-N | Triage, helpdesk, mixed-domain workloads |
| 10 | **Hierarchical** | Manager → Sub-managers → Workers | Large decomposable tasks, org-chart delegation |
| 11 | **Map-Reduce** | Split → parallel process → merge | Document summarization, batch analysis |
| 12 | **Blackboard** | Shared board, agents self-activate | Emergent problem-solving, design sessions |
| 13 | **Supervisor** | Agent runs + monitor approves | Safety-critical, compliance, guardrails |
| 14 | **Iterative Refinement** | Single agent self-revises | Quick quality boost without a second agent |
| 15 | **Auction** | Agents bid → winner executes | Dynamic capability matching, heterogeneous pools |

## Architecture

```
.env                          # Secrets & config (gitignored)
.env.example                  # Committed template
pyproject.toml                # pip install -e .  (makes agents importable)

hybridagents/                       # ── SDK (framework only, no example code) ──
├── config.py                 # Loads .env, exposes settings
├── core/
│   ├── llm.py                # LLM router (dispatches to provider) + auto-filter hook
│   ├── repl.py               # Reusable interactive REPL (used by examples)
│   ├── orchestration/        # Orchestration patterns (15 helpers)
│   │   ├── __init__.py       # Re-exports all patterns
│   │   ├── _common.py        # Shared imports (console, VERBOSE, Agent, …)
│   │   ├── sequential.py     # 1. Sequential pipeline
│   │   ├── concurrent.py     # 2. Concurrent / parallel broadcast
│   │   ├── group_chat.py     # 3. Manager-directed group conversation
│   │   ├── handoff.py        # 4. Dynamic agent-to-agent handoff
│   │   ├── magentic.py       # 5. Lead plans → specialists execute
│   │   ├── debate.py         # 6. Adversarial debate → judge rules
│   │   ├── voting.py         # 7. Ensemble voting → judge picks best
│   │   ├── reflection.py     # 8. Producer ↔ critic loop
│   │   ├── router.py         # 9. Classifier routes to one specialist
│   │   ├── hierarchical.py   # 10. Recursive manager → worker tree
│   │   ├── map_reduce.py     # 11. Split → parallel → reduce
│   │   ├── blackboard.py     # 12. Shared memory, agents contribute
│   │   ├── supervisor.py     # 13. Monitor approves / redirects / overrides
│   │   ├── iterative_refinement.py  # 14. Single-agent self-revision loop
│   │   └── auction.py        # 15. Confidence bidding → winner executes
│   ├── providers/
│   │   ├── base.py           # Abstract LLMProvider interface
│   │   ├── ollama_provider.py    # Ollama SDK implementation
│   │   └── aifoundry_provider.py # Azure AI Foundry (OpenAI SDK)
│   ├── memory.py             # ChromaDB vector store
│   ├── runtime.py            # Runtime container (owns tool + agent registries)
│   ├── tool_registry.py      # Decorator-based tool plugin system
│   ├── agent.py              # Agent dataclass (provider, model, …)
│   ├── deterministic_agent.py # DeterministicAgent ABC (code-only agents)
│   ├── results.py            # AgentResponse & HandoverRequest result types
│   ├── agent_registry.py     # Multi-agent registry + handover
│   └── loop.py               # ReAct agentic loop (+ deterministic dispatch)
├── privacy/                  # Privacy SDK – anonymisation & filtering
│   ├── __init__.py           # Public API surface
│   ├── __main__.py           # CLI (python -m hybridagents.privacy)
│   ├── models.py             # Detection, ScanResult dataclasses
│   ├── vault.py              # EntityVault – reversible placeholder mapping
│   ├── config.py             # PrivacyConfig, LLMFilterConfig, CustomPatternConfig
│   ├── pipeline.py           # PrivacyPipeline – main orchestrator
│   └── filters/
│       ├── base.py           # Filter ABC
│       ├── regex_filter.py   # Generic user-configurable regex filter
│       ├── email_filter.py   # Email address detection
│       ├── phone_filter.py   # Phone numbers (DE/AT/CH + international)
│       ├── iban_filter.py    # IBAN with MOD-97 checksum validation
│       ├── tax_id_filter.py  # Tax IDs (USt-IdNr, UID, Steuer-ID)
│       ├── credential_filter.py  # API keys, tokens, connection strings
│       ├── money_filter.py   # Monetary amounts (€/$/ CHF/GBP)
│       └── llm_filter.py     # Local-LLM filter (names, companies, addresses)
├── tools/                    # Drop-in tool plugins
│   ├── search_tool.py        # memory_search, memory_store
│   ├── calculator_tool.py    # calculator
│   ├── file_tool.py          # read_file, write_file, list_dir
│   └── privacy_tool.py       # privacy_scan, privacy_anonymize, privacy_deanonymize

examples/                     # ── Self-contained, directly runnable examples ──
├── README.md                 # Overview of all examples
├── 01_simple_chat/
│   └── run.py                # Minimal: 1 agent, no tools
├── 02_research_team/
│   └── run.py                # Orchestrator + researcher + coder
├── 03_privacy_demo/
│   └── run.py                # Privacy scan/anonymise/restore
├── 04_orchestration_patterns/
│   └── run.py                # Sequential, debate, voting demo
├── 05_custom_tools/
│   ├── run.py                # Entry point
│   └── tools.py              # Custom tools: current_time, dice_roll, word_count
├── 06_deterministic/
│   └── run.py                # Deterministic agents: validator, keyword router
└── 07_multi_runtime/
    └── run.py                # Two isolated runtimes, with-block & activate/deactivate
```

## Runtime

A **`Runtime`** is a self-contained environment that owns its own tool and
agent registries.  Create one, register agents, and call `repl()` or `run()` —
no global functions needed.

```python
from hybridagents import Agent, Runtime

rt = Runtime()                         # loads default tools automatically

rt.register(Agent(name="assistant", instruction="You are helpful."))
rt.repl("assistant")                   # interactive REPL
```

Two runtimes are completely isolated — agents and tools registered in one
cannot be seen by the other.  This makes testing and multi-tenant setups
straightforward: create a runtime, use it, discard it.

### Context-var activation

When you call `rt.run()` or `rt.repl()`, the runtime activates itself via a
`contextvars.ContextVar` so that all internal helpers (`call_tool`,
`get_agent`, …) resolve to **this** runtime's registries. You can also
activate manually:

```python
with rt:                                       # context-manager
    result = sequential([a, b, c], task)

# or manual
token = rt.activate()
try:
    result = sequential([a, b, c], task)
finally:
    rt.deactivate(token)
```

### Targeting tools at a specific runtime

Three ways to register a tool into a specific runtime:

**Option 1: `rt.tool()` decorator** (recommended)

```python
rt = Runtime()

@rt.tool(name="greet", description="Say hello")
def greet(name: str) -> str:
    return f"Hello, {name}!"
```

**Option 2: Context-manager** — `@tool` inside a `with rt:` block auto-targets that runtime

```python
with rt:
    @tool(name="greet", description="Say hello")
    def greet(name: str) -> str:
        return f"Hello, {name}!"
```

**Option 3: Explicit `runtime=` keyword**

```python
@tool(name="greet", description="Say hello", runtime=rt)
def greet(name: str) -> str:
    return f"Hello, {name}!"
```

When no runtime is specified and no runtime is active, the tool lands in the
module-level default registry and is automatically included in every new
`Runtime()`.

## Deterministic Agents

Not every agent needs an LLM. A **`DeterministicAgent`** runs pure-Python
logic and plugs into the same ecosystem — `run_agent()`, `Runtime.run()`,
`Runtime.repl()`, and all 15 orchestration patterns.

```python
from hybridagents import DeterministicAgent, AgentResponse, HandoverRequest, Runtime

class InputValidator(DeterministicAgent):
    """Validates input, then delegates to an LLM agent."""

    def execute(self, message, conversation=None, context=None):
        cleaned = message.strip()
        if len(cleaned) < 3:
            return AgentResponse(answer="Message too short.")
        return HandoverRequest(agent_name="researcher", task=cleaned)

rt = Runtime()
rt.register(InputValidator(
    name="validator",
    instruction="Cleans and validates user input.",
    handover_agents=["researcher"],
))
rt.register(Agent(name="researcher", instruction="You research topics."))

rt.run("validator", "  Tell me about quantum computing  ")
```

### Return types

| Type | Purpose |
|------|-----|
| `AgentResponse(answer, metadata={})` | Agent answers directly. `metadata` is an optional structured payload. |
| `HandoverRequest(agent_name, task, context={})` | Delegate to another agent (LLM or deterministic). |

Handovers work in both directions: deterministic → LLM, LLM → deterministic,
and deterministic → deterministic. The depth limit of 5 applies to all chains.

See `examples/06_deterministic/` for a full working example.

## How to Create a New Example

1. Create a directory under `examples/`, e.g. `examples/06_my_demo/`.
2. Add a `run.py` entry point (and optionally `agents.py`, `tools.py`, etc.).
3. Use the `sys.path` preamble so it works with or without `pip install -e .`:

```python
# examples/06_my_demo/run.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
```

4. Create a `Runtime`, register agents, and start the REPL or run orchestration.
5. Run: `python examples/06_my_demo/run.py`

## How to Add a Custom Tool

### Option A: In an example (local to that example)

```python
# examples/05_custom_tools/tools.py
from hybridagents import tool

@tool(
    name="my_tool",
    description="Does something useful — shown to the LLM.",
    parameters={
        "query": {"type": "string", "description": "Input query"},
    },
)
def my_tool(query: str) -> str:
    return f"Result for {query}"
```

Then import it from your `run.py` before registering agents.

You can also register a tool directly into a specific `Runtime`:

```python
# Option A: rt.tool() decorator (recommended)
@rt.tool(name="my_tool", description="...")
def my_tool(query: str) -> str: ...

# Option B: @tool inside a with-block (auto-targets active runtime)
with rt:
    @tool(name="my_tool", description="...")
    def my_tool(query: str) -> str: ...

# Option C: explicit runtime= keyword
@tool(name="my_tool", description="...", runtime=rt)
def my_tool(query: str) -> str: ...
```

### Option B: In the SDK (available to all examples)

1. Create `hybridagents/tools/my_tool.py` with the `@tool` decorator.
2. Import it in `hybridagents/tools/__init__.py`:
```python
from hybridagents.tools import my_tool  # noqa: F401
```
3. Every `Runtime()` will automatically include the new tool.

See `examples/05_custom_tools/` for a working demo.

## How to Add a New Agent

Agents are defined where you need them — typically inside an example:

```python
# examples/06_my_demo/run.py
from hybridagents import Agent, Runtime

rt = Runtime()

rt.register(
    Agent(
        name="my_agent",
        instruction="You are a specialist in X. Always do Y.",
        tool_names=["calculator", "memory_search"],    # tools this agent can use
        handover_agents=["researcher"],                 # agents it can delegate to
        memory_collection="my_agent_memory",            # optional dedicated memory
        provider=None,       # None = use DEFAULT_PROVIDER from .env
        model=None,          # None = use DEFAULT_MODEL from .env
        temperature=None,    # None = use DEFAULT_TEMPERATURE from .env
    )
)

rt.repl("my_agent")
```

## Agent Handover

Agents can delegate tasks to other agents listed in their `handover_agents` field.

```
User → Orchestrator
            ├── "research this" → Researcher → answer
            └── "write code"    → Coder      → answer
```

The orchestrator receives the sub-agent's answer as an observation and can
continue reasoning or return the final answer to the user.
Handover depth is limited to 5 to prevent infinite loops.

## Configuration

All model/provider settings are loaded from `.env` (see **Environment Configuration** above).  
Non-secret settings in `config.py`:

| Setting              | Default                | Description                        |
|----------------------|------------------------|------------------------------------|
| `CHROMA_PERSIST_DIR` | `./hybridagents/chroma_data` | ChromaDB storage path        |
| `CHROMA_COLLECTION`  | `agent_memory`         | Default ChromaDB collection        |
| `MAX_LOOP_ITERATIONS`| `50`                   | Safety limit per agent turn        |
| `VERBOSE`            | `True`                 | Print reasoning steps to console   |

## Example Agents (02_research_team)

| Agent          | Tools                                           | Can delegate to        |
|----------------|-------------------------------------------------|------------------------|
| **orchestrator** | memory_search, memory_store, calculator       | researcher, coder      |
| **researcher**   | memory_search, memory_store, read_file, list_dir | —                   |
| **coder**        | calculator, read_file, write_file, list_dir   | —                      |

These agents are defined in `examples/02_research_team/run.py`.

## Pre-installed Tools

| Tool                   | Description                                               |
|------------------------|-----------------------------------------------------------|
| `memory_search`        | Semantic search over ChromaDB                             |
| `memory_store`         | Store text into ChromaDB                                  |
| `calculator`           | Safe math expression evaluator                            |
| `read_file`            | Read file from disk                                       |
| `write_file`           | Write file to disk                                        |
| `list_dir`             | List directory contents                                   |
| `privacy_scan`         | Scan text for PII/credentials (returns report, no change) |
| `privacy_anonymize`    | Replace sensitive data with reversible placeholders       |
| `privacy_deanonymize`  | Restore original values from placeholders                 |

---

## Privacy SDK

The **Privacy SDK** (`agents.privacy`) provides anonymisation and filtering of
sensitive data before it leaves the local machine — e.g. before sending prompts
to Azure AI Foundry or any remote LLM provider.

### Key Features

- **6 built-in regex filters** — email, phone, IBAN, tax ID, credentials, monetary amounts
- **Local-LLM filter** — uses Ollama to detect fuzzy PII (person names, company names, addresses)
- **Reversible placeholders** — `EntityVault` maps `<EMAIL_1>` ↔ `max@firma.de` for faithful round-trips
- **Auto-filter hook** — transparently scrubs outgoing messages for the `aifoundry` provider
- **Agent tools** — `privacy_scan`, `privacy_anonymize`, `privacy_deanonymize` integrate into the agentic loop
- **Standalone CLI** — test and debug without starting the agent framework
- **Declarative config** — configure from code, environment variables, or a JSON/YAML file
- **Custom patterns** — add regex rules via config without writing a Filter subclass

### Built-in Filters

| Filter       | Category     | Examples                                                   |
|--------------|--------------|------------------------------------------------------------|
| `email`      | EMAIL        | `max@firma.ch`, `user.name+tag@example.co.uk`              |
| `phone`      | PHONE        | `+49 170 1234567`, `089/12345-678`, `0170 12345678`        |
| `iban`       | IBAN         | `DE89 3704 0044 0532 0130 00` (MOD-97 validated)           |
| `tax_id`     | TAX_ID       | `DE123456789`, `ATU12345678`, `CHE-123.456.789`            |
| `credential` | CREDENTIAL   | `sk-proj-...`, `AKIA...`, `Bearer eyJ...`, `password=...`  |
| `money`      | MONEY        | `€5.000,00`, `$1,234.56`, `250.000 Euro`, `100 CHF`        |
| *regex*      | configurable | Use your own regex (via Python Code)                       |
| *LLM filter* | configurable | Person names, company names, addresses (via local Ollama)  |
| *custom*     | configurable | Define your own filter in Python code                      |

### CLI Usage

```bash
# List available filters
python -m hybridagents.privacy filters

# Scan text for sensitive data
python -m hybridagents.privacy scan --text "Max Mustermann, max@firma.de, IBAN DE89370400440532013000"

# Scrub text (replace PII with placeholders) and show the vault
python -m hybridagents.privacy scrub --text "Send €5,000 to max@firma.de" --show-vault

# Full round-trip: scrub → restore → verify match
python -m hybridagents.privacy roundtrip --text "Max Mustermann, max@firma.de"

# Read from a file
python -m hybridagents.privacy scan --file invoice.txt

# Pipe from stdin
echo "max@firma.de" | python -m hybridagents.privacy scan

# Use only specific filters
python -m hybridagents.privacy scan --text "..." --filters email,iban

# Enable local-LLM filter (requires running Ollama)
python -m hybridagents.privacy scan --text "Max Mustermann from Berlin" --llm

# Set confidence threshold
python -m hybridagents.privacy scan --text "..." --threshold 0.8
```

### Python API

```python
from hybridagents.privacy import PrivacyPipeline, PrivacyConfig, EntityVault

# 1. Create a pipeline (all built-in filters, default config)
pipeline = PrivacyPipeline.from_config(PrivacyConfig.default())

# 2. Scan – inspect detections without modifying text
result = pipeline.scan("max@firma.de, IBAN DE89370400440532013000")
for d in result.detections:
    print(f"{d.filter_name}: {d.original!r} (confidence: {d.confidence:.2f})")

# 3. Scrub – replace sensitive data with reversible placeholders
scrubbed, vault = pipeline.scrub("Send €5,000 to max@firma.de")
print(scrubbed)   # "Send <MONEY_1> to <EMAIL_1>"

# 4. Restore – bring back the original values
restored = pipeline.restore(scrubbed, vault)
assert restored == "Send €5,000 to max@firma.de"

# 5. Vault is serialisable (persist across requests)
vault_json = vault.to_json()
vault2 = EntityVault.from_json(vault_json)
```

#### Scrub chat messages (list of dicts)

```python
messages = [
    {"role": "user", "content": "My email is max@firma.de"},
    {"role": "user", "content": "IBAN: DE89370400440532013000"},
]
scrubbed_msgs, vault = pipeline.scrub_messages(messages)
# Each message's "content" is now anonymised
```

#### Custom regex patterns via config

```python
from hybridagents.privacy import PrivacyConfig, CustomPatternConfig, PrivacyPipeline

config = PrivacyConfig(
    filters=["email"],                     # only email + custom
    custom_patterns=[
        CustomPatternConfig(
            name="order_id",
            pattern=r"ORD-\d{6,10}",
            category="ORDER_ID",
            confidence=1.0,
        ),
    ],
)
pipeline = PrivacyPipeline.from_config(config)
result = pipeline.scan("Order ORD-12345678 for max@firma.de")
```

#### Adding custom filters via Python code

You can register additional filters on **any** pipeline instance at any time —
this works independently of the `PRIVACY_AUTO_FILTER` setting and the
`PrivacyConfig`.  There are three ways, from simplest to most flexible:

**1. Quick regex filter (one-liner)**

Use `add_regex_filter()` to add a pattern without writing a class:

```python
from hybridagents.privacy import PrivacyPipeline, PrivacyConfig

pipeline = PrivacyPipeline.from_config(PrivacyConfig.default())

# Add a custom regex filter for internal project IDs
pipeline.add_regex_filter(
    name="project_id",
    patterns=[r"PRJ-\d{6}"],
    category="internal",
    placeholder_prefix="PROJECT_ID",   # produces <PROJECT_ID_1>, <PROJECT_ID_2>, …
    confidence=1.0,
)

# Add another for Swiss AHV numbers
pipeline.add_regex_filter(
    name="ahv_number",
    patterns=[r"756\.\d{4}\.\d{4}\.\d{2}"],
    category="pii",
    placeholder_prefix="AHV",
)

# Both filters are now active alongside the built-in ones
result = pipeline.scan("Project PRJ-123456, AHV 756.1234.5678.90")
scrubbed, vault = pipeline.scrub("Project PRJ-123456, AHV 756.1234.5678.90")
print(scrubbed)   # "Project <PROJECT_ID_1>, AHV <AHV_1>"
```

**2. Instantiate `RegexFilter` directly and add it**

Equivalent to the above, but gives you direct access to the filter object:

```python
from hybridagents.privacy import PrivacyPipeline, PrivacyConfig, RegexFilter

pipeline = PrivacyPipeline.from_config(PrivacyConfig.default())

order_filter = RegexFilter(
    name="order_id",
    category="internal",
    patterns=[r"ORD-\d{6,10}", r"INV-\d{6,10}"],   # multiple patterns per filter
    placeholder_prefix="ORDER_ID",
    confidence=1.0,
)
pipeline.add_filter(order_filter)
```

**3. Write a full `Filter` subclass**

For complex detection logic that goes beyond regex (e.g. checksum validation,
context-aware heuristics), subclass `Filter` directly:

```python
from hybridagents.privacy import PrivacyPipeline, PrivacyConfig, Filter
from hybridagents.privacy.models import Detection

class MyCustomFilter(Filter):
    name = "custom_id"
    category = "internal"

    def scan(self, text: str) -> list[Detection]:
        detections = []
        # … your detection logic here …
        # For each match, append a Detection:
        #   Detection(filter_name=self.name, category=self.category,
        #             start=..., end=..., original=..., confidence=1.0)
        return detections

pipeline = PrivacyPipeline.from_config(PrivacyConfig.default())
pipeline.add_filter(MyCustomFilter())
```

> **Tip:** You can also remove built-in filters you don't need:
> `pipeline.remove_filter("money")`.  Use `pipeline.filter_names` to
> list all currently active filters.

### Agent Tools

Three tools are registered for use inside the agentic loop:

| Tool                  | Description                                                              |
|-----------------------|--------------------------------------------------------------------------|
| `privacy_scan`        | Inspect PII detections without changing the text                         |
| `privacy_anonymize`   | Scrub text and store mappings in a shared per-session vault              |
| `privacy_deanonymize` | Restore original values from the shared vault                            |

Add them to an agent:

```python
Agent(
    name="my_agent",
    tool_names=["privacy_scan", "privacy_anonymize", "privacy_deanonymize", ...],
    ...
)
```

### Example: Privacy-Safe Sequential Pipeline

Use the **sequential** orchestration pattern to build a three-step pipeline
where data is anonymised locally before it ever reaches a cloud LLM:

```
          User prompt
               │
               ▼
┌──────────────────────────────┐
│ 1. Anonymiser  (Ollama/phi4) │  ← local, scrubs PII
│    tool: privacy_anonymize   │
└──────────────┬───────────────┘
               │  scrubbed text
               ▼
┌────────────────────────────────────┐
│ 2. Processor  (AI Foundry/gpt-5.2) │  ← cloud, sees only placeholders
│    does the actual reasoning       │
└──────────────┬─────────────────────┘
               │  answer with placeholders
               ▼
┌──────────────────────────────────┐
│ 3. Deanonymiser  (Ollama/phi4)   │  ← local, restores real values
│    tool: privacy_deanonymize     │
└──────────────┬───────────────────┘
               │
               ▼
         Final answer (with real data)
```

#### 1. Define the agents

```python
# In your example run.py:
from hybridagents import Agent, Runtime

rt = Runtime()

anonymiser = rt.register(
    Agent(
        name="anonymiser",
        instruction=(
            "You are a privacy gate-keeper. "
            "Use the privacy_anonymize tool to replace ALL sensitive data "
            "(names, emails, IBANs, amounts, …) in the user's text with "
            "placeholders. Return ONLY the scrubbed text, nothing else."
        ),
        tool_names=["privacy_anonymize"],
        provider="ollama",
        model="phi4",
    )
)

processor = rt.register(
    Agent(
        name="processor",
        instruction=(
            "You are a helpful assistant. Answer the user's request. "
            "The text may contain placeholders like <EMAIL_1> or <PERSON_NAME_1> — "
            "keep them exactly as they are in your answer."
        ),
        tool_names=[],
        provider="aifoundry",
        model="gpt-5.2",
    )
)

deanonymiser = rt.register(
    Agent(
        name="deanonymiser",
        instruction=(
            "You are a privacy gate-keeper. "
            "Use the privacy_deanonymize tool to restore all placeholders "
            "in the text back to their original values. "
            "Return ONLY the restored text, nothing else."
        ),
        tool_names=["privacy_deanonymize"],
        provider="ollama",
        model="phi4",
    )
)
```

#### 2. Run the sequential pipeline

```python
from hybridagents.core.orchestration import sequential

with rt:
    result = sequential(
        agents=[anonymiser, processor, deanonymiser],
        task="Summarise this invoice: Max Mustermann, max@firma.de, IBAN DE89370400440532013000, €12.500,00",
    )
    print(result)
```

**What happens under the hood:**

| Step | Agent | Provider | Sees | Does |
|------|-------|----------|------|------|
| 1 | anonymiser | Ollama (local) | Raw text with PII | Calls `privacy_anonymize` → returns scrubbed text |
| 2 | processor | AI Foundry (cloud) | `<PERSON_NAME_1>, <EMAIL_1>, <IBAN_1>, <MONEY_1>` | Reasons over safe placeholders |
| 3 | deanonymiser | Ollama (local) | Answer with placeholders | Calls `privacy_deanonymize` → restores real values |

The cloud LLM **never sees** the real names, emails, IBANs, or amounts.
The `EntityVault` is shared in-process, so step 3 can restore everything
step 1 replaced — no data leaves the local machine unprotected.

> **Tip:** For simple use-cases where you don't need per-step agent reasoning,
> consider the [Auto-Filter Hook](#auto-filter-hook) instead — it does the
> scrub/restore transparently inside `llm.py` without extra agents.

### Auto-Filter Hook

When `PRIVACY_AUTO_FILTER=true` (or `auto_filter_enabled=True` in config),
the LLM router in `llm.py` **automatically scrubs messages** before sending
them to the `aifoundry` provider and **restores placeholders** in the response.
No agent configuration needed — it works as a transparent safety net.

```env
# .env
PRIVACY_AUTO_FILTER=true
```

Local Ollama calls are **never filtered** (the data stays on your machine).

### LLM Filter

The LLM filter uses a **local Ollama model** to detect fuzzy PII that regex
cannot catch — person names, company names, street addresses, etc.

```env
PRIVACY_LLM_FILTER=true
PRIVACY_LLM_MODEL=phi4              # any Ollama model
PRIVACY_LLM_CATEGORIES=person_name,company_name,address
```

The LLM filter employs a **"value is truth, offsets are hints"** strategy:
the LLM returns JSON with entity values and approximate character offsets.
The SDK trusts the **value** and uses the offsets only as search hints,
falling back to case-insensitive and whitespace-normalised matching when
offsets are wrong — making it robust against typical LLM inaccuracies.

### Privacy Configuration Reference

| Env Variable                   | Default         | Description                                     |
|--------------------------------|-----------------|-------------------------------------------------|
| `PRIVACY_FILTERS`              | *(all)*         | Comma-separated filter names to activate        |
| `PRIVACY_CONFIDENCE_THRESHOLD` | `0.0`           | Min confidence to keep a detection              |
| `PRIVACY_MODE`                 | `redact`        | `redact` (placeholders) or `mask` (****)        |
| `PRIVACY_AUTO_FILTER`          | `false`         | Auto-scrub on aifoundry calls                   |
| `PRIVACY_LLM_FILTER`          | `false`         | Enable local-LLM filter                         |
| `PRIVACY_LLM_MODEL`           | `phi4`          | Ollama model for LLM filter                     |
| `PRIVACY_LLM_CATEGORIES`      | `person_name,company_name,address` | Categories the LLM should detect |
