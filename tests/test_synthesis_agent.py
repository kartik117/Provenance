from provenance.agents import SynthesisAgent
from provenance.models import Citation, Paper, PaperSource, ResearchSummary


def make_paper(source_id: str, title: str = "Test Paper") -> Paper:
    return Paper(source=PaperSource.ARXIV, source_id=source_id, title=title, url=f"https://example.com/{source_id}")


async def test_synthesis_agent_returns_synthesizer_output():
    papers = [make_paper("a1")]
    expected = ResearchSummary(overview="x", citations=[Citation(claim="y", source_ids=["a1"])])

    async def fake_synthesizer(query: str, papers: list[Paper]) -> ResearchSummary:
        assert query == "test query"
        assert [p.source_id for p in papers] == ["a1"]
        return expected

    agent = SynthesisAgent(synthesizer=fake_synthesizer)
    result = await agent.synthesize("test query", papers)

    assert result == expected


async def test_synthesis_agent_short_circuits_when_no_papers():
    async def fake_synthesizer(query: str, papers: list[Paper]) -> ResearchSummary:
        raise AssertionError("synthesizer should not be called when there are no papers")

    agent = SynthesisAgent(synthesizer=fake_synthesizer)
    result = await agent.synthesize("test query", [])

    assert "No relevant papers" in result.overview
