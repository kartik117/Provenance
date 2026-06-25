from fastapi import FastAPI

from provenance.agents import SearchAgent, dedupe
from provenance.models import Paper, ResearchResult
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


@app.get("/research", response_model=ResearchResult)
async def research(query: str, max_results: int = 10) -> ResearchResult:
    """Full pipeline: search -> filter -> synthesize -> verify a cited summary."""
    result = await _pipeline.ainvoke({"query": query, "max_results": max_results})
    return ResearchResult(query=query, summary=result["summary"], papers=result["filtered_papers"])
