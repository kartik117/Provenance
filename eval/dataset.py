# Kept small deliberately: each query costs ~3 pipeline LLM calls (filter,
# synthesize, verify) plus ~3 RAGAS scoring calls, and the Gemini free tier
# caps at 20 requests/day per model. Five queries reliably exhausts it
# mid-run; three fits comfortably with room left for the day's other usage.
EVAL_QUERIES = [
    "What are recent approaches to reducing hallucination in retrieval augmented generation?",
    "How does instruction tuning improve large language model alignment?",
    "What techniques exist for efficient fine-tuning of large language models?",
]
