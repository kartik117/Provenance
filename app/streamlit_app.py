import os

import requests
import streamlit as st

API_BASE_URL = os.environ.get("PROVENANCE_API_URL", "http://localhost:8000")

st.set_page_config(page_title="Provenance", page_icon="📚")
st.title("Provenance")
st.caption("A research assistant that verifies every citation against its source before showing it to you.")

research_tab, search_tab = st.tabs(["Research", "Raw search"])


def render_paper_meta(paper: dict) -> str:
    meta = [", ".join(paper["authors"]) or "Unknown authors"]
    if paper.get("published"):
        meta.append(paper["published"])
    if paper.get("citation_count") is not None:
        meta.append(f"{paper['citation_count']} citations")
    return " · ".join(meta) + f"  ·  source: {paper['source']}"


with research_tab:
    query = st.text_input(
        "Research question", placeholder="e.g. what are recent approaches to reducing hallucination in RAG?"
    )
    max_results = st.slider("Max results per source", min_value=5, max_value=30, value=10, key="research_max")

    if st.button("Research", type="primary") and query:
        with st.spinner("Searching, filtering, synthesizing, and verifying citations..."):
            try:
                response = requests.get(
                    f"{API_BASE_URL}/research",
                    params={"query": query, "max_results": max_results},
                    timeout=120,
                )
                response.raise_for_status()
                result = response.json()
            except requests.RequestException as exc:
                st.error(f"Research failed: {exc}")
                result = None

        if result:
            papers_by_id = {p["source_id"]: p for p in result["papers"]}
            citations = result["summary"]["citations"]
            verified_count = sum(1 for c in citations if c["verified"])

            st.subheader("Overview")
            st.write(result["summary"]["overview"])

            if citations:
                st.caption(f"{verified_count} of {len(citations)} claims verified against their cited sources")

            for citation in citations:
                badge = "✅ Verified" if citation["verified"] else "⚠️ Not verified"
                with st.container(border=True):
                    st.markdown(f"{badge}  —  {citation['claim']}")
                    for source_id in citation["source_ids"]:
                        paper = papers_by_id.get(source_id)
                        if paper:
                            st.caption(f"[{paper['title']}]({paper['url']})")
                        else:
                            st.caption(f"⚠️ cited source `{source_id}` was not in the retrieved papers")

            if not citations:
                st.info("No citable claims were produced for this query.")


with search_tab:
    st.caption("Bypasses filtering and synthesis — raw merged results from ArXiv and Semantic Scholar.")
    raw_query = st.text_input("Search query", placeholder="e.g. retrieval augmented generation", key="raw_query")
    raw_max_results = st.slider("Max results per source", min_value=5, max_value=30, value=10, key="raw_max")

    if st.button("Search", key="raw_search") and raw_query:
        with st.spinner("Searching ArXiv and Semantic Scholar..."):
            try:
                response = requests.get(
                    f"{API_BASE_URL}/search",
                    params={"query": raw_query, "max_results": raw_max_results},
                    timeout=30,
                )
                response.raise_for_status()
                papers = response.json()
            except requests.RequestException as exc:
                st.error(f"Search failed: {exc}")
                papers = []

        if not papers:
            st.info("No results.")

        for paper in papers:
            with st.container(border=True):
                st.markdown(f"**[{paper['title']}]({paper['url']})**")
                st.caption(render_paper_meta(paper))
                if paper.get("abstract"):
                    with st.expander("Abstract"):
                        st.write(paper["abstract"])
