"""
models.py - Data Models for the Daily AI News Agent
=====================================================

This file defines the "shape" of our data using Python dataclasses.
Think of a dataclass as a blueprint — it describes what information
a news article should contain.

WHY DATACLASSES?
- They automatically generate __init__, __repr__, and __eq__ methods
- They make the code self-documenting (you can see all fields at a glance)
- They enforce structure so every part of the program agrees on the data format

STAGE 1: We define NewsArticle with basic fields.
Later stages will add fields like 'summary', 'image_url', 'relevance_score'.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class NewsArticle:
    """
    Represents a single news article collected from an RSS feed.

    Attributes:
        title:        The headline of the article
        url:          The link to the full article
        source:       Which website/feed it came from (e.g., "TechCrunch")
        published:    When the article was published
        description:  A short snippet or summary from the RSS feed
        author:       Who wrote the article (if available)

    Fields added in later stages:
        summary:          AI-generated summary (Stage 3)
        image_url:        A relevant image URL (Stage 4)
        relevance_score:  How relevant the article is to our topics (Stage 2)
    """

    title: str
    url: str
    source: str
    published: Optional[datetime] = None
    description: str = ""
    author: str = ""

    # --- Fields for later stages (pre-defined but not used yet) ---
    summary: str = ""
    image_url: str = ""
    relevance_score: float = 0.0

    def __str__(self) -> str:
        """Human-readable representation of the article."""
        date_str = self.published.strftime("%Y-%m-%d %H:%M") if self.published else "Unknown date"
        return (
            f"📰 {self.title}\n"
            f"   🔗 {self.url}\n"
            f"   📡 Source: {self.source}\n"
            f"   📅 Published: {date_str}\n"
            f"   📝 {self.description[:150]}..." if len(self.description) > 150
            else f"📰 {self.title}\n"
                 f"   🔗 {self.url}\n"
                 f"   📡 Source: {self.source}\n"
                 f"   📅 Published: {date_str}\n"
                 f"   📝 {self.description}"
        )
