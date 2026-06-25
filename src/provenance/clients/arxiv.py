import xml.etree.ElementTree as ET
from datetime import date, datetime

import httpx

from provenance.config import Settings, get_settings
from provenance.models import Paper, PaperSource

ARXIV_API_URL = "https://export.arxiv.org/api/query"
_ATOM_NS = "{http://www.w3.org/2005/Atom}"


class ArxivClient:
    """Async wrapper around the public ArXiv Atom API. No API key required."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    async def search(self, query: str, max_results: int | None = None) -> list[Paper]:
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": max_results or self._settings.arxiv_max_results,
            "sortBy": "relevance",
            "sortOrder": "descending",
        }
        async with httpx.AsyncClient(timeout=self._settings.http_timeout_seconds) as client:
            response = await client.get(ARXIV_API_URL, params=params)
            response.raise_for_status()
        return _parse_feed(response.text)


def _parse_feed(xml_text: str) -> list[Paper]:
    root = ET.fromstring(xml_text)
    return [_parse_entry(entry) for entry in root.findall(f"{_ATOM_NS}entry")]


def _parse_entry(entry: ET.Element) -> Paper:
    raw_id = entry.findtext(f"{_ATOM_NS}id", default="")
    arxiv_id = raw_id.rsplit("/", 1)[-1]
    title = " ".join(entry.findtext(f"{_ATOM_NS}title", default="").split())
    abstract = " ".join(entry.findtext(f"{_ATOM_NS}summary", default="").split())
    authors = [
        " ".join(author.findtext(f"{_ATOM_NS}name", default="").split())
        for author in entry.findall(f"{_ATOM_NS}author")
    ]

    return Paper(
        source=PaperSource.ARXIV,
        source_id=arxiv_id,
        title=title,
        authors=authors,
        abstract=abstract,
        url=raw_id,
        published=_parse_arxiv_date(entry.findtext(f"{_ATOM_NS}published", default="")),
    )


def _parse_arxiv_date(raw: str) -> date | None:
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%Y-%m-%dT%H:%M:%SZ").date()
    except ValueError:
        return None
