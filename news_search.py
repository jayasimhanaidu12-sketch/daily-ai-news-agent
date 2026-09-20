"""
news_search.py - RSS Feed Fetcher for the Daily AI News Agent
===============================================================

This is the CORE of Stage 1. It does three things:

1. Connects to each RSS feed URL in config.py
2. Parses the XML data into Python objects
3. Converts each feed entry into our NewsArticle model

HOW RSS WORKS:
- RSS (Really Simple Syndication) is a standard XML format
- Websites publish their latest articles as an RSS "feed"
- We use the `feedparser` library to read these feeds
- Each feed contains "entries" — one per article
- Each entry has a title, link, summary, date, etc.

WHAT HAPPENS IF A FEED FAILS?
- We catch the error, print a warning, and skip that feed
- The agent continues with the remaining feeds
- This makes the agent resilient to individual feed outages

KEY LIBRARY: feedparser
- Handles RSS 2.0, Atom, and other feed formats automatically
- Parses dates into Python time structs
- Handles encoding issues gracefully
"""

import feedparser
from datetime import datetime, timezone
from time import mktime
from typing import List

from models import NewsArticle
from config import RSS_FEEDS, MAX_ARTICLES_PER_FEED


def parse_published_date(entry) -> datetime | None:
    """
    Extract and convert the publication date from a feed entry.

    RSS feeds store dates in different formats. The `feedparser` library
    normalizes them into a `time.struct_time` object called `published_parsed`.

    Args:
        entry: A single entry from a parsed RSS feed.

    Returns:
        A Python datetime object, or None if no date is available.
    """
    # feedparser normalizes dates into 'published_parsed' or 'updated_parsed'
    date_struct = entry.get("published_parsed") or entry.get("updated_parsed")

    if date_struct:
        # Convert time struct → timestamp → datetime (in UTC)
        timestamp = mktime(date_struct)
        return datetime.fromtimestamp(timestamp, tz=timezone.utc)

    return None


def clean_html(text: str) -> str:
    """
    Remove HTML tags from a string.

    RSS feed descriptions often contain HTML markup like <p>, <a>, <img>.
    We strip these out to get clean, readable text.

    This is a simple approach using string replacement.
    For Stage 2+, we might use a library like BeautifulSoup for better parsing.

    Args:
        text: A string that may contain HTML tags.

    Returns:
        The string with HTML tags removed.
    """
    import re
    # Remove HTML tags
    clean = re.sub(r"<[^>]+>", "", text)
    # Replace HTML entities
    clean = clean.replace("&amp;", "&")
    clean = clean.replace("&lt;", "<")
    clean = clean.replace("&gt;", ">")
    clean = clean.replace("&quot;", '"')
    clean = clean.replace("&#39;", "'")
    clean = clean.replace("&nbsp;", " ")
    # Collapse multiple whitespace into single spaces
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


def fetch_single_feed(feed_config: dict) -> List[NewsArticle]:
    """
    Fetch and parse a single RSS feed.

    This function:
    1. Downloads the RSS feed XML from the URL
    2. Parses it using feedparser
    3. Converts each entry into a NewsArticle
    4. Returns a list of NewsArticle objects

    Args:
        feed_config: A dictionary with 'name', 'url', and 'category' keys.

    Returns:
        A list of NewsArticle objects from this feed.
    """
    feed_name = feed_config["name"]
    feed_url = feed_config["url"]
    articles = []

    try:
        print(f"   📡 Fetching: {feed_name}...")

        # feedparser.parse() downloads and parses the feed in one call
        feed = feedparser.parse(feed_url)

        # Check if the feed was fetched successfully
        if feed.bozo and not feed.entries:
            # 'bozo' flag means feedparser detected an issue with the feed
            print(f"   ⚠️  Warning: Could not parse {feed_name} — skipping")
            return []

        # Process each entry (article) in the feed
        # We limit to MAX_ARTICLES_PER_FEED to avoid overwhelming ourselves
        for entry in feed.entries[:MAX_ARTICLES_PER_FEED]:
            # Extract fields, using defaults if not present
            title = entry.get("title", "No Title")
            url = entry.get("link", "")
            description = entry.get("summary", entry.get("description", ""))
            author = entry.get("author", "")
            published = parse_published_date(entry)

            # Clean HTML from the description
            description = clean_html(description)

            # Create a NewsArticle object
            article = NewsArticle(
                title=title,
                url=url,
                source=feed_name,
                published=published,
                description=description,
                author=author,
            )
            articles.append(article)

        print(f"   ✅ Found {len(articles)} articles from {feed_name}")

    except Exception as e:
        # If anything goes wrong, log it and continue
        # This ensures one broken feed doesn't crash the entire agent
        print(f"   ❌ Error fetching {feed_name}: {e}")

    return articles


def fetch_all_news() -> List[NewsArticle]:
    """
    Fetch news from ALL configured RSS feeds.

    This is the main function that Stage 1's main.py calls.
    It loops through every feed in config.py, fetches articles,
    and combines them into one big list.

    Returns:
        A combined list of NewsArticle objects from all feeds.
    """
    all_articles = []

    print("\n" + "=" * 60)
    print("🔍 COLLECTING NEWS FROM RSS FEEDS")
    print("=" * 60)
    print(f"   Configured feeds: {len(RSS_FEEDS)}")
    print(f"   Max articles per feed: {MAX_ARTICLES_PER_FEED}")
    print()

    for feed_config in RSS_FEEDS:
        articles = fetch_single_feed(feed_config)
        all_articles.extend(articles)

    print()
    print(f"📊 Total articles collected: {len(all_articles)}")
    print("=" * 60)

    return all_articles
