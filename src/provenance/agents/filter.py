from collections.abc import Awaitable, Callable

from pydantic import BaseModel, Field

from provenance.clients import get_chat_model
from provenance.models import Paper

DEFAULT_MIN_RELEVANCE = 0.4
DEFAULT_MAX_PAPERS = 10

_RELEVANCE_PROMPT = """You are scoring how relevant each paper is to a research query.

Query: {query}

For each paper below, give a relevance score from 0.0 (irrelevant) to 1.0 \
(directly helps answer the query), based on its title and abstract. Return a \
score for every paper listed, identified by its source_id.

{papers_block}
"""


class RelevanceScore(BaseModel):
    source_id: str
    score: float = Field(ge=0.0, le=1.0)


class RelevanceScores(BaseModel):
    scores: list[RelevanceScore]


Scorer = Callable[[str, list[Paper]], Awaitable[dict[str, float]]]


async def score_relevance_with_llm(query: str, papers: list[Paper]) -> dict[str, float]:
    """Default scorer: one batched structured-output call to Gemini."""
    papers_block = "\n\n".join(
        f"[{paper.source_id}] {paper.title}\n{paper.abstract[:500]}" for paper in papers
    )
    prompt = _RELEVANCE_PROMPT.format(query=query, papers_block=papers_block)
    structured_llm = get_chat_model().with_structured_output(RelevanceScores)
    result: RelevanceScores = await structured_llm.ainvoke(prompt)
    return {item.source_id: item.score for item in result.scores}


def dedupe(papers: list[Paper]) -> list[Paper]:
    seen: set[str] = set()
    deduped: list[Paper] = []
    for paper in papers:
        if paper.dedup_key in seen:
            continue
        seen.add(paper.dedup_key)
        deduped.append(paper)
    return deduped


class FilterAgent:
    """Dedupes search results and ranks what's left by relevance to the query."""

    def __init__(
        self,
        scorer: Scorer = score_relevance_with_llm,
        min_relevance: float = DEFAULT_MIN_RELEVANCE,
        max_papers: int = DEFAULT_MAX_PAPERS,
    ) -> None:
        self._scorer = scorer
        self._min_relevance = min_relevance
        self._max_papers = max_papers

    async def filter(self, query: str, papers: list[Paper]) -> list[Paper]:
        deduped = dedupe(papers)
        if not deduped:
            return []

        scores = await self._scorer(query, deduped)
        for paper in deduped:
            paper.relevance_score = scores.get(paper.source_id, 0.0)

        relevant = [p for p in deduped if (p.relevance_score or 0.0) >= self._min_relevance]
        relevant.sort(key=lambda p: p.relevance_score or 0.0, reverse=True)
        return relevant[: self._max_papers]
