from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from provenance.models import ResearchResult
from provenance.storage.orm import ResearchSessionRecord


class SessionRepository:
    """Persists ResearchResults so past queries can be browsed later."""

    def __init__(self, session_factory: async_sessionmaker) -> None:
        self._session_factory = session_factory

    async def save(self, result: ResearchResult) -> int:
        async with self._session_factory() as session:
            record = ResearchSessionRecord(
                query=result.query,
                summary_json=result.summary.model_dump(mode="json"),
                papers_json=[paper.model_dump(mode="json") for paper in result.papers],
            )
            session.add(record)
            await session.commit()
            await session.refresh(record)
            return record.id

    async def list_recent(self, limit: int = 20) -> list[ResearchSessionRecord]:
        async with self._session_factory() as session:
            stmt = (
                select(ResearchSessionRecord)
                .order_by(ResearchSessionRecord.created_at.desc(), ResearchSessionRecord.id.desc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get(self, session_id: int) -> ResearchSessionRecord | None:
        async with self._session_factory() as session:
            return await session.get(ResearchSessionRecord, session_id)
