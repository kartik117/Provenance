import httpx
import respx

from provenance.agents import SearchAgent
from provenance.clients.arxiv import ARXIV_API_URL, ArxivClient
from provenance.clients.semantic_scholar import SEMANTIC_SCHOLAR_API_URL, SemanticScholarClient


@respx.mock
async def test_search_merges_results_from_both_sources(
    arxiv_feed_single_entry, semantic_scholar_single_paper
):
    respx.get(ARXIV_API_URL).mock(return_value=httpx.Response(200, text=arxiv_feed_single_entry))
    respx.get(SEMANTIC_SCHOLAR_API_URL).mock(
        return_value=httpx.Response(200, json=semantic_scholar_single_paper)
    )

    papers = await SearchAgent(ArxivClient(), SemanticScholarClient()).search("transformers")

    assert {p.source.value for p in papers} == {"arxiv", "semantic_scholar"}


@respx.mock
async def test_search_continues_when_one_source_fails(arxiv_feed_single_entry):
    respx.get(ARXIV_API_URL).mock(return_value=httpx.Response(200, text=arxiv_feed_single_entry))
    respx.get(SEMANTIC_SCHOLAR_API_URL).mock(return_value=httpx.Response(429))

    papers = await SearchAgent(ArxivClient(), SemanticScholarClient()).search("transformers")

    assert len(papers) == 1
    assert papers[0].source.value == "arxiv"
