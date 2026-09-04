import os

from crewai import LLM


def create_llm() -> LLM:
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()
    if provider == "openai":
        return LLM(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    return LLM(
        model=f"ollama/{os.getenv('OLLAMA_MODEL', 'gemma3:4b')}",
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    )