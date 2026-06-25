from provenance.agents import CitationVerificationAgent
from provenance.models import Citation, Paper, PaperSource, ResearchSummary


def make_paper(source_id: str, abstract: str = "") -> Paper:
    return Paper(
        source=PaperSource.ARXIV,
        source_id=source_id,
        title=f"Paper {source_id}",
        abstract=abstract,
        url=f"https://example.com/{source_id}",
    )


async def test_verify_marks_citations_using_verifier_verdicts():
    papers = [make_paper("a1"), make_paper("a2")]
    summary = ResearchSummary(
        overview="x",
        citations=[
            Citation(claim="supported claim", source_ids=["a1"]),
            Citation(claim="unsupported claim", source_ids=["a2"]),
        ],
    )

    async def fake_verifier(citations, papers_by_id):
        assert papers_by_id.keys() == {"a1", "a2"}
        return {0: True, 1: False}

    agent = CitationVerificationAgent(verifier=fake_verifier)
    result = await agent.verify(summary, papers)

    assert result.citations[0].verified is True
    assert result.citations[1].verified is False


async def test_verify_defaults_missing_verdicts_to_false():
    papers = [make_paper("a1")]
    summary = ResearchSummary(overview="x", citations=[Citation(claim="claim", source_ids=["a1"])])

    async def fake_verifier(citations, papers_by_id):
        return {}

    agent = CitationVerificationAgent(verifier=fake_verifier)
    result = await agent.verify(summary, papers)

    assert result.citations[0].verified is False


async def test_verify_short_circuits_when_no_citations():
    summary = ResearchSummary(overview="x", citations=[])

    async def fake_verifier(citations, papers_by_id):
        raise AssertionError("verifier should not be called with no citations")

    agent = CitationVerificationAgent(verifier=fake_verifier)
    result = await agent.verify(summary, [])

    assert result == summary
