"""Groq LLM configuration for AG2 agents."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root (override=True so a leftover shell/system
# GROQ_API_KEY placeholder does not block the real key in .env)
_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT / ".env", override=True)

DEFAULT_MODEL = "llama-3.3-70b-versatile"


def get_groq_api_key() -> str:
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key or api_key == "your_groq_api_key_here":
        raise RuntimeError(
            "GROQ_API_KEY is missing. Copy .env.example to .env and add a free key from "
            "https://console.groq.com/keys"
        )
    return api_key


def get_llm_config() -> dict:
    """Return AG2 llm_config dict for Groq."""
    model = os.getenv("GROQ_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    return {
        "config_list": [
            {
                "model": model,
                "api_key": get_groq_api_key(),
                "api_type": "groq",
            }
        ],
        "temperature": 0.2,
        "timeout": 120,
    }
