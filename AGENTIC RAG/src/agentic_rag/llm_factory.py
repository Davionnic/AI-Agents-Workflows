import os
from typing import Optional

from crewai import LLM


def create_llm(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    base_url: Optional[str] = None,
) -> LLM | None:
    """Create an LLM instance. Returns None to use CrewAI defaults (OpenAI)."""
    selected = (provider or os.getenv("LLM_PROVIDER", "openai")).lower()

    if selected == "ollama":
        ollama_model = model or os.getenv("OLLAMA_MODEL", "llama3.2")
        ollama_base = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        return LLM(model=f"ollama/{ollama_model}", base_url=ollama_base)

    openai_model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    return LLM(model=openai_model)
