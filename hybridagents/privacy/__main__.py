"""
CLI entry point for the privacy SDK.

Usage::

    python -m agents.privacy scan   --text "max@firma.de"
    python -m agents.privacy scan   --file invoice.txt
    python -m agents.privacy scan   --text "DE89..." --filters iban
    python -m agents.privacy scrub  --text "Send €5,000 to max@firma.de" --show-vault
    python -m agents.privacy roundtrip --text "Max Mustermann, max@firma.de"
    python -m agents.privacy filters                       # list available filters
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from hybridagents.privacy.config import PrivacyConfig
from hybridagents.privacy.pipeline import PrivacyPipeline
from hybridagents.privacy.vault import EntityVault


def _build_pipeline(args: argparse.Namespace) -> PrivacyPipeline:
    """Construct a pipeline from CLI flags."""
    config = PrivacyConfig.default()
    if args.filters:
        config.filters = [f.strip() for f in args.filters.split(",")]
    if getattr(args, "llm", False):
        config.llm_filter.enabled = True
    if getattr(args, "threshold", None) is not None:
        config.confidence_threshold = args.threshold
    return PrivacyPipeline.from_config(config)


def _get_text(args: argparse.Namespace) -> str:
    """Get input text from --text or --file."""
    if args.text:
        return args.text
    if args.file:
        return Path(args.file).read_text(encoding="utf-8")
    # stdin
    if not sys.stdin.isatty():
        return sys.stdin.read()
    print("Error: provide --text, --file, or pipe text via stdin.", file=sys.stderr)
    sys.exit(1)


def cmd_scan(args: argparse.Namespace) -> None:
    """Scan text and print detections."""
    pipeline = _build_pipeline(args)
    text = _get_text(args)
    result = pipeline.scan(text)

    if not result.detections:
        print("No detections.")
        return

    print(f"\n  Detections ({result.count} found):")
    print("  " + "─" * 56)
    for d in result.detections:
        print(
            f"  [{d.filter_name:12s}] {d.original!r:30s} → {d.placeholder or '(n/a)':16s} "
            f"confidence: {d.confidence:.2f}"
        )
    print()


def cmd_scrub(args: argparse.Namespace) -> None:
    """Scrub text and print anonymised version."""
    pipeline = _build_pipeline(args)
    text = _get_text(args)
    scrubbed, vault = pipeline.scrub(text)

    print("\n  Scrubbed output:")
    print("  " + "─" * 56)
    print(f"  {scrubbed}")

    if args.show_vault:
        print("\n  Vault:")
        print("  " + "─" * 56)
        for placeholder, original in vault.items():
            print(f"  {placeholder:20s} → {original}")
    print()


def cmd_roundtrip(args: argparse.Namespace) -> None:
    """Demonstrate full scrub → restore round-trip."""
    pipeline = _build_pipeline(args)
    text = _get_text(args)
    scrubbed, vault = pipeline.scrub(text)
    restored = pipeline.restore(scrubbed, vault)

    print("\n  Original:")
    print(f"    {text}")
    print("\n  Scrubbed:")
    print(f"    {scrubbed}")
    print("\n  Restored:")
    print(f"    {restored}")

    match = "✓ MATCH" if restored == text else "✗ MISMATCH"
    print(f"\n  Round-trip: {match}")
    print()


def cmd_filters(args: argparse.Namespace) -> None:
    """List available built-in filters."""
    from hybridagents.privacy.filters import BUILTIN_FILTERS

    print("\n  Built-in filters:")
    print("  " + "─" * 40)
    for name, cls in BUILTIN_FILTERS.items():
        inst = cls()
        print(f"  {name:16s}  category={inst.category}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m agents.privacy",
        description="Privacy SDK – scan, scrub, and test anonymisation filters.",
    )
    sub = parser.add_subparsers(dest="command")

    # ── scan ────────────────────────────────────────────
    p_scan = sub.add_parser("scan", help="Scan text for sensitive data")
    p_scan.add_argument("--text", "-t", help="Text to scan")
    p_scan.add_argument("--file", "-f", help="File to read and scan")
    p_scan.add_argument("--filters", help="Comma-separated filter names")
    p_scan.add_argument("--llm", action="store_true", help="Enable local LLM filter")
    p_scan.add_argument("--threshold", type=float, default=None, help="Min confidence")
    p_scan.set_defaults(func=cmd_scan)

    # ── scrub ───────────────────────────────────────────
    p_scrub = sub.add_parser("scrub", help="Scrub (anonymise) text")
    p_scrub.add_argument("--text", "-t", help="Text to scrub")
    p_scrub.add_argument("--file", "-f", help="File to read and scrub")
    p_scrub.add_argument("--filters", help="Comma-separated filter names")
    p_scrub.add_argument("--llm", action="store_true", help="Enable local LLM filter")
    p_scrub.add_argument("--threshold", type=float, default=None, help="Min confidence")
    p_scrub.add_argument("--show-vault", action="store_true", help="Print the vault mapping")
    p_scrub.set_defaults(func=cmd_scrub)

    # ── roundtrip ───────────────────────────────────────
    p_rt = sub.add_parser("roundtrip", help="Demo full scrub→restore cycle")
    p_rt.add_argument("--text", "-t", help="Text to round-trip")
    p_rt.add_argument("--file", "-f", help="File to read and round-trip")
    p_rt.add_argument("--filters", help="Comma-separated filter names")
    p_rt.add_argument("--llm", action="store_true", help="Enable local LLM filter")
    p_rt.add_argument("--threshold", type=float, default=None, help="Min confidence")
    p_rt.set_defaults(func=cmd_roundtrip)

    # ── filters ─────────────────────────────────────────
    p_filt = sub.add_parser("filters", help="List available filters")
    p_filt.set_defaults(func=cmd_filters)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
