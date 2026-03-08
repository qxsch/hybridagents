"""
Tool: memory_search – semantic search over ChromaDB.
Tool: memory_store  – store a text chunk into ChromaDB.

Collection resolution:
    If the calling agent has ``memory_collection`` set, these tools
    operate on that collection.  Otherwise they fall back to the
    global default (``CHROMA_COLLECTION`` from config / env).
    The agent context is set automatically by ``loop.run_agent()``.
"""

from hybridagents.core.agent_context import current_agent
from hybridagents.core.tool_registry import tool
from hybridagents.core import memory
from hybridagents.config import CHROMA_COLLECTION


def _resolve_collection() -> str:
    """Return the effective ChromaDB collection for the calling agent."""
    if current_agent:
        agent = current_agent.get(None)
        if agent and agent.memory_collection:
            return agent.memory_collection
    return CHROMA_COLLECTION


@tool(
    name="memory_search",
    description="Semantic search over the vector memory (ChromaDB). Returns the most relevant stored documents.",
    parameters={
        "query": {"type": "string", "description": "Natural-language search query"},
        "n_results": {"type": "integer", "description": "Number of results (default 5)"},
    },
)
def memory_search(query: str, n_results: int = 5) -> str:
    collection = _resolve_collection()
    results = memory.query(query, n_results=int(n_results), collection_name=collection)
    if not results:
        return "No results found."
    lines = []
    for r in results:
        lines.append(f"- [{r['id']}] (dist={r['distance']:.3f}) {r['document'][:200]}")
    return "\n".join(lines)


@tool(
    name="memory_store",
    description="Store a text chunk into the vector memory for later retrieval.",
    parameters={
        "text": {"type": "string", "description": "Text to store"},
        "metadata_json": {"type": "string", "description": "Optional JSON metadata string, e.g. '{\"source\": \"web\"}'"},
    },
)
def memory_store(text: str, metadata_json: str = "{}") -> str:
    import json
    try:
        meta = json.loads(metadata_json)
    except Exception:
        meta = {}
    collection = _resolve_collection()
    doc_id = memory.store(text, metadata=meta, collection_name=collection)
    return f"Stored document {doc_id} in '{collection}' ({len(text)} chars)"
