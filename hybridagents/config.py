"""
Central configuration for the agentic framework.
All secrets and tunables are loaded from .env (see .env.example).
"""

import os
from dotenv import load_dotenv

load_dotenv()  # reads .env from project root

# ── Provider / model defaults ─────────────────────────────────
DEFAULT_PROVIDER = os.getenv("DEFAULT_PROVIDER", "ollama")  # "ollama" | "aifoundry" | "ghcopilot"
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "phi4")
DEFAULT_TEMPERATURE: float | None = (
    float(v) if (v := os.getenv("DEFAULT_TEMPERATURE", "")) else None
)

# ── Ollama (local inference) ──────────────────────────────────
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_NUM_CTX = int(os.getenv("OLLAMA_NUM_CTX", "8192"))

# ── Azure AI Foundry ─────────────────────────────────────────
AZURE_FOUNDRY_ENDPOINT = os.getenv("AZURE_FOUNDRY_ENDPOINT", "")
AZURE_FOUNDRY_API_KEY = os.getenv("AZURE_FOUNDRY_API_KEY", "")
AZURE_FOUNDRY_MODEL = os.getenv("AZURE_FOUNDRY_MODEL", "gpt-4o")

# ── GitHub Copilot (via Copilot SDK) ─────────────────────────
GHCOPILOT_MODEL = os.getenv("GHCOPILOT_MODEL", "gpt-4.1")
GHCOPILOT_CLI_URL = os.getenv("GHCOPILOT_CLI_URL", "")  # e.g. "localhost:4321" for external CLI

# ── ChromaDB ───────────────────────────────────────────────────
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./agents/chroma_data")
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "agent_memory")

# ── Agent loop ─────────────────────────────────────────────────
MAX_LOOP_ITERATIONS = int(os.getenv("MAX_LOOP_ITERATIONS", "50"))
VERBOSE = os.getenv("VERBOSE", "true").lower() in ("1", "true", "yes")
