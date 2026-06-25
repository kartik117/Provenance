from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from provenance.agents import CitationVerificationAgent, FilterAgent, SearchAgent, SynthesisAgent
from provenance.models import Paper, ResearchSummary


class PipelineState(TypedDict, total=False):
    query: str
    max_results: int
    papers: list[Paper]
    filtered_papers: list[Paper]
    summary: ResearchSummary


def build_pipeline(
    search_agent: SearchAgent | None = None,
    filter_agent: FilterAgent | None = None,
    synthesis_agent: SynthesisAgent | None = None,
    citation_verification_agent: CitationVerificationAgent | None = None,
) -> CompiledStateGraph:
    """Assembles search -> filter -> synthesize -> verify as a LangGraph graph."""
    search_agent = search_agent or SearchAgent()
    filter_agent = filter_agent or FilterAgent()
    synthesis_agent = synthesis_agent or SynthesisAgent()
    citation_verification_agent = citation_verification_agent or CitationVerificationAgent()

    async def search_node(state: PipelineState) -> dict:
        papers = await search_agent.search(state["query"], max_results=state.get("max_results", 10))
        return {"papers": papers}

    async def filter_node(state: PipelineState) -> dict:
        filtered = await filter_agent.filter(state["query"], state["papers"])
        return {"filtered_papers": filtered}

    async def synthesize_node(state: PipelineState) -> dict:
        summary = await synthesis_agent.synthesize(state["query"], state["filtered_papers"])
        return {"summary": summary}

    async def verify_node(state: PipelineState) -> dict:
        verified = await citation_verification_agent.verify(state["summary"], state["filtered_papers"])
        return {"summary": verified}

    graph = StateGraph(PipelineState)
    graph.add_node("search", search_node)
    graph.add_node("filter", filter_node)
    graph.add_node("synthesize", synthesize_node)
    graph.add_node("verify", verify_node)
    graph.add_edge(START, "search")
    graph.add_edge("search", "filter")
    graph.add_edge("filter", "synthesize")
    graph.add_edge("synthesize", "verify")
    graph.add_edge("verify", END)

    return graph.compile()
