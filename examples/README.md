# Examples

Self-contained examples showing how to use the `agents` SDK.

Each example is directly runnable from the **repo root**:

```bash
# Option A: pip install (recommended)
pip install -e .
python examples/01_simple_chat/run.py

# Option B: no install needed – each script adds the repo root to sys.path
python examples/01_simple_chat/run.py
```

## Examples

| #  | Directory                    | What it shows |
|----|------------------------------|---------------|
| 01 | `01_simple_chat/`            | Minimal single-agent REPL – no tools, no delegation |
| 02 | `02_research_team/`          | Orchestrator delegates to researcher & coder agents |
| 03 | `03_privacy_demo/`           | Privacy pipeline: scan, anonymise, de-anonymise |
| 04 | `04_orchestration_patterns/` | Using SDK orchestration (sequential, debate, voting…) |
| 05 | `05_custom_tools/`           | Writing and registering custom tools |
| 06 | `06_deterministic/`          | Deterministic (code-only) agents with handovers |
| 07 | `07_multi_runtime/`          | Multiple isolated runtimes, context-manager enter/exit |

## Creating Your Own Example

1. Create a new directory under `examples/`, e.g. `examples/06_my_demo/`.
2. Add a `run.py` (entry point) and optionally `agents.py`, `tools.py`, etc.
3. At the top of `run.py`, add the path preamble (so it works without `pip install -e .`):

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
```

4. Import from the SDK and register your agents/tools.
5. Run: `python examples/06_my_demo/run.py`
