import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request

from provenance.agents import SearchAgent, dedupe
from provenance.models import Paper, ResearchResult, SavedSession, SessionListItem
from provenance.pipeline import build_pipeline
from provenance.storage import SessionRepository, create_engine, init_models, session_factory

logger = logging.getLogger(__name__)
_pipeline = build_pipeline()


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = create_engine()
    try:
        await init_models(engine)
        app.state.repository = SessionRepository(session_factory(engine))
    except Exception as exc:
        logger.warning("Session storage unavailable, /research will not persist results: %s", exc)
        app.state.repository = None
    yield
    await engine.dispose()


app = FastAPI(title="Provenance", version="0.1.0", lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/search", response_model=list[Paper])
async def search(query: str, max_results: int = 10) -> list[Paper]:
    """Raw merged search results, with no relevance filtering or synthesis."""
    papers = await SearchAgent().search(query, max_results=max_results)
    return dedupe(papers)


@app.get("/research", response_model=ResearchResult)
async def research(request: Request, query: str, max_results: int = 10) -> ResearchResult:
    """Full pipeline: search -> filter -> synthesize -> verify a cited summary."""
    pipeline_result = await _pipeline.ainvoke({"query": query, "max_results": max_results})
    result = ResearchResult(
        query=query, summary=pipeline_result["summary"], papers=pipeline_result["filtered_papers"]
    )

    if request.app.state.repository is not None:
        try:
            await request.app.state.repository.save(result)
        except Exception as exc:
            logger.warning("Failed to save research session: %s", exc)

    return result


@app.get("/sessions", response_model=list[SessionListItem])
async def list_sessions(request: Request, limit: int = 20) -> list[SessionListItem]:
    """Previously saved research sessions, most recent first."""
    if request.app.state.repository is None:
        return []
    records = await request.app.state.repository.list_recent(limit=limit)
    return [
        SessionListItem(
            id=record.id,
            query=record.query,
            overview=record.summary_json.get("overview", ""),
            created_at=record.created_at,
        )
        for record in records
    ]


@app.get("/sessions/{session_id}", response_model=SavedSession)
async def get_session(request: Request, session_id: int) -> SavedSession:
    if request.app.state.repository is None:
        raise HTTPException(status_code=404, detail="Session storage unavailable")
    record = await request.app.state.repository.get(session_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return SavedSession(
        id=record.id,
        query=record.query,
        summary=record.summary_json,
        papers=record.papers_json,
        created_at=record.created_at,
    )
