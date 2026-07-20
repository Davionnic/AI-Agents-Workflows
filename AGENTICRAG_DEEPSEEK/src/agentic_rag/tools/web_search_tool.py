from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from duckduckgo_search import DDGS


class WebSearchToolInput(BaseModel):
    query: str = Field(..., description="Search query for the web.")


class WebSearchTool(BaseTool):
    name: str = "WebSearchTool"
    description: str = (
        "Search the web for information. "
        "Use this when the document search tool cannot answer the query."
    )
    args_schema: Type[BaseModel] = WebSearchToolInput

    def _run(self, query: str) -> str:
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=5))
        except Exception as e:
            return f"Web search failed: {e}"

        if not results:
            return "No web results found."

        formatted = ""
        for i, item in enumerate(results, start=1):
            title = item.get("title", "")
            href = item.get("href", "")
            body = item.get("body", "")
            formatted += f"{i}. {title}\n{href}\n{body}\n____\n"

        return formatted.rstrip("____\n")
