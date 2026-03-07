"""
Orchestration helpers – plug agents together using standard patterns.

Patterns (inspired by Azure AI Agent Design Patterns):
  • sequential            – agents process a task in order, each refining the previous result
  • concurrent            – agents work in parallel, results are aggregated
  • group_chat            – agents converse in a shared chat, a manager picks the next speaker
  • handoff               – agents dynamically transfer control based on context
  • magentic              – a lead agent builds a plan then delegates steps to specialists
  • debate                – adversarial agents argue, a judge synthesizes
  • voting                – ensemble of agents vote on the best answer
  • reflection            – producer/critic loop until quality bar is met
  • router                – classifier agent routes task to one specialist
  • hierarchical          – recursive manager→worker tree
  • map_reduce            – split task, agents process chunks in parallel, reducer merges
  • blackboard            – shared memory space; agents contribute until goal is met
  • supervisor            – agents run freely; supervisor can veto/redirect
  • iterative_refinement  – single agent self-critiques and refines in a loop
  • auction               – agents bid confidence; highest bidder executes

Reference:
  https://learn.microsoft.com/azure/architecture/ai-ml/guide/ai-agent-design-patterns
"""

from hybridagents.core.orchestration.sequential import sequential  # noqa: F401
from hybridagents.core.orchestration.concurrent import concurrent  # noqa: F401
from hybridagents.core.orchestration.group_chat import group_chat  # noqa: F401
from hybridagents.core.orchestration.handoff import handoff  # noqa: F401
from hybridagents.core.orchestration.magentic import magentic  # noqa: F401
from hybridagents.core.orchestration.debate import debate  # noqa: F401
from hybridagents.core.orchestration.voting import voting  # noqa: F401
from hybridagents.core.orchestration.reflection import reflection  # noqa: F401
from hybridagents.core.orchestration.router import router  # noqa: F401
from hybridagents.core.orchestration.hierarchical import hierarchical  # noqa: F401
from hybridagents.core.orchestration.map_reduce import map_reduce  # noqa: F401
from hybridagents.core.orchestration.blackboard import blackboard  # noqa: F401
from hybridagents.core.orchestration.supervisor import supervisor  # noqa: F401
from hybridagents.core.orchestration.iterative_refinement import iterative_refinement  # noqa: F401
from hybridagents.core.orchestration.auction import auction  # noqa: F401

__all__ = [
    "sequential",
    "concurrent",
    "group_chat",
    "handoff",
    "magentic",
    "debate",
    "voting",
    "reflection",
    "router",
    "hierarchical",
    "map_reduce",
    "blackboard",
    "supervisor",
    "iterative_refinement",
    "auction",
]
