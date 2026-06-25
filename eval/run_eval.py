"""RAGAS evaluation of the full search -> filter -> synthesize -> verify pipeline.

Measures faithfulness (does the synthesized overview actually follow from the
retrieved paper abstracts?) and context precision (were the retrieved papers
actually relevant?) across a small set of representative research queries.

Usage:
    pip install -e ".[eval]"
    python -m eval.run_eval
"""

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path

from eval import _ragas_compat  # noqa: F401  (must be imported before ragas)
from eval.dataset import EVAL_QUERIES
from ragas import SingleTurnSample
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import Faithfulness, LLMContextPrecisionWithoutReference

from provenance.clients import get_chat_model
from provenance.pipeline import build_pipeline

RESULTS_PATH = Path(__file__).parent / "results.json"


async def evaluate_query(query: str, pipeline, faithfulness, context_precision) -> dict:
    result = await pipeline.ainvoke({"query": query, "max_results": 10})
    contexts = [p.abstract for p in result["filtered_papers"] if p.abstract]
    overview = result["summary"].overview

    sample = SingleTurnSample(user_input=query, response=overview, retrieved_contexts=contexts or [""])

    faithfulness_score = await faithfulness.single_turn_ascore(sample)
    context_precision_score = await context_precision.single_turn_ascore(sample)

    return {
        "query": query,
        "papers_retrieved": len(result["papers"]),
        "papers_after_filter": len(result["filtered_papers"]),
        "overview": overview,
        "faithfulness": faithfulness_score,
        "context_precision": context_precision_score,
    }


async def main() -> None:
    ragas_llm = LangchainLLMWrapper(get_chat_model())
    faithfulness = Faithfulness(llm=ragas_llm)
    context_precision = LLMContextPrecisionWithoutReference(llm=ragas_llm)
    pipeline = build_pipeline()

    results = []
    for query in EVAL_QUERIES:
        print(f"Evaluating: {query}")
        try:
            results.append(await evaluate_query(query, pipeline, faithfulness, context_precision))
        except Exception as exc:
            message = str(exc).splitlines()[0][:200]
            print(f"  FAILED: {message}")
            results.append({"query": query, "error": message})

    scored = [r for r in results if "faithfulness" in r]
    avg_faithfulness = sum(r["faithfulness"] for r in scored) / len(scored) if scored else 0.0
    avg_context_precision = sum(r["context_precision"] for r in scored) / len(scored) if scored else 0.0

    summary = {
        "generated_at": datetime.now(UTC).isoformat(),
        "num_queries": len(EVAL_QUERIES),
        "num_scored": len(scored),
        "avg_faithfulness": avg_faithfulness,
        "avg_context_precision": avg_context_precision,
        "results": results,
    }
    RESULTS_PATH.write_text(json.dumps(summary, indent=2))

    print(f"\nAverage faithfulness:      {avg_faithfulness:.3f}")
    print(f"Average context precision: {avg_context_precision:.3f}")
    print(f"Scored {len(scored)}/{len(EVAL_QUERIES)} queries. Full results: {RESULTS_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
