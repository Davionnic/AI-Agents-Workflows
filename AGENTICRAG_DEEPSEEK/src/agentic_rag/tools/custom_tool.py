import uuid
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field, ConfigDict
from pypdf import PdfReader
import chromadb
from chromadb.utils import embedding_functions


class DocumentSearchToolInput(BaseModel):
    query: str = Field(..., description="Query to search the document.")


class DocumentSearchTool(BaseTool):
    name: str = "DocumentSearchTool"
    description: str = "Search the document for the given query."
    args_schema: Type[BaseModel] = DocumentSearchToolInput

    model_config = ConfigDict(extra="allow")

    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path
        self.collection_name = f"docs_{uuid.uuid4().hex[:8]}"

        self.client = chromadb.Client()
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_fn,
        )
        self._index_documents()

    def _load_pdf_text(self) -> str:
        reader = PdfReader(self.file_path)
        pages = []
        for page in reader.pages:
            text = page.extract_text() or ""
            pages.append(text)
        return "\n".join(pages)

    def _chunk_text(
        self, text: str, chunk_size: int = 1000, chunk_overlap: int = 200
    ) -> list[str]:
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start += chunk_size - chunk_overlap
        return chunks

    def _index_documents(self):
        text = self._load_pdf_text()
        chunks = self._chunk_text(text)
        if not chunks:
            raise ValueError("No chunks found in the document")

        ids = [f"chunk_{i}" for i in range(len(chunks))]
        self.collection.add(documents=chunks, ids=ids)

    def _run(self, query: str) -> str:
        results = self.collection.query(
            query_texts=[query],
            n_results=5,
        )
        documents = results.get("documents", [[]])[0]
        if not documents:
            return "No relevant information found in the document."

        formatted = ""
        for i, doc in enumerate(documents, start=1):
            formatted += f"Document {i}:\n{doc}\n____\n"
        return formatted.rstrip("____\n")
