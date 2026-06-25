import pytest
from sqlalchemy.ext.asyncio import create_async_engine

from provenance.models import Citation, Paper, PaperSource, ResearchResult, ResearchSummary
from provenance.storage import SessionRepository, init_models, session_factory


@pytest.fixture
async def repository() -> SessionRepository:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    await init_models(engine)
    return SessionRepository(session_factory(engine))


def make_result(query: str = "test query") -> ResearchResult:
    paper = Paper(source=PaperSource.ARXIV, source_id="a1", title="Test Paper", url="https://example.com/a1")
    summary = ResearchSummary(overview="x", citations=[Citation(claim="y", source_ids=["a1"], verified=True)])
    return ResearchResult(query=query, summary=summary, papers=[paper])


async def test_save_then_get_round_trips_the_result(repository: SessionRepository):
    result = make_result()

    session_id = await repository.save(result)
    record = await repository.get(session_id)

    assert record is not None
    assert record.query == "test query"
    assert record.summary_json["overview"] == "x"
    assert record.papers_json[0]["source_id"] == "a1"


async def test_get_returns_none_for_missing_id(repository: SessionRepository):
    record = await repository.get(999)

    assert record is None


async def test_list_recent_orders_most_recent_first(repository: SessionRepository):
    await repository.save(make_result("first query"))
    await repository.save(make_result("second query"))

    records = await repository.list_recent()

    assert [r.query for r in records] == ["second query", "first query"]


async def test_list_recent_respects_limit(repository: SessionRepository):
    for i in range(5):
        await repository.save(make_result(f"query {i}"))

    records = await repository.list_recent(limit=2)

    assert len(records) == 2
