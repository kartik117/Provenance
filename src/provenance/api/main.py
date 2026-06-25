from fastapi import FastAPI

from provenance.agents import SearchAgent, dedupe
from provenance.models import Paper, ResearchSummary
from provenance.pipeline import build_pipeline

app = FastAPI(title="Provenance", version="0.1.0")
_pipeline = build_pipeline()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/search", response_model=list[Paper])
async def search(query: str, max_results: int = 10) -> list[Paper]:
    """Raw merged search results, with no relevance filtering or synthesis."""
    papers = await SearchAgent().search(query, max_results=max_results)
    return dedupe(papers)


@app.get("/research", response_model=ResearchSummary)
async def research(query: str, max_results: int = 10) -> ResearchSummary:
    """Full pipeline: search -> filter -> synthesize a cited summary."""
    result = await _pipeline.ainvoke({"query": query, "max_results": max_results})
    return result["summary"]
