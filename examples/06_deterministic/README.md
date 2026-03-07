# 06 – Deterministic Agents

Demonstrates `DeterministicAgent` — agents that execute pure-Python
logic and integrate with the full SDK (REPL, orchestration, handovers).

## What's shown

| Agent             | Type            | Behaviour                                    |
|-------------------|-----------------|----------------------------------------------|
| `validator`       | Deterministic   | Cleans input, rejects short messages, hands over to `researcher` |
| `router`          | Deterministic   | Keyword-based routing to specialist agents   |
| `researcher`      | LLM             | Answers research questions                   |
| `calculator_agent`| LLM             | Evaluates math with the calculator tool      |

## Run

```bash
python examples/06_deterministic/run.py
```
