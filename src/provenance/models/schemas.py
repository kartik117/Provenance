from datetime import date
from enum import Enum

from pydantic import BaseModel, Field


class PaperSource(str, Enum):
    ARXIV = "arxiv"
    SEMANTIC_SCHOLAR = "semantic_scholar"


class Paper(BaseModel):
    """A single paper returned by a search client, before filtering or scoring."""

    source: PaperSource
    source_id: str
    title: str
    authors: list[str] = Field(default_factory=list)
    abstract: str = ""
    url: str
    published: date | None = None
    citation_count: int | None = None

    @property
    def dedup_key(self) -> str:
        """Normalized title used to spot the same paper returned by multiple sources."""
        return " ".join(self.title.lower().split())
