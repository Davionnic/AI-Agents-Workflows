# Agentic RAG (DeepSeek)

Local **Agentic RAG** built with [CrewAI](https://docs.crewai.com/) and [Streamlit](https://streamlit.io/). Uses **Ollama DeepSeek R1**, **Chroma** for document search, and **DuckDuckGo** for web fallback — no cloud API keys required.

Part of the [AI Agents & Workflows](../) monorepo.

## Features

- **Two-agent crew**: retriever + response synthesizer
- **Document search**: PDF indexing with Chroma + SentenceTransformers
- **Web fallback**: DuckDuckGo when the PDF does not answer the query
- **Local LLM**: Ollama `deepseek-r1:7b`

## Prerequisites

- Python 3.11+
- [Ollama](https://ollama.com/) running on `http://localhost:11434`
- Model: `ollama pull deepseek-r1:7b`

## Setup

```bash
cd AGENTICRAG_DEEPSEEK
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

## Run

```bash
streamlit run app_deep_seek.py
```

## How it works

1. Upload a PDF in the sidebar (optional).
2. The PDF is chunked and indexed in an in-memory Chroma collection.
3. The **retriever agent** searches the document first, then DuckDuckGo if needed.
4. The **synthesizer agent** returns a concise final answer.

## Project structure

```
AGENTICRAG_DEEPSEEK/
├── app_deep_seek.py              # Streamlit UI
├── requirements.txt
├── .env.example
└── src/agentic_rag/tools/
    ├── custom_tool.py            # PDF → Chroma document search
    └── web_search_tool.py        # DuckDuckGo web search
```

## License

MIT
