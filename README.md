# AI Agents & Workflows

Monorepo for AI agent projects and automated workflows built with [CrewAI](https://www.crewai.com/), [AG2](https://docs.ag2.ai/) (AutoGen), Streamlit, and related tooling.

Each project lives in its own top-level directory with its own dependencies, config, and README.

## Projects

| Project | Description |
|---------|-------------|
| [agentic-rag](./AGENTIC%20RAG/) | Agentic RAG with document search (Qdrant) and web fallback (Firecrawl / Serper), with a Streamlit chat UI |
| [agenticrag-deepseek](./AGENTICRAG_DEEPSEEK/) | Local Agentic RAG with DeepSeek R1 (Ollama), Chroma document search, and DuckDuckGo web fallback |
| [autogen-stock-analyst](./AUTOGEN%20STOCK%20ANALYST/) | Multi-agent stock analysis with AG2 + Groq (free tier), yfinance data, and local code execution |
| [yt-trend-analysis](./YT%20TREND%20ANALYSIS/) | Scrape YouTube channel transcripts via Bright Data and analyze trends with a CrewAI agent crew |
| [book-writer-flow](./BOOK%20WRITER%20FLOW/) | Research a topic and write a complete Markdown book with a concurrent CrewAI flow |

## How it works

### agentic-rag

```mermaid
flowchart TD
  pdf[Uploaded PDF] --> parse[MarkItDown]
  parse --> chunk["SemanticChunker with potion-base-8M"]
  chunk --> qdrant[In-memory Qdrant]
  question[User query] --> retriever[Retriever agent]
  qdrant --> doctool[DocumentSearchTool]
  doctool --> retriever
  retriever -->|"If docs are not enough"| web["Firecrawl or Serper web search"]
  web --> retriever
  retriever --> synth[Response synthesizer agent]
  synth --> answer[Final answer in Streamlit]
  llm["LLM: OpenAI gpt-4o-mini or Ollama llama3.2"] --> retriever
  llm --> synth
```

### agenticrag-deepseek

```mermaid
flowchart TD
  pdf[Uploaded PDF] --> extract[PyPDF extract text]
  extract --> chunk["Chunk size 1000, overlap 200"]
  chunk --> chroma["In-memory Chroma with all-MiniLM-L6-v2"]
  question[User query] --> retriever[Retriever agent]
  chroma --> doctool["DocumentSearchTool, top 5"]
  doctool --> retriever
  retriever -->|"If the PDF is not enough"| ddg["DuckDuckGo, max 5 results"]
  ddg --> retriever
  retriever --> synth[Response synthesizer agent]
  synth --> answer[Final answer in Streamlit]
  llm["Ollama deepseek-r1:7b"] --> retriever
  llm --> synth
```

### autogen-stock-analyst

```mermaid
flowchart TD
  task[Analysis request] --> planner[planner agent]
  planner --> engineer["engineer writes Python"]
  engineer --> executor["executor runs code in coding/"]
  executor -->|"On failure"| engineer
  executor -->|"On success"| writer[writer agent]
  writer --> report["Markdown report with charts and CSVs"]
  tools["yfinance, pandas, matplotlib"] --> executor
  llm["Groq llama-3.3-70b-versatile"] --> planner
  llm --> engineer
  llm --> writer
```

### yt-trend-analysis

```mermaid
flowchart TD
  urls[YouTube channel URLs] --> scrape[Bright Data scrape videos and transcripts]
  scrape --> files["Save transcripts/"]
  files --> analysis["Analysis agent with FileReadTool"]
  analysis --> report["Topics, trends, sentiment, keywords"]
  report --> synth[Response synthesizer agent]
  synth --> summary["Concise summary with recommendations"]
  llm["OpenAI gpt-4o or Ollama llama3.2"] --> analysis
  llm --> synth
```

### book-writer-flow

```mermaid
flowchart TD
  topic[Book topic] --> research[Book Research Agent]
  research --> search["Optional Bright Data web search"]
  search --> research
  research --> outlineWriter[Book Outline Writer]
  outlineWriter --> outline[Chapter outline]
  outline --> chapterResearch[Topic Researcher per chapter]
  chapterResearch --> chapterWriter[Senior Writer per chapter]
  chapterWriter --> book["Save Markdown book to outputs/"]
  note["Chapters are written concurrently"] --> chapterResearch
  llm["Ollama gemma3:4b or OpenAI gpt-4o-mini"] --> research
  llm --> outlineWriter
  llm --> chapterResearch
  llm --> chapterWriter
```

## Getting started

1. Clone the repo:
   ```bash
   git clone https://github.com/Davionnic/AI-Agents-Workflows.git
   cd AI-Agents-Workflows
   ```

2. Pick a project from the table above and follow its README.

3. Copy `.env.example` to `.env` inside that project and add your API keys.

## Adding a new project

1. Create a new directory at the repo root (e.g. `my-new-agent/`).
2. Add a `README.md` with setup and usage instructions.
3. Include a `.env.example` — never commit real secrets.
4. Update the **Projects** table in this file.

## Requirements

- Python 3.11+
- Git

Individual projects may require additional API keys or local services (e.g. Ollama, Groq). See each project's README.
