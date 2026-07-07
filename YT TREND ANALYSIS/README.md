# YouTube Trend Analysis

Streamlit app that scrapes YouTube channel transcripts with [Bright Data](https://brightdata.com/) and runs a two-agent CrewAI pipeline to surface topics, trends, sentiment, and actionable insights.

Part of the [AI Agents & Workflows](../) monorepo.

## Setup

```bash
cd "YT TREND ANALYSIS"
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env   # then fill in your keys
```

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `BRIGHT_DATA_API_KEY` | Yes | Bright Data API key for YouTube scraping |
| `OPENAI_API_KEY` | No* | OpenAI key for GPT-4o (default when set) |

\* Leave `OPENAI_API_KEY` empty to use Ollama locally (`ollama pull llama3.2`).

## Run

```bash
streamlit run app.py
```

## How it works

1. Enter YouTube channel URLs in the Streamlit UI.
2. Bright Data scrapes videos and formatted transcripts.
3. Transcripts are saved to `transcripts/` and passed to the agent crew.
4. **Analysis agent** reads transcripts and produces a structured report (topics, trends, sentiment, keywords).
5. **Response synthesizer agent** turns that report into a concise summary with recommendations.

Agent roles and tasks are defined in `config.yaml`.

## Project structure

```
YT TREND ANALYSIS/
├── app.py                  # Streamlit UI and CrewAI orchestration
├── brightdata_scrapper.py  # Bright Data API client
├── config.yaml             # Agent and task definitions
├── requirements.txt
├── .env.example
├── assets/                 # UI branding images
└── transcripts/            # Generated transcript files (gitignored)
```

## License

MIT
