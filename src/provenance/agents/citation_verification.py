from collections.abc import Awaitable, Callable

from pydantic import BaseModel

from provenance.clients import get_chat_model
from provenance.models import Citation, Paper, ResearchSummary

_VERIFICATION_PROMPT = """You are fact-checking claims against their cited source papers.

For each claim below, decide whether the cited paper abstract(s) actually \
support the claim. Mark a claim verified only if the abstract gives clear \
evidence for it. If no source abstract is given, or the abstract doesn't \
support the claim, mark it not verified — do not verify a claim just because \
it sounds plausible.

{claims_block}
"""


class VerificationResult(BaseModel):
    index: int
    verified: bool


class VerificationResults(BaseModel):
    results: list[VerificationResult]


Verifier = Callable[[list[Citation], dict[str, Paper]], Awaitable[dict[int, bool]]]


async def verify_with_llm(citations: list[Citation], papers_by_id: dict[str, Paper]) -> dict[int, bool]:
    """Default verifier: one structured-output call to Gemini checking claim <-> abstract alignment."""
    blocks = []
    for index, citation in enumerate(citations):
        cited_papers = [papers_by_id[sid] for sid in citation.source_ids if sid in papers_by_id]
        if cited_papers:
            sources_text = "\n".join(
                f"  [{paper.source_id}] {paper.title}: {paper.abstract[:600]}" for paper in cited_papers
            )
        else:
            sources_text = "  (no cited source found)"
        blocks.append(f"Claim [{index}]: {citation.claim}\nCited sources:\n{sources_text}")

    prompt = _VERIFICATION_PROMPT.format(claims_block="\n\n".join(blocks))
    structured_llm = get_chat_model().with_structured_output(VerificationResults)
    result: VerificationResults = await structured_llm.ainvoke(prompt)
    return {item.index: item.verified for item in result.results}


class CitationVerificationAgent:
    """Checks every claim in a ResearchSummary against the abstracts of its cited papers."""

    def __init__(self, verifier: Verifier = verify_with_llm) -> None:
        self._verifier = verifier

    async def verify(self, summary: ResearchSummary, papers: list[Paper]) -> ResearchSummary:
        if not summary.citations:
            return summary

        papers_by_id = {paper.source_id: paper for paper in papers}
        verdicts = await self._verifier(summary.citations, papers_by_id)

        verified_citations = [
            citation.model_copy(update={"verified": verdicts.get(index, False)})
            for index, citation in enumerate(summary.citations)
        ]
        return summary.model_copy(update={"citations": verified_citations})
