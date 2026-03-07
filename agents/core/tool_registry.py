"""
Tool registry – the plugin system for agent tools.

Provides two layers:

1. ``ToolRegistry`` – an instance that holds ``ToolDefinition`` objects.
2. Module-level helpers (``tool``, ``get_tool``, ``call_tool``, …) that
   resolve to whichever ``Runtime`` is currently active via a context-var.
   When no runtime is active they fall back to a module-level default
   registry so that ``@tool(...)`` at import time still works.

HOW TO ADD A NEW TOOL
─────────────────────
Decorate a function with ``@tool``:

    from agents import tool

    @tool(
        name="my_tool",
        description="One-line description shown to the LLM.",
        parameters={
            "query": {"type": "string", "description": "Search query"},
        },
    )
    def my_tool(query: str) -> str:
        return f"result for {query}"

To register into a specific ``Runtime`` instead of the default registry::

    @tool(name="my_tool", description="...", runtime=rt)
    def my_tool(query: str) -> str: ...
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from typing import Any, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from agents.core.runtime import Runtime


@dataclass
class ToolDefinition:
    """Metadata + callable for one tool."""

    name: str
    description: str
    parameters: dict[str, Any]  # JSON-Schema-like param descriptions
    fn: Callable[..., str]

    def schema_for_prompt(self) -> dict[str, Any]:
        """Return a dict the LLM can read to understand the tool."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }


# ── Registry class ─────────────────────────────────────────

class ToolRegistry:
    """Instance-based tool store.  Each ``Runtime`` owns one."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    # -- mutators ------------------------------------------------

    def register(self, tool_def: ToolDefinition) -> ToolDefinition:
        self._tools[tool_def.name] = tool_def
        return tool_def

    def clear(self) -> None:
        self._tools.clear()

    # -- queries -------------------------------------------------

    def get(self, name: str) -> ToolDefinition | None:
        return self._tools.get(name)

    def get_many(self, names: list[str] | None = None) -> list[ToolDefinition]:
        if names is None:
            return list(self._tools.values())
        return [self._tools[n] for n in names if n in self._tools]

    def names(self) -> list[str]:
        return list(self._tools.keys())

    def call(self, name: str, arguments: dict[str, Any]) -> str:
        td = self._tools.get(name)
        if td is None:
            return f"[ERROR] Unknown tool: {name}"
        try:
            result = td.fn(**arguments)
            return str(result)
        except Exception as exc:
            return f"[ERROR] Tool '{name}' raised: {exc}"

    # -- copy helpers --------------------------------------------

    def copy_from(self, other: "ToolRegistry") -> None:
        """Merge all tools from *other* into this registry."""
        self._tools.update(other._tools)

    def snapshot(self) -> "ToolRegistry":
        """Return a shallow copy."""
        r = ToolRegistry()
        r._tools = dict(self._tools)
        return r


# ── Default (module-level) registry ────────────────────────
# Used by the @tool decorator at import time (before any Runtime exists).

_default_registry = ToolRegistry()


def _active_registry() -> ToolRegistry:
    """Return the registry of the active runtime, or the default."""
    from agents.core.runtime import current_runtime
    rt = current_runtime()
    return rt.tools if rt is not None else _default_registry


# ── @tool decorator ────────────────────────────────────────

def tool(
    name: str,
    description: str,
    parameters: dict[str, Any] | None = None,
    *,
    runtime: "Runtime | None" = None,
) -> Callable:
    """Decorator that registers a function as an agent tool.

    Parameters
    ----------
    name, description, parameters:
        Metadata shown to the LLM.
    runtime:
        If given, register into that *runtime*'s tool registry.
        If omitted and a runtime is active (via ``with rt:``),
        register into that runtime.  Otherwise register into the
        module-level default registry.
    """

    def decorator(fn: Callable[..., str]) -> Callable[..., str]:
        td = ToolDefinition(
            name=name,
            description=description,
            parameters=parameters or _infer_params(fn),
            fn=fn,
        )
        if runtime is not None:
            runtime.tools.register(td)
        else:
            # If a Runtime is active (via context manager), register there;
            # otherwise fall back to the module-level default registry.
            from agents.core.runtime import current_runtime
            active = current_runtime()
            if active is not None:
                active.tools.register(td)
            else:
                _default_registry.register(td)
        return fn

    return decorator


# ── Backward-compatible module-level functions ─────────────
# These resolve via the active runtime's registry (context-var)
# so loop.py and orchestration patterns need zero changes.

def get_tool(name: str) -> ToolDefinition | None:
    return _active_registry().get(name)


def get_tools(names: list[str] | None = None) -> list[ToolDefinition]:
    return _active_registry().get_many(names)


def all_tool_names() -> list[str]:
    return _active_registry().names()


def call_tool(name: str, arguments: dict[str, Any]) -> str:
    return _active_registry().call(name, arguments)


def clear_tools() -> None:
    """Clear the default registry (useful in tests)."""
    _default_registry.clear()


# ── Helpers ────────────────────────────────────────────────

def _infer_params(fn: Callable) -> dict[str, Any]:
    """Auto-generate parameter schema from function signature."""
    sig = inspect.signature(fn)
    params: dict[str, Any] = {}
    for pname, p in sig.parameters.items():
        ptype = "string"
        if p.annotation is int:
            ptype = "integer"
        elif p.annotation is float:
            ptype = "number"
        elif p.annotation is bool:
            ptype = "boolean"
        params[pname] = {"type": ptype, "description": pname}
    return params
