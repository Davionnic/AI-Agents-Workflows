import os
from typing import Optional

from crewai_tools import FirecrawlSearchTool, SerperDevTool


def create_web_search_tool(provider: Optional[str] = None):
    """Return a web search tool based on configured provider."""
    selected = (provider or os.getenv("WEB_SEARCH_PROVIDER", "firecrawl")).lower()

    if selected == "serper":
        return SerperDevTool()

    return FirecrawlSearchTool()
