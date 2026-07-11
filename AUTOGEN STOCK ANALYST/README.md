# AutoGen Stock Analyst

Multi-agent stock analysis powered by [AG2](https://docs.ag2.ai/) (AutoGen) and [Groq](https://console.groq.com/) free-tier LLMs. Agents plan the analysis, write Python (yfinance / pandas / matplotlib), execute it locally, and produce a Markdown report.

A free remake of the [ai-engineering-hub autogen-stock-analyst](https://github.com/patchy631/ai-engineering-hub/tree/main/autogen-stock-analyst) demo (Groq instead of Qualcomm Cloud AI / Imagine SDK).

Part of the [AI Agents & Workflows](../) monorepo.

## Agents

| Agent | Role |
|--------|------|
| `planner` | Breaks the request into analysis steps |
| `engineer` | Writes Python (yfinance / pandas / matplotlib) |
| `executor` | Runs the code in `coding/` |
| `writer` | Produces a Markdown report |

## Setup

```bash
cd "AUTOGEN STOCK ANALYST"
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
| `GROQ_API_KEY` | Yes | Free key from [console.groq.com/keys](https://console.groq.com/keys) |
| `GROQ_MODEL` | No | Defaults to `llama-3.3-70b-versatile` |

## Run

Default NVDA demo:

```bash
python main.py
```

By ticker:

```bash
python main.py --ticker AAPL --period 6mo --save
```

Custom task:

```bash
python main.py "Compare TSLA and F over the last year; plot both closes normalized to 100."
```

Outputs land in:

- `coding/data/` — CSVs
- `coding/figures/` — charts
- `coding/reports/` — saved Markdown (with `--save`)

## Project structure

```
AUTOGEN STOCK ANALYST/
├── main.py                     # CLI entry point
├── requirements.txt
├── .env.example
├── coding/                     # Generated code, data, figures, reports (gitignored)
└── stock_analyst/
    ├── config.py               # Groq LLM config
    └── team.py                 # Agent team + group chat
```

## Notes

- Groq free tier has rate limits; if you hit them, wait a minute and retry.
- Analysis is educational only — not investment advice.
- Generated code runs on your machine via AG2's local executor.

## License

MIT
