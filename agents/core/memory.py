"""
ChromaDB-backed vector memory for agents.
Supports storing & retrieving text chunks with metadata.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

import chromadb
from chromadb.api import ClientAPI

from agents.config import CHROMA_PERSIST_DIR, CHROMA_COLLECTION

if TYPE_CHECKING:
    pass  # ClientAPI already imported above for runtime use too

_chroma_client: ClientAPI | None = None


def _get_client() -> ClientAPI:
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    return _chroma_client


def get_collection(name: str = CHROMA_COLLECTION) -> chromadb.Collection:
    """Return (or create) a named ChromaDB collection."""
    return _get_client().get_or_create_collection(name=name)


def store(
    text: str,
    metadata: dict[str, Any] | None = None,
    collection_name: str = CHROMA_COLLECTION,
    doc_id: str | None = None,
) -> str:
    """Store a text chunk. Returns the document id."""
    coll = get_collection(collection_name)
    doc_id = doc_id or str(uuid.uuid4())
    coll.upsert(
        ids=[doc_id],
        documents=[text],
        metadatas=[metadata or {}],
    )
    return doc_id


def query(
    text: str,
    n_results: int = 5,
    collection_name: str = CHROMA_COLLECTION,
    where: dict | None = None,
) -> list[dict[str, Any]]:
    """Semantic search. Returns list of {id, document, metadata, distance}."""
    coll = get_collection(collection_name)
    kwargs: dict[str, Any] = {
        "query_texts": [text],
        "n_results": n_results,
    }
    if where:
        kwargs["where"] = where
    results = coll.query(**kwargs)

    ids = results["ids"][0]
    docs_outer = results.get("documents")
    meta_outer = results.get("metadatas")
    dist_outer = results.get("distances")
    documents = docs_outer[0] if docs_outer else []
    metadatas = meta_outer[0] if meta_outer else []
    distances = dist_outer[0] if dist_outer else []

    items: list[dict[str, Any]] = []
    for i in range(len(ids)):
        items.append(
            {
                "id": ids[i],
                "document": documents[i] if i < len(documents) else None,
                "metadata": metadatas[i] if i < len(metadatas) else {},
                "distance": distances[i] if i < len(distances) else None,
            }
        )
    return items


def list_collections() -> list[str]:
    return [c.name for c in _get_client().list_collections()]
