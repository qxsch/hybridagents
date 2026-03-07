"""
GitHub Copilot provider – uses the official Copilot SDK.

Requires:
  - pip install github-copilot-sdk
  - GitHub Copilot CLI installed and authenticated (``copilot --version``)
"""

from __future__ import annotations

import asyncio
import concurrent.futures
from typing import Any, cast

from copilot import CopilotClient, PermissionRequest, PermissionRequestResult
from copilot.types import CopilotClientOptions, SessionConfig, SystemMessageConfig

from agents.config import GHCOPILOT_MODEL, GHCOPILOT_CLI_URL
from agents.core.providers.base import LLMProvider


def _deny_all(request: PermissionRequest, *args: Any) -> PermissionRequestResult:
    """Deny every permission request so the SDK acts as a pure chat endpoint."""
    return cast(PermissionRequestResult, {"kind": "denied-by-rules"})


class GHCopilotProvider(LLMProvider):
    """Talks to GitHub Copilot via the official Copilot SDK.

    The SDK is async; this provider bridges to the synchronous
    ``LLMProvider.chat`` interface expected by the framework.
    """

    # ------------------------------------------------------------------
    # internal async implementation
    # ------------------------------------------------------------------

    async def _async_chat(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float | None = None,
        json_mode: bool = False,
    ) -> str:
        # Build client options
        client_opts = cast(CopilotClientOptions, {})
        if GHCOPILOT_CLI_URL:
            client_opts["cli_url"] = GHCOPILOT_CLI_URL

        client = CopilotClient(client_opts) if client_opts else CopilotClient()
        await client.start()

        try:
            # ── session config ────────────────────────────────────
            session_cfg = cast(SessionConfig, {
                "model": model,
                "on_permission_request": _deny_all,
                "available_tools": [],          # disable all SDK built-in tools
                "mcp_servers": {},              # no MCP servers
                "custom_agents": [],            # no SDK-level agents
                "skill_directories": [],        # no SDK skills
            })

            # Extract system message(s) from the messages list
            system_parts = [
                m["content"] for m in messages if m.get("role") == "system"
            ]
            if system_parts:
                sys_msg: SystemMessageConfig = {
                    "content": "\n".join(system_parts),
                }
                session_cfg["system_message"] = sys_msg

            # If JSON mode requested, append a hint to the system message
            if json_mode:
                json_hint = "You MUST respond with valid JSON only."
                existing = session_cfg.get("system_message")
                if existing and "content" in existing:
                    existing["content"] = existing["content"] + f"\n{json_hint}"  # type: ignore[typeddict-item]
                else:
                    session_cfg["system_message"] = {"content": json_hint}

            session = await client.create_session(session_cfg)

            # ── build prompt from messages ─────────────────────────
            # The Copilot SDK injects its own system-level persona which
            # can override the session-config ``system_message``.  To make
            # sure the model follows our ReAct protocol we embed the full
            # system instructions directly in the prompt text so they are
            # always visible to the model.
            system_parts_prompt = [
                m["content"] for m in messages if m.get("role") == "system"
            ]
            non_system = [m for m in messages if m.get("role") != "system"]
            if not non_system:
                return ""

            prompt_sections: list[str] = []

            # 1) Inject system instructions as an explicit block.
            #    The SDK injects its own persona; embedding our full
            #    protocol in the prompt ensures the model always sees it.
            if system_parts_prompt:
                prompt_sections.append(
                    "=== INSTRUCTIONS (you MUST follow these) ===\n"
                    + "\n".join(system_parts_prompt)
                    + "\n=== END INSTRUCTIONS ==="
                )

            # 1b) If the system prompt mentions delegatable agents,
            #     add a nudge so the model prefers delegation over
            #     answering itself (counters the SDK’s built-in
            #     "helpful coding assistant" persona).
            joined_sys = "\n".join(system_parts_prompt)
            if "handover" in joined_sys or "delegate" in joined_sys:
                prompt_sections.append(
                    "NOTE: When specialist agents are listed above, "
                    "you SHOULD delegate tasks to them rather than "
                    "answering yourself, unless the user explicitly "
                    "asks you to answer directly."
                )

            # 2) Prior conversation turns (tool results, assistant replies)
            if len(non_system) > 1:
                for m in non_system[:-1]:
                    role = m.get("role", "user").capitalize()
                    prompt_sections.append(f"[{role}]: {m['content']}")

            # 3) Current user message
            prompt_sections.append(non_system[-1]["content"])

            # 4) JSON-mode reinforcement at the very end of the prompt
            if json_mode:
                prompt_sections.append(
                    "REMINDER: You MUST respond with a single valid JSON object only. "
                    "No markdown, no explanation outside the JSON."
                )

            prompt = "\n\n".join(prompt_sections)

            response = await session.send_and_wait({"prompt": prompt})
            content = (
                response.data.content
                if response and response.data and response.data.content
                else ""
            )
            return content

        finally:
            await client.stop()

    # ------------------------------------------------------------------
    # public synchronous interface (required by LLMProvider)
    # ------------------------------------------------------------------

    def chat(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float | None = None,
        json_mode: bool = False,
    ) -> str:
        coro = self._async_chat(messages, model, temperature, json_mode)

        # If we're already inside a running event loop (e.g. Jupyter,
        # nested async), run the coroutine in a separate thread.
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(asyncio.run, coro).result()

        return asyncio.run(coro)
