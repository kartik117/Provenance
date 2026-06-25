import httpx
import respx

from provenance.clients.arxiv import ARXIV_API_URL, ArxivClient
from provenance.models import PaperSource


@respx.mock
async def test_search_parses_entries_into_papers(arxiv_feed_single_entry):
    respx.get(ARXIV_API_URL).mock(return_value=httpx.Response(200, text=arxiv_feed_single_entry))

    papers = await ArxivClient().search("transformers")

    assert len(papers) == 1
    paper = papers[0]
    assert paper.source == PaperSource.ARXIV
    assert paper.source_id == "2301.00001v1"
    assert paper.title == "Attention Is All You Need Again"
    assert paper.abstract == "We revisit the transformer architecture and propose improvements."
    assert paper.authors == ["Jane Doe", "John Smith"]
    assert paper.published.isoformat() == "2023-01-01"
    assert paper.url == "http://arxiv.org/abs/2301.00001v1"


@respx.mock
async def test_search_returns_empty_list_for_no_results():
    empty_feed = '<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"></feed>'
    respx.get(ARXIV_API_URL).mock(return_value=httpx.Response(200, text=empty_feed))

    papers = await ArxivClient().search("a query with no matches")

    assert papers == []
