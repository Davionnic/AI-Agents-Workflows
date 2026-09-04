# Book Writer Flow

Standalone CrewAI flow inspired by [patchy631/ai-engineering-hub/book-writer-flow](https://github.com/patchy631/ai-engineering-hub/tree/main/book-writer-flow). It researches a topic, generates a chapter outline, writes chapters concurrently, and saves a Markdown book.

## Features

- Outline research agent and outline writer agent
- Parallel chapter research and writing
- Local Ollama support with Gemma 3, or OpenAI support
- Optional Bright Data proxy-backed web search
- Streamlit UI and command-line runner
- Offline demo mode for validating the project without credentials

## Setup

```powershell
cd "BOOK WRITER FLOW"
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
Copy-Item .env.example .env
```

For local generation, install [Ollama](https://ollama.com/), run it, and pull the model:

```powershell
ollama pull gemma3:4b
```

For OpenAI, set `LLM_PROVIDER=openai` and `OPENAI_API_KEY` in `.env`. Bright Data credentials are optional; without them, the agents use the model's existing knowledge.

## Run

Generate a sample without external services:

```powershell
python -m book_writer_flow.main --demo
```

Generate a real book:

```powershell
python -m book_writer_flow.main "Astronomy in 2025" --chapters 5
```

Launch the UI:

```powershell
streamlit run app.py
```

Generated books are written to `outputs/`.

## Project structure

```
BOOK WRITER FLOW/
├── app.py
├── requirements.txt
├── pyproject.toml
├── .env.example
├── outputs/
└── src/book_writer_flow/
    ├── flow.py
    ├── llm_factory.py
    ├── main.py
    ├── models.py
    └── tools/brightdata.py
```

## License

MIT