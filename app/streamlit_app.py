import os

import requests
import streamlit as st

API_BASE_URL = os.environ.get("PROVENANCE_API_URL", "http://localhost:8000")

st.set_page_config(page_title="Provenance", page_icon="📚")
st.title("Provenance")
st.caption("Search ArXiv and Semantic Scholar in one query, deduplicated and merged.")

query = st.text_input("Research question or topic", placeholder="e.g. retrieval augmented generation")
max_results = st.slider("Max results per source", min_value=5, max_value=30, value=10)

if st.button("Search", type="primary") and query:
    with st.spinner("Searching ArXiv and Semantic Scholar..."):
        try:
            response = requests.get(
                f"{API_BASE_URL}/search",
                params={"query": query, "max_results": max_results},
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
            meta = [", ".join(paper["authors"]) or "Unknown authors"]
            if paper.get("published"):
                meta.append(paper["published"])
            if paper.get("citation_count") is not None:
                meta.append(f"{paper['citation_count']} citations")
            st.caption(" · ".join(meta) + f"  ·  source: {paper['source']}")
            if paper.get("abstract"):
                with st.expander("Abstract"):
                    st.write(paper["abstract"])
