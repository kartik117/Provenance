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

All four agents are wired into a single LangGraph `StateGraph` (`src/provenance/pipeline.py`), exposed via FastAPI's `/research` endpoint and rendered in a Streamlit UI that shows a verified/unverified badge on every claim.

## Status

Core pipeline, API, UI, RAGAS evaluation, Postgres session history, and Docker packaging are all working end-to-end against live ArXiv/Semantic Scholar/Gemini.

## Stack

LangGraph · FastAPI · Streamlit · Gemini · PostgreSQL · RAGAS

## Local setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # add your GOOGLE_API_KEY
pytest
```

## Running it

**Docker (recommended — runs Postgres, the API, and the UI together):**

```bash
cp .env.example .env   # add your GOOGLE_API_KEY
docker compose up --build
```

API on `localhost:8000`, UI on `localhost:8501`.

**Without Docker:**

```bash
source .venv/bin/activate
uvicorn provenance.api.main:app --port 8000 &
streamlit run app/streamlit_app.py
```

Needs a running Postgres matching `DATABASE_URL` in `.env` (e.g. `brew services start postgresql@16` and create the `provenance` role/db) — if it's not reachable, `/research` still works, it just skips persistence.

Either way, open the **Research** tab and ask a question like "reducing hallucination in retrieval augmented generation."

Note: Gemini's free tier caps each model at **20 requests/day**, and `/research` costs 3 calls (filter, synthesize, verify) per query — so expect roughly 6 free queries/day on a given model before it 429s.

Every `/research` call is saved to Postgres and browsable in the **History** tab.

## Evaluation

`eval/run_eval.py` runs the full pipeline over a small set of representative queries and scores each result with RAGAS **faithfulness** (does the synthesized overview actually follow from the retrieved abstracts?) and **context precision** (were the retrieved papers relevant?).

```bash
pip install -e ".[eval]"
python -m eval.run_eval
```

Results are written to `eval/results.json` (gitignored — it's a generated, point-in-time run, not a static benchmark). The query set is intentionally small (3 queries) because each one costs ~6 LLM calls between the pipeline and RAGAS's own scoring, and the free tier's 20-requests/day cap is shared with everything else hitting that model that day; running the full set in one sitting is easy to throttle out of.

On the one query that completed before hitting that limit during development, faithfulness scored **0.92** — consistent with the pipeline's design (synthesis is grounded only in retrieved abstracts, and citation verification catches claims that overreach). A full multi-query run needs either a fresh day's quota or a billing-enabled key.

## License

MIT
