import httpx
import respx
from fastapi.testclient import TestClient

from provenance.api.main import app
from provenance.clients.arxiv import ARXIV_API_URL
from provenance.clients.semantic_scholar import SEMANTIC_SCHOLAR_API_URL

client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@respx.mock
def test_search_merges_results_from_both_sources(
    arxiv_feed_single_entry, semantic_scholar_single_paper
):
    respx.get(ARXIV_API_URL).mock(return_value=httpx.Response(200, text=arxiv_feed_single_entry))
    respx.get(SEMANTIC_SCHOLAR_API_URL).mock(
        return_value=httpx.Response(200, json=semantic_scholar_single_paper)
    )

    response = client.get("/search", params={"query": "transformers"})

    assert response.status_code == 200
    papers = response.json()
    assert len(papers) == 2
    assert {p["source"] for p in papers} == {"arxiv", "semantic_scholar"}


@respx.mock
def test_search_still_returns_results_when_one_source_fails(arxiv_feed_single_entry):
    respx.get(ARXIV_API_URL).mock(return_value=httpx.Response(200, text=arxiv_feed_single_entry))
    respx.get(SEMANTIC_SCHOLAR_API_URL).mock(return_value=httpx.Response(429))

    response = client.get("/search", params={"query": "transformers"})

    assert response.status_code == 200
    papers = response.json()
    assert len(papers) == 1
    assert papers[0]["source"] == "arxiv"
