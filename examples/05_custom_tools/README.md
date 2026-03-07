# 05 – Custom Tools

Demonstrates how to write your own tools using the `@tool` decorator and
wire them to an agent.

**Files:**
- `tools.py` – defines `current_time`, `dice_roll`, `word_count`
- `run.py` – imports the tools and starts a REPL

```bash
python examples/05_custom_tools/run.py
```

Try: "What time is it?", "Roll 3d20", "Count the words in: hello world foo bar"
