from provenance.agents.filter import FilterAgent, dedupe
from provenance.models import Paper, PaperSource


def make_paper(source_id: str, title: str, source: PaperSource = PaperSource.ARXIV) -> Paper:
    return Paper(source=source, source_id=source_id, title=title, url=f"https://example.com/{source_id}")


def test_dedupe_drops_same_title_from_different_sources():
    papers = [
        make_paper("a1", "Attention Is All You Need", source=PaperSource.ARXIV),
        make_paper("s1", "attention is all you need", source=PaperSource.SEMANTIC_SCHOLAR),
        make_paper("a2", "A Different Paper"),
    ]

    deduped = dedupe(papers)

    assert [p.source_id for p in deduped] == ["a1", "a2"]


async def test_filter_agent_ranks_by_relevance_and_drops_low_scores():
    papers = [
        make_paper("a1", "Highly Relevant Paper"),
        make_paper("a2", "Somewhat Relevant Paper"),
        make_paper("a3", "Irrelevant Paper"),
    ]

    async def fake_scorer(query: str, papers: list[Paper]) -> dict[str, float]:
        return {"a1": 0.9, "a2": 0.5, "a3": 0.1}

    agent = FilterAgent(scorer=fake_scorer, min_relevance=0.4, max_papers=10)
    result = await agent.filter("test query", papers)

    assert [p.source_id for p in result] == ["a1", "a2"]
    assert result[0].relevance_score == 0.9


async def test_filter_agent_caps_results_to_max_papers():
    papers = [make_paper(f"a{i}", f"Paper {i}") for i in range(5)]

    async def fake_scorer(query: str, papers: list[Paper]) -> dict[str, float]:
        return {p.source_id: 1.0 for p in papers}

    agent = FilterAgent(scorer=fake_scorer, min_relevance=0.0, max_papers=2)
    result = await agent.filter("test query", papers)

    assert len(result) == 2


async def test_filter_agent_returns_empty_list_for_no_papers():
    async def fake_scorer(query: str, papers: list[Paper]) -> dict[str, float]:
        raise AssertionError("scorer should not be called when there are no papers")

    agent = FilterAgent(scorer=fake_scorer)
    result = await agent.filter("test query", [])

    assert result == []
