from collections.abc import Awaitable, Callable

from provenance.clients import get_chat_model
from provenance.models import Paper, ResearchSummary

_SYNTHESIS_PROMPT = """You are a research assistant. Answer the query using ONLY the \
papers below — do not use outside knowledge. Every factual claim must cite the \
source_id(s) of the paper(s) that support it.

Query: {query}

Papers:
{papers_block}

Write a short overview (3-6 sentences) answering the query, then break the answer \
into individual claims, each with the source_ids of the papers that support it.
"""

Synthesizer = Callable[[str, list[Paper]], Awaitable[ResearchSummary]]


async def synthesize_with_llm(query: str, papers: list[Paper]) -> ResearchSummary:
    """Default synthesizer: one structured-output call to Gemini grounded in the papers."""
    papers_block = "\n\n".join(
        f"[{paper.source_id}] {paper.title}\n{paper.abstract[:800]}" for paper in papers
    )
    prompt = _SYNTHESIS_PROMPT.format(query=query, papers_block=papers_block)
    structured_llm = get_chat_model().with_structured_output(ResearchSummary)
    return await structured_llm.ainvoke(prompt)


class SynthesisAgent:
    """Turns a filtered set of papers into a short, cited research summary."""

    def __init__(self, synthesizer: Synthesizer = synthesize_with_llm) -> None:
        self._synthesizer = synthesizer

    async def synthesize(self, query: str, papers: list[Paper]) -> ResearchSummary:
        if not papers:
            return ResearchSummary(overview="No relevant papers were found for this query.")
        return await self._synthesizer(query, papers)
