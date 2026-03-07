"""
Tool: memory_search – semantic search over ChromaDB.
Tool: memory_store  – store a text chunk into ChromaDB.
"""

from agents.core.tool_registry import tool
from agents.core import memory


@tool(
    name="memory_search",
    description="Semantic search over the vector memory (ChromaDB). Returns the most relevant stored documents.",
    parameters={
        "query": {"type": "string", "description": "Natural-language search query"},
        "n_results": {"type": "integer", "description": "Number of results (default 5)"},
    },
)
def memory_search(query: str, n_results: int = 5) -> str:
    results = memory.query(query, n_results=int(n_results))
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
    doc_id = memory.store(text, metadata=meta)
    return f"Stored document {doc_id} ({len(text)} chars)"
