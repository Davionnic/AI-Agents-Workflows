#!/usr/bin/env python
"""CLI entry point for running the agentic RAG crew."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from agentic_rag.crew_factory import create_agents_and_tasks
from agentic_rag.tools.document_search import DocumentSearchTool


def run(query: str, document_path: str | None = None) -> str:
    document_tool = None
    if document_path:
        document_tool = DocumentSearchTool(file_path=document_path)

    crew = create_agents_and_tasks(document_tool=document_tool)
    return crew.kickoff(inputs={"query": query}).raw


if __name__ == "__main__":
    user_query = sys.argv[1] if len(sys.argv) > 1 else "What is agentic RAG?"
    doc = sys.argv[2] if len(sys.argv) > 2 else None
    print(run(user_query, doc))
