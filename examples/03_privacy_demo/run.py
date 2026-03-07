"""
03 – Privacy Demo

Shows the privacy pipeline in action:
  • Scan text for PII / financial data
  • Anonymise before sending to a remote LLM
  • De-anonymise the response

Usage:
    python examples/03_privacy_demo/run.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agents import Agent, Runtime

# ── Build runtime (default tools include privacy_*) ────────
rt = Runtime()

# ── Privacy-aware agent ────────────────────────────────────
rt.register(
    Agent(
        name="privacy_agent",
        instruction=(
            "You are a privacy-aware assistant. Before processing any text "
            "that may contain personal data you ALWAYS:\n"
            "1. Use privacy_scan to check what sensitive items exist.\n"
            "2. Use privacy_anonymize to replace them with safe placeholders.\n"
            "3. Work with the anonymised text.\n"
            "4. Use privacy_deanonymize on your final answer to restore originals.\n\n"
            "Never reveal raw PII in intermediate reasoning."
        ),
        tool_names=[
            "privacy_scan",
            "privacy_anonymize",
            "privacy_deanonymize",
            "calculator",
        ],
    )
)


def main() -> None:
    from rich.console import Console
    from rich.panel import Panel

    console = Console()
    console.print(
        Panel(
            "[bold]Privacy Demo[/bold]\n\n"
            "Try pasting text that contains e-mails, IBANs, phone numbers,\n"
            "amounts of money, or tax IDs. The agent will scan & anonymise\n"
            "before reasoning, then de-anonymise the answer.",
            title="03 – Privacy Demo",
            style="magenta",
        )
    )
    rt.repl("privacy_agent")


if __name__ == "__main__":
    main()
