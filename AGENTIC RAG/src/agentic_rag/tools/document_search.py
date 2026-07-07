import os
from typing import Type

from chonkie import SemanticChunker
from crewai.tools import BaseTool
from markitdown import MarkItDown
from pydantic import BaseModel, ConfigDict, Field
from qdrant_client import QdrantClient


class DocumentSearchToolInput(BaseModel):
    query: str = Field(..., description="Query to search the document.")


class DocumentSearchTool(BaseTool):
    name: str = "DocumentSearchTool"
    description: str = (
        "Search the uploaded document for relevant passages. "
        "Use this tool first before web search."
    )
    args_schema: Type[BaseModel] = DocumentSearchToolInput

    model_config = ConfigDict(extra="allow")

    def __init__(self, file_path: str, collection_name: str = "document_collection"):
        super().__init__()
        self.file_path = file_path
        self.collection_name = collection_name
        self.client = QdrantClient(":memory:")
        self._process_document()

    def _extract_text(self) -> str:
        md = MarkItDown()
        result = md.convert(self.file_path)
        return result.text_content or ""

    def _create_chunks(self, raw_text: str) -> list:
        if not raw_text.strip():
            return []

        chunker = SemanticChunker(
            embedding_model="minishlab/potion-base-8M",
            threshold=0.5,
            chunk_size=512,
            min_sentences=1,
        )
        return chunker.chunk(raw_text)

    def _process_document(self) -> None:
        raw_text = self._extract_text()
        chunks = self._create_chunks(raw_text)

        if not chunks:
            return

        docs = [chunk.text for chunk in chunks]
        metadata = [{"source": os.path.basename(self.file_path)} for _ in chunks]
        ids = list(range(len(chunks)))

        self.client.add(
            collection_name=self.collection_name,
            documents=docs,
            metadata=metadata,
            ids=ids,
        )

    def _run(self, query: str) -> str:
        if not query.strip():
            return "No query provided."

        try:
            relevant_chunks = self.client.query(
                collection_name=self.collection_name,
                query_text=query,
            )
        except Exception as exc:
            return f"Document search failed: {exc}"

        if not relevant_chunks:
            return "No relevant passages found in the document."

        docs = [chunk.document for chunk in relevant_chunks]
        return "\n___\n".join(docs)
