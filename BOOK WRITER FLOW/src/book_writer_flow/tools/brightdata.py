import os

import requests
from crewai.tools import BaseTool
from pydantic import Field


class BrightDataWebSearchTool(BaseTool):
    name: str = "Bright Data web search"
    description: str = "Search the web for current, factual information about a topic."
    timeout: int = Field(default=30, exclude=True)

    def _run(self, query: str) -> str:
        username = os.getenv("BRIGHTDATA_USERNAME")
        password = os.getenv("BRIGHTDATA_PASSWORD")
        if not username or not password:
            return "No live search credentials are configured. Use the model's existing knowledge."

        host = os.getenv("BRIGHTDATA_PROXY_HOST", "brd.superproxy.io")
        port = os.getenv("BRIGHTDATA_PROXY_PORT", "33335")
        proxy = f"http://{username}:{password}@{host}:{port}"
        response = requests.get(
            "https://www.google.com/search",
            params={"q": query},
            proxies={"http": proxy, "https": proxy},
            headers={"User-Agent": "book-writer-flow/0.1"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.text[:12000]