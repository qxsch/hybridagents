"""
Tool: read_file  – read a file from disk.
Tool: write_file – write content to a file on disk.
Tool: list_dir   – list directory contents.
"""

import os
from agents.core.tool_registry import tool


@tool(
    name="read_file",
    description="Read the contents of a file from disk.",
    parameters={
        "path": {"type": "string", "description": "File path to read"},
    },
)
def read_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        if len(content) > 10_000:
            return content[:10_000] + f"\n... [truncated, total {len(content)} chars]"
        return content
    except Exception as exc:
        return f"Error reading file: {exc}"


@tool(
    name="write_file",
    description="Write content to a file on disk. Creates directories if needed.",
    parameters={
        "path": {"type": "string", "description": "File path to write"},
        "content": {"type": "string", "description": "Content to write"},
    },
)
def write_file(path: str, content: str) -> str:
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Written {len(content)} chars to {path}"
    except Exception as exc:
        return f"Error writing file: {exc}"


@tool(
    name="list_dir",
    description="List the contents of a directory.",
    parameters={
        "path": {"type": "string", "description": "Directory path to list"},
    },
)
def list_dir(path: str) -> str:
    try:
        entries = os.listdir(path)
        if not entries:
            return "(empty directory)"
        return "\n".join(sorted(entries))
    except Exception as exc:
        return f"Error listing directory: {exc}"
