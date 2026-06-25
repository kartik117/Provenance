import httpx
import respx

from provenance.clients.semantic_scholar import SEMANTIC_SCHOLAR_API_URL, SemanticScholarClient
from provenance.models import PaperSource


@respx.mock
async def test_search_parses_papers(semantic_scholar_single_paper):
    respx.get(SEMANTIC_SCHOLAR_API_URL).mock(
        return_value=httpx.Response(200, json=semantic_scholar_single_paper)
    )

    papers = await SemanticScholarClient().search("transformers")

    assert len(papers) == 1
    paper = papers[0]
    assert paper.source == PaperSource.SEMANTIC_SCHOLAR
    assert paper.source_id == "abc123"
    assert paper.authors == ["Ashish Vaswani"]
    assert paper.citation_count == 100000
    assert paper.published.isoformat() == "2017-06-12"


@respx.mock
async def test_search_handles_missing_optional_fields():
    response = {"total": 1, "data": [{"paperId": "xyz", "title": "Untitled Draft"}]}
    respx.get(SEMANTIC_SCHOLAR_API_URL).mock(return_value=httpx.Response(200, json=response))

    papers = await SemanticScholarClient().search("draft paper")

    assert papers[0].authors == []
    assert papers[0].published is None
    assert papers[0].citation_count is None
