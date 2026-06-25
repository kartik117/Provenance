from provenance.models import Paper, PaperSource, ResearchSummary
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


async def test_pipeline_threads_state_through_search_filter_synthesize():
    paper = Paper(source=PaperSource.ARXIV, source_id="a1", title="Test Paper", url="https://example.com/a1")
    summary = ResearchSummary(overview="Test overview")

    search_agent = FakeSearchAgent([paper])
    filter_agent = FakeFilterAgent([paper])
    synthesis_agent = FakeSynthesisAgent(summary)

    pipeline = build_pipeline(search_agent, filter_agent, synthesis_agent)
    result = await pipeline.ainvoke({"query": "test query", "max_results": 5})

    assert result["papers"] == [paper]
    assert result["filtered_papers"] == [paper]
    assert result["summary"] == summary
    assert filter_agent.received_papers == [paper]
    assert synthesis_agent.received_papers == [paper]
