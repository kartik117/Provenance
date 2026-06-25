from datetime import date

import httpx

from provenance.config import Settings, get_settings
from provenance.models import Paper, PaperSource

SEMANTIC_SCHOLAR_API_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
_FIELDS = "title,abstract,authors,url,publicationDate,citationCount"


class SemanticScholarClient:
    """Async wrapper around the Semantic Scholar Graph API. Works without a key at a lower rate limit."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    async def search(self, query: str, max_results: int | None = None) -> list[Paper]:
        params = {
            "query": query,
            "limit": max_results or self._settings.semantic_scholar_max_results,
            "fields": _FIELDS,
        }
        headers = (
            {"x-api-key": self._settings.semantic_scholar_api_key}
            if self._settings.semantic_scholar_api_key
            else {}
        )
        async with httpx.AsyncClient(timeout=self._settings.http_timeout_seconds) as client:
            response = await client.get(SEMANTIC_SCHOLAR_API_URL, params=params, headers=headers)
            response.raise_for_status()
        return [_parse_paper(item) for item in response.json().get("data", [])]


def _parse_paper(item: dict) -> Paper:
    authors = [author.get("name", "") for author in item.get("authors") or []]
    return Paper(
        source=PaperSource.SEMANTIC_SCHOLAR,
        source_id=item.get("paperId", ""),
        title=item.get("title") or "",
        authors=authors,
        abstract=item.get("abstract") or "",
        url=item.get("url") or "",
        published=_parse_iso_date(item.get("publicationDate")),
        citation_count=item.get("citationCount"),
    )


def _parse_iso_date(raw: str | None) -> date | None:
    if not raw:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return None
