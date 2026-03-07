# 04 – Orchestration Patterns

Interactive demo of SDK orchestration strategies:

| Pattern      | What happens |
|-------------|-------------|
| `sequential` | drafter → critic → editor pipeline |
| `debate`     | optimist vs pessimist, judge synthesizes |
| `voting`     | multiple agents answer independently, judge picks best |

```bash
python examples/04_orchestration_patterns/run.py
python examples/04_orchestration_patterns/run.py --pattern debate
```
