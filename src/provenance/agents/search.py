import asyncio
import logging

from provenance.clients import ArxivClient, SemanticScholarClient
from provenance.models import Paper

logger = logging.getLogger(__name__)


class SearchAgent:
    """Queries ArXiv and Semantic Scholar concurrently.

    Each source is queried independently so a rate limit or outage on one
    (Semantic Scholar's unauthenticated tier is easy to hit) doesn't fail
    the whole search.
    """

    def __init__(
        self,
        arxiv: ArxivClient | None = None,
        semantic_scholar: SemanticScholarClient | None = None,
    ) -> None:
        self._arxiv = arxiv or ArxivClient()
        self._semantic_scholar = semantic_scholar or SemanticScholarClient()

    async def search(self, query: str, max_results: int = 10) -> list[Paper]:
        results = await asyncio.gather(
            self._arxiv.search(query, max_results=max_results),
            self._semantic_scholar.search(query, max_results=max_results),
            return_exceptions=True,
        )

        papers: list[Paper] = []
        for result in results:
            if isinstance(result, BaseException):
                logger.warning("Search source failed: %s", result)
                continue
            papers.extend(result)
        return papers
