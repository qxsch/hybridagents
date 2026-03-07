# 07 – Multiple Runtimes

Demonstrates **runtime isolation** and the context-manager protocol.

## What's shown

| Concept                    | How                                                       |
|----------------------------|-----------------------------------------------------------|
| **Two isolated runtimes**  | `rt_research` and `rt_coding` — agents don't leak across  |
| **`with rt:` block**       | Context manager activates the runtime for orchestration    |
| **`activate` / `deactivate`** | Manual token-based control for when `with` isn't enough |
| **Switching runtimes**     | Back-to-back `with` blocks targeting different runtimes    |
| **`@tool(..., runtime=...)` decorator**  | Register a tool directly into a specific runtime |
| **`@tool` in `with rt:`**  | `@tool` auto-targets the active runtime's registry         |

## Agents

| Runtime       | Agent        | Type | Purpose                          |
|---------------|-------------|------|----------------------------------|
| `rt_research` | `researcher` | LLM  | Summarises research topics       |
| `rt_research` | `reviewer`   | LLM  | Reviews for accuracy             |
| `rt_coding`   | `coder`      | LLM  | Writes Python code               |
| `rt_coding`   | `tester`     | LLM  | Suggests unit tests              |

## Run

```bash
python examples/07_multi_runtime/run.py
```
