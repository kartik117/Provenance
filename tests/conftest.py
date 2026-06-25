import pytest

ARXIV_FEED_SINGLE_ENTRY = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2301.00001v1</id>
    <title>Attention Is All You Need Again</title>
    <summary>
      We revisit the transformer architecture and propose improvements.
    </summary>
    <published>2023-01-01T12:00:00Z</published>
    <author><name>Jane Doe</name></author>
    <author><name>John Smith</name></author>
  </entry>
</feed>
"""

SEMANTIC_SCHOLAR_SINGLE_PAPER = {
    "total": 1,
    "data": [
        {
            "paperId": "abc123",
            "title": "Attention Is All You Need",
            "abstract": "We propose the transformer architecture.",
            "authors": [{"authorId": "1", "name": "Ashish Vaswani"}],
            "url": "https://www.semanticscholar.org/paper/abc123",
            "publicationDate": "2017-06-12",
            "citationCount": 100000,
        }
    ],
}


@pytest.fixture
def arxiv_feed_single_entry() -> str:
    return ARXIV_FEED_SINGLE_ENTRY


@pytest.fixture
def semantic_scholar_single_paper() -> dict:
    return SEMANTIC_SCHOLAR_SINGLE_PAPER
