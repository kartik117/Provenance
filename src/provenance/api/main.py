import asyncio
import logging

from fastapi import FastAPI

from provenance.clients import ArxivClient, SemanticScholarClient
from provenance.models import Paper

logger = logging.getLogger(__name__)

app = FastAPI(title="Provenance", version="0.1.0")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/search", response_model=list[Paper])
async def search(query: str, max_results: int = 10) -> list[Paper]:
    """Search ArXiv and Semantic Scholar concurrently and merge the results.

    Each source is queried independently so a rate limit or outage on one
    (Semantic Scholar's unauthenticated tier is easy to hit) doesn't fail
    the whole request.
    """
    results = await asyncio.gather(
        ArxivClient().search(query, max_results=max_results),
        SemanticScholarClient().search(query, max_results=max_results),
        return_exceptions=True,
    )

    papers: list[Paper] = []
    for result in results:
        if isinstance(result, BaseException):
            logger.warning("Search source failed: %s", result)
            continue
        papers.extend(result)

    return _dedupe(papers)


def _dedupe(papers: list[Paper]) -> list[Paper]:
    seen: set[str] = set()
    deduped: list[Paper] = []
    for paper in papers:
        if paper.dedup_key in seen:
            continue
        seen.add(paper.dedup_key)
        deduped.append(paper)
    return deduped
