# Provenance

A multi-agent research assistant that searches academic papers, filters them for relevance, synthesizes a summary, and verifies every claim against its cited source before showing it to you.

Most LLM research tools will cite a paper that doesn't actually say what they claim it says. Provenance runs a dedicated verification step over every citation, so the output is grounded in sources that were actually checked.

## How it works

```
query
  -> Search Agent          (ArXiv + Semantic Scholar)
  -> Filter Agent           (relevance scoring, dedup)
  -> Synthesis Agent        (LangGraph, summarizes findings)
  -> Citation Verification  (checks claim <-> paper alignment)
  -> grounded summary with verified citations
```

## Status

Early build — search clients are in place; the agent pipeline, evaluation suite, and UI are in progress. See open issues/commits for current state.

## Stack

LangGraph · FastAPI · Streamlit · Gemini · Chroma · PostgreSQL · RAGAS

## Local setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # add your GOOGLE_API_KEY
pytest
```

## License

MIT
