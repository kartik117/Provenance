from provenance.models import Citation, Paper, PaperSource, ResearchSummary
from provenance.pipeline import build_pipeline


class FakeSearchAgent:
    def __init__(self, papers: list[Paper]) -> None:
        self._papers = papers

    async def search(self, query: str, max_results: int = 10) -> list[Paper]:
        return self._papers


class FakeFilterAgent:
    def __init__(self, filtered: list[Paper]) -> None:
        self._filtered = filtered
        self.received_papers: list[Paper] | None = None

    async def filter(self, query: str, papers: list[Paper]) -> list[Paper]:
        self.received_papers = papers
        return self._filtered


class FakeSynthesisAgent:
    def __init__(self, summary: ResearchSummary) -> None:
        self._summary = summary
        self.received_papers: list[Paper] | None = None

    async def synthesize(self, query: str, papers: list[Paper]) -> ResearchSummary:
        self.received_papers = papers
        return self._summary


class FakeCitationVerificationAgent:
    def __init__(self, verified_summary: ResearchSummary) -> None:
        self._verified_summary = verified_summary
        self.received_summary: ResearchSummary | None = None
        self.received_papers: list[Paper] | None = None

    async def verify(self, summary: ResearchSummary, papers: list[Paper]) -> ResearchSummary:
        self.received_summary = summary
        self.received_papers = papers
        return self._verified_summary


async def test_pipeline_threads_state_through_all_four_stages():
    paper = Paper(source=PaperSource.ARXIV, source_id="a1", title="Test Paper", url="https://example.com/a1")
    draft_summary = ResearchSummary(overview="Draft", citations=[Citation(claim="x", source_ids=["a1"])])
    verified_summary = ResearchSummary(
        overview="Draft", citations=[Citation(claim="x", source_ids=["a1"], verified=True)]
    )

    search_agent = FakeSearchAgent([paper])
    filter_agent = FakeFilterAgent([paper])
    synthesis_agent = FakeSynthesisAgent(draft_summary)
    citation_verification_agent = FakeCitationVerificationAgent(verified_summary)

    pipeline = build_pipeline(search_agent, filter_agent, synthesis_agent, citation_verification_agent)
    result = await pipeline.ainvoke({"query": "test query", "max_results": 5})

    assert result["papers"] == [paper]
    assert result["filtered_papers"] == [paper]
    assert result["summary"] == verified_summary
    assert filter_agent.received_papers == [paper]
    assert synthesis_agent.received_papers == [paper]
    assert citation_verification_agent.received_summary == draft_summary
    assert citation_verification_agent.received_papers == [paper]
