# Sample Knowledge Document

This folder holds documents you can index with Agentic RAG.

## What is Agentic RAG?

Agentic RAG combines retrieval-augmented generation with autonomous AI agents. Instead of a fixed retrieve-then-generate pipeline, agents decide:

1. Which tool to use (document search vs web search)
2. Whether retrieved context is sufficient
3. How to synthesize a final answer

## DSPy Overview

DSPy is a framework for programming language models rather than prompting them. Key concepts:

- **Signatures**: Define input/output behavior declaratively
- **Modules**: Reusable LM-powered components (like PyTorch modules)
- **Optimizers**: Automatically tune prompts and weights (e.g., BootstrapFewShot, MIPRO)

DSPy treats prompts as parameters that can be optimized, making LM pipelines more reliable and maintainable.

## CrewAI Overview

CrewAI orchestrates role-playing AI agents that collaborate on tasks:

- **Agents** have roles, goals, and tools
- **Tasks** define work units with expected outputs
- **Crews** coordinate agents in sequential or hierarchical processes

This project uses a sequential crew: retrieve first, then synthesize.

## Usage Tips

- Upload a PDF in the Streamlit sidebar, or pass a file path to the CLI
- Ask specific questions for best retrieval results
- Use Ollama for fully local inference (no OpenAI key needed)
- Use Firecrawl or Serper for web fallback when docs lack the answer
