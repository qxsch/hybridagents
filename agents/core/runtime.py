"""
Runtime – the top-level container that owns tool & agent registries.

A ``Runtime`` holds its own ``ToolRegistry`` and ``AgentRegistry``.
When you call ``rt.repl()`` or ``rt.run()`` the runtime activates itself
via a ``contextvars.ContextVar`` so that all module-level helpers
(``call_tool``, ``get_agent``, …) resolve to **this** runtime's registries.

Quick start::

    from agents import Agent, Runtime, tool

    rt = Runtime()  # loads default tools (calculator, file, search, privacy)

    rt.register(Agent(name="assistant", instruction="You are helpful."))
    rt.repl("assistant")
"""

from __future__ import annotations

import contextvars
from typing import Any, Callable, TYPE_CHECKING, overload

if TYPE_CHECKING:
    from agents.core.agent import Agent
    from agents.core.deterministic_agent import DeterministicAgent

from agents.core.agent_registry import AgentRegistry
from agents.core.tool_registry import ToolRegistry, _default_registry


# ── Context variable ───────────────────────────────────────

_current_runtime: contextvars.ContextVar["Runtime | None"] = contextvars.ContextVar(
    "_current_runtime", default=None,
)


def current_runtime() -> "Runtime | None":
    """Return the runtime active in the current context, if any."""
    return _current_runtime.get()


# ── Runtime class ──────────────────────────────────────────

class Runtime:
    """Self-contained environment with its own tool & agent registries.

    Parameters
    ----------
    load_defaults:
        If *True* (the default), the four built-in SDK tool modules
        (``calculator``, ``file``, ``search``, ``privacy``) are
        loaded into this runtime's tool registry automatically.
    """

    def __init__(self, *, load_defaults: bool = True) -> None:
        self.tools = ToolRegistry()
        self.agents = AgentRegistry()

        if load_defaults:
            self._load_default_tools()

    # -- convenience agent registration -------------------------

    @overload
    def register(self, agent: "Agent") -> "Agent": ...
    @overload
    def register(self, agent: "DeterministicAgent") -> "DeterministicAgent": ...

    def register(self, agent: "Agent | DeterministicAgent") -> "Agent | DeterministicAgent":
        """Register an agent and return it (for chaining)."""
        return self.agents.register(agent)

    # -- convenience tool registration --------------------------

    def tool(
        self,
        name: str,
        description: str,
        parameters: dict[str, Any] | None = None,
    ) -> Callable:
        """Decorator that registers a function as a tool in this runtime.

        Usage::

            @rt.tool(name="greet", description="Say hello")
            def greet(name: str) -> str:
                return f"Hello, {name}!"
        """
        from agents.core.tool_registry import ToolDefinition, _infer_params

        def decorator(fn: Callable[..., str]) -> Callable[..., str]:
            td = ToolDefinition(
                name=name,
                description=description,
                parameters=parameters or _infer_params(fn),
                fn=fn,
            )
            self.tools.register(td)
            return fn

        return decorator

    # -- run / repl with context-var activation -----------------

    def run(
        self,
        agent: "Agent | DeterministicAgent | str",
        message: str,
        *,
        conversation: list[dict[str, str]] | None = None,
        **kwargs: Any,
    ) -> str:
        """Execute a single agentic turn inside this runtime's context.

        *agent* can be an ``Agent`` instance or a registered name.
        """
        from agents.core.loop import run_agent

        agent_obj = self._resolve_agent(agent)
        token = _current_runtime.set(self)
        try:
            return run_agent(agent_obj, message, conversation=conversation, **kwargs)
        finally:
            _current_runtime.reset(token)

    def repl(
        self,
        agent: "Agent | DeterministicAgent | str",
        *,
        max_iterations: int | None = None,
    ) -> None:
        """Start an interactive REPL inside this runtime's context."""
        from agents.core.repl import run_repl

        agent_obj = self._resolve_agent(agent)
        token = _current_runtime.set(self)
        try:
            run_repl(agent_obj, max_iterations=max_iterations)
        finally:
            _current_runtime.reset(token)

    # -- context-manager support --------------------------------

    def activate(self) -> contextvars.Token:
        """Manually activate this runtime (for orchestration, tests, etc.).

        Returns a token you can pass to ``deactivate()`` later::

            token = rt.activate()
            try:
                result = sequential([a, b, c], task)
            finally:
                rt.deactivate(token)
        """
        return _current_runtime.set(self)

    def deactivate(self, token: contextvars.Token) -> None:
        """Restore the previous runtime."""
        _current_runtime.reset(token)

    def __enter__(self) -> "Runtime":
        self._ctx_token = _current_runtime.set(self)
        return self

    def __exit__(self, *exc: Any) -> None:
        _current_runtime.reset(self._ctx_token)

    # -- internal -----------------------------------------------

    def _resolve_agent(self, agent: "Agent | DeterministicAgent | str") -> "Agent | DeterministicAgent":
        from agents.core.agent import Agent as AgentCls
        from agents.core.deterministic_agent import DeterministicAgent as DetCls

        if isinstance(agent, str):
            obj = self.agents.get(agent)
            if obj is None:
                available = self.agents.names()
                raise KeyError(
                    f"Agent '{agent}' not found in this runtime. "
                    f"Available: {available}"
                )
            return obj
        if isinstance(agent, (AgentCls, DetCls)):
            return agent
        raise TypeError(f"Expected Agent, DeterministicAgent, or str, got {type(agent)}")

    def _load_default_tools(self) -> None:
        """Copy whatever tools were registered by module-level @tool decorators.

        The SDK tool modules (calculator, file, search, privacy) are
        imported once at the module level — their @tool decorators
        populate ``_default_registry``.  We ensure that import has
        happened, then snapshot the defaults into our own registry.
        """
        # Trigger side-effect imports (safe to call multiple times)
        import agents.tools  # noqa: F401

        self.tools.copy_from(_default_registry)
