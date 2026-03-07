"""
03 – Privacy Demo (deterministic scrub → LLM → deterministic restore)

Privacy is enforced **in code** – no reliance on the LLM calling
tools correctly:

  1. ``Scrubber`` (DeterministicAgent) – scans & anonymises the user
     message with `PrivacyPipeline.scrub()` and stashes the vault
     in `context` so the restorer can use it later.
  2. ``assistant`` (LLM Agent) – reasons over the *scrubbed* text.
     It never sees real PII.
  3. ``Restorer`` (DeterministicAgent) – replaces placeholders in the
     LLM answer with the originals from the vault.

The three agents are wired together with ``sequential()``.

Usage:
    python examples/03_privacy_demo/run.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from hybridagents import Agent, AgentResponse, DeterministicAgent, Runtime
from hybridagents.core.orchestration import sequential
from hybridagents.privacy import PrivacyConfig, PrivacyPipeline, EntityVault


# ── Shared state (vault travels between the two deterministic agents) ──
_shared_vault: EntityVault | None = None
_pipeline = PrivacyPipeline.from_config(PrivacyConfig.from_env())


# ── Deterministic agents ───────────────────────────────────


class Scrubber(DeterministicAgent):
    """Scan & anonymise PII before the LLM ever sees the text."""

    def execute(self, message, conversation=None, context=None):
        global _shared_vault

        scrubbed, vault = _pipeline.scrub(message)
        _shared_vault = vault  # stash for the Restorer

        # Show what was detected (purely informational)
        scan = _pipeline.scan(message)
        if scan.detections:
            tags = ", ".join(
                f"{d.filter_name}({d.original!r})" for d in scan.detections
            )
            print(f"  🛡  Scrubber detected: {tags}")
            print(f"  🛡  Scrubbed text:     {scrubbed}")
        else:
            print("  🛡  Scrubber: no PII detected")

        return AgentResponse(answer=scrubbed)


class Restorer(DeterministicAgent):
    """Replace placeholders with originals after the LLM has answered."""

    def execute(self, message, conversation=None, context=None):
        global _shared_vault

        if _shared_vault is None:
            return AgentResponse(answer=message)

        restored = _pipeline.restore(message, _shared_vault)
        if restored != message:
            print(f"  🛡  Restorer: placeholders replaced")
        _shared_vault = None  # reset for next turn
        return AgentResponse(answer=restored)


# ── Build runtime ──────────────────────────────────────────

rt = Runtime()

scrubber = Scrubber(
    name="scrubber",
    instruction="Scans user input and replaces PII with safe placeholders.",
)

assistant = Agent(
    name="assistant",
    instruction=(
        "You are a helpful assistant. Answer the user's question. "
        "Some parts of the input may be replaced with placeholders "
        "like <EMAIL_1> or <IBAN_1> — treat them as opaque tokens "
        "and include them as-is in your answer where relevant."
    ),
)

restorer = Restorer(
    name="restorer",
    instruction="Replaces placeholders with original values.",
)

rt.register(scrubber)
rt.register(assistant)
rt.register(restorer)

pipeline_agents = [scrubber, assistant, restorer]


# ── REPL that uses sequential orchestration ────────────────


def main() -> None:
    from rich.console import Console
    from rich.panel import Panel

    console = Console()
    console.print(
        Panel(
            "[bold]Privacy Demo[/bold]  (deterministic scrub → LLM → deterministic restore)\n\n"
            "Try pasting text that contains e-mails, IBANs, phone numbers,\n"
            "amounts of money, or tax IDs.\n\n"
            "The [cyan]Scrubber[/cyan] agent anonymises your input in code,\n"
            "the [green]assistant[/green] LLM reasons over the clean text,\n"
            "then the [cyan]Restorer[/cyan] agent puts the originals back.",
            title="03 – Privacy Demo",
            style="magenta",
        )
    )

    # Simple REPL loop using sequential orchestration
    while True:
        try:
            user_input = console.input("\n[bold magenta]You:[/bold magenta] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Bye![/dim]")
            break
        if not user_input or user_input.lower() in ("exit", "quit"):
            break

        result = sequential(pipeline_agents, user_input)
        console.print(f"\n[bold green]Assistant:[/bold green] {result}")


if __name__ == "__main__":
    main()
