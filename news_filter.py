"""
news_filter.py - News Filtering, Deduplication & Ranking (Stage 2)
====================================================================

This module takes the raw list of ~148 articles from Stage 1 and
narrows it down to the ~10 most important AI/Tech stories.

THE PIPELINE (3 steps):

    Raw Articles (148)
        │
        ▼
    ① DEDUPLICATE ──→ Remove same-story duplicates
        │
        ▼
    ② FILTER ──→ Keep only AI/Tech relevant articles
        │
        ▼
    ③ RANK & SELECT ──→ Score each article, pick top 10

WHY NOT USE AN LLM?
- Stage 2 uses rule-based scoring (keywords, recency, source quality)
- This is fast, free, transparent, and reproducible
- Stage 3 will add AI summarization on top of these filtered results

TRANSPARENCY:
- Every article gets a numeric score
- You can see exactly WHY each article scored the way it did
- The scoring weights are easy to tune in this file
"""

import re
from datetime import datetime, timezone, timedelta
from typing import List, Tuple
from difflib import SequenceMatcher

from models import NewsArticle
from config import RELEVANCE_KEYWORDS, TARGET_STORY_COUNT, NEWS_LOOKBACK_HOURS


# ============================================================
# SCORING WEIGHTS
# ============================================================
# These control how much each factor contributes to the final
# score. Higher weight = more influence on ranking.
#
# Feel free to tune these to change what the agent prioritizes.
# ============================================================

WEIGHTS = {
    "keyword_relevance": 40,   # How many AI/Tech keywords appear (max 40 pts)
    "recency":           25,   # How recent the article is (max 25 pts)
    "source_quality":    20,   # Tier of the source (max 20 pts)
    "title_signals":     15,   # Power words in the title (max 15 pts)
}

# Source quality tiers — higher tier = more trustworthy/relevant
# Tier 3: Primary AI-focused sources (most relevant)
# Tier 2: Major tech publications
# Tier 1: General tech / community sources
SOURCE_TIERS = {
    # Tier 3 — AI-focused, primary sources (20 pts)
    "Google AI Blog":              3,
    "OpenAI Blog":                 3,
    "MIT Technology Review - AI":  3,

    # Tier 2 — Major tech publications (14 pts)
    "TechCrunch - AI":             2,
    "Wired - AI":                  2,
    "VentureBeat":                 2,
    "NVIDIA Blog - AI":            2,
    "Ars Technica - Technology":   2,

    # Tier 1 — General / community (8 pts)
    "The Verge - Tech":            1,
    "Hacker News - Best":          1,
}

# Words in the title that signal an important story
TITLE_POWER_WORDS = [
    "launch", "launches", "launched", "announce", "announces", "announced",
    "release", "releases", "released", "reveal", "reveals", "revealed",
    "introduce", "introduces", "introduced", "unveil", "unveils", "unveiled",
    "breakthrough", "new", "first", "major", "biggest",
    "raises", "funding", "acquisition", "acquires", "acquired",
    "open-source", "open source", "partnership", "partners",
    "ban", "bans", "regulation", "regulate",
    "record", "surpass", "surpasses", "milestone",
]

# Words that signal IRRELEVANT content (negative signals)
IRRELEVANT_SIGNALS = [
    "horoscope", "zodiac", "celebrity", "kardashian", "reality tv",
    "sports score", "game recap", "movie review", "album review",
    "recipe", "cooking", "fashion week", "red carpet",
    "sponsored content", "advertisement", "promoted",
    "buy now", "discount code", "affiliate",
    "deal of the day", "best deals", "price drop",
]


# ============================================================
# STEP 1: DEDUPLICATION
# ============================================================

def normalize_url(url: str) -> str:
    """
    Normalize a URL for comparison.

    Different feeds sometimes link to the same article with slightly
    different URLs (e.g., with/without trailing slashes, tracking
    parameters, or www prefix).

    Examples:
        https://www.example.com/article?utm_source=rss
        https://example.com/article
        → Both normalize to: example.com/article

    Args:
        url: The original URL string.

    Returns:
        A cleaned, normalized URL for comparison.
    """
    url = url.lower().strip()
    # Remove protocol
    url = re.sub(r"^https?://", "", url)
    # Remove www.
    url = re.sub(r"^www\.", "", url)
    # Remove trailing slash
    url = url.rstrip("/")
    # Remove common tracking parameters
    url = re.sub(r"\?.*$", "", url)
    # Remove fragment (#section)
    url = re.sub(r"#.*$", "", url)
    return url


def normalize_title(title: str) -> str:
    """
    Normalize a title for similarity comparison.

    Removes punctuation, extra spaces, and converts to lowercase
    so titles like these are recognized as similar:
        "OpenAI Launches GPT-5!"
        "OpenAI launches GPT-5"

    Args:
        title: The original article title.

    Returns:
        A cleaned, lowercase title string.
    """
    title = title.lower().strip()
    # Remove punctuation
    title = re.sub(r"[^\w\s]", "", title)
    # Collapse whitespace
    title = re.sub(r"\s+", " ", title)
    return title


def titles_are_similar(title_a: str, title_b: str, threshold: float = 0.75) -> bool:
    """
    Check if two titles are similar enough to be the same story.

    Uses SequenceMatcher from Python's difflib — it computes a
    similarity ratio between 0.0 (completely different) and 1.0
    (identical). We use a threshold of 0.75 (75% similar).

    Example:
        "Google launches Gemini 2.0"  vs  "Google unveils Gemini 2.0"
        → Similarity: ~0.82 → DUPLICATE ✓

        "Google launches Gemini 2.0"  vs  "Apple releases new iPhone"
        → Similarity: ~0.25 → NOT duplicate ✗

    Args:
        title_a:   First title (already normalized).
        title_b:   Second title (already normalized).
        threshold: Minimum similarity ratio to consider as duplicate.

    Returns:
        True if the titles are similar enough to be duplicates.
    """
    ratio = SequenceMatcher(None, title_a, title_b).ratio()
    return ratio >= threshold


def deduplicate(articles: List[NewsArticle]) -> List[NewsArticle]:
    """
    Remove duplicate articles from the list.

    An article is considered a duplicate if:
    1. Its URL matches another article's URL (exact match after normalization)
    2. Its title is very similar to another article's title (≥75% similar)

    When duplicates are found, we keep the one from the higher-tier source.

    Args:
        articles: The raw list of articles from all feeds.

    Returns:
        A deduplicated list of articles.
    """
    if not articles:
        return []

    unique_articles = []
    seen_urls = set()         # Track normalized URLs we've already seen
    seen_titles = []          # Track normalized titles for fuzzy matching

    # Sort by source tier (highest first) so we keep the best source
    articles_sorted = sorted(
        articles,
        key=lambda a: SOURCE_TIERS.get(a.source, 0),
        reverse=True,
    )

    for article in articles_sorted:
        norm_url = normalize_url(article.url)
        norm_title = normalize_title(article.title)

        # Check 1: Have we seen this exact URL before?
        if norm_url in seen_urls:
            continue

        # Check 2: Is the title very similar to one we've already kept?
        is_title_dup = False
        for existing_title in seen_titles:
            if titles_are_similar(norm_title, existing_title):
                is_title_dup = True
                break

        if is_title_dup:
            continue

        # This article is unique — keep it
        seen_urls.add(norm_url)
        seen_titles.append(norm_title)
        unique_articles.append(article)

    return unique_articles


# ============================================================
# STEP 2: RELEVANCE FILTERING
# ============================================================

def count_keyword_matches(text: str) -> int:
    """
    Count how many relevance keywords appear in the text.

    We search the combined title + description for each keyword
    in our RELEVANCE_KEYWORDS list from config.py.

    Args:
        text: The combined title + description text (lowercased).

    Returns:
        The number of distinct keywords found.
    """
    text_lower = text.lower()
    matches = 0
    for keyword in RELEVANCE_KEYWORDS:
        if keyword.lower() in text_lower:
            matches += 1
    return matches


def has_irrelevant_signals(text: str) -> bool:
    """
    Check if the article contains signals of irrelevant content.

    If any of the IRRELEVANT_SIGNALS words/phrases appear in the
    article text, it's likely not a story we want.

    Args:
        text: The combined title + description text (lowercased).

    Returns:
        True if the article appears irrelevant.
    """
    text_lower = text.lower()
    for signal in IRRELEVANT_SIGNALS:
        if signal in text_lower:
            return True
    return False


def filter_relevant(articles: List[NewsArticle]) -> List[NewsArticle]:
    """
    Keep only articles that are relevant to AI and Technology.

    An article passes the filter if:
    1. It has at least 1 keyword match (from RELEVANCE_KEYWORDS)
    2. It does NOT contain irrelevant signals

    This is a simple but effective first pass. The ranking step
    (Step 3) will further prioritize the best stories.

    Args:
        articles: The deduplicated list of articles.

    Returns:
        A filtered list containing only relevant articles.
    """
    relevant = []

    for article in articles:
        # Combine title and description for keyword searching
        combined_text = f"{article.title} {article.description}"

        # Check for irrelevant content first (fast rejection)
        if has_irrelevant_signals(combined_text):
            continue

        # Check for at least 1 relevant keyword
        keyword_count = count_keyword_matches(combined_text)
        if keyword_count >= 1:
            relevant.append(article)

    return relevant


# ============================================================
# STEP 3: RANKING
# ============================================================

def score_keyword_relevance(article: NewsArticle) -> float:
    """
    Score based on how many AI/Tech keywords appear.

    More keyword matches = higher relevance.
    Score is capped at WEIGHTS["keyword_relevance"] (40 points).

    Scoring:
        1 keyword  →  8 pts
        2 keywords → 16 pts
        3 keywords → 24 pts
        4 keywords → 32 pts
        5+ keywords→ 40 pts (cap)

    Args:
        article: The article to score.

    Returns:
        A score between 0 and 40.
    """
    combined_text = f"{article.title} {article.description}"
    matches = count_keyword_matches(combined_text)
    max_score = WEIGHTS["keyword_relevance"]

    # Each keyword match is worth 8 points, capped at max_score
    score = min(matches * 8, max_score)
    return score


def score_recency(article: NewsArticle) -> float:
    """
    Score based on how recently the article was published.

    Newer articles score higher. Articles older than
    NEWS_LOOKBACK_HOURS get 0 points.

    Scoring:
        Published 0-2 hours ago  → 25 pts
        Published 2-6 hours ago  → 20 pts
        Published 6-12 hours ago → 15 pts
        Published 12-24 hours ago→ 10 pts
        Published 24-48 hours ago→  5 pts
        Older than 48 hours      →  0 pts

    Args:
        article: The article to score.

    Returns:
        A score between 0 and 25.
    """
    max_score = WEIGHTS["recency"]

    if article.published is None:
        # No date available — give a middling score
        return max_score * 0.3

    now = datetime.now(timezone.utc)
    age = now - article.published
    hours_old = age.total_seconds() / 3600

    if hours_old <= 2:
        return max_score                  # 25 pts — very fresh
    elif hours_old <= 6:
        return max_score * 0.8            # 20 pts
    elif hours_old <= 12:
        return max_score * 0.6            # 15 pts
    elif hours_old <= 24:
        return max_score * 0.4            # 10 pts
    elif hours_old <= 48:
        return max_score * 0.2            #  5 pts
    else:
        return 0.0                        #  0 pts — too old


def score_source_quality(article: NewsArticle) -> float:
    """
    Score based on the source's tier.

    Higher-tier sources (Google AI Blog, OpenAI Blog) get more
    points because they publish original, authoritative content.

    Scoring:
        Tier 3 (primary AI sources) → 20 pts
        Tier 2 (major tech pubs)    → 14 pts
        Tier 1 (general/community)  →  8 pts
        Unknown source              →  5 pts

    Args:
        article: The article to score.

    Returns:
        A score between 5 and 20.
    """
    max_score = WEIGHTS["source_quality"]
    tier = SOURCE_TIERS.get(article.source, 0)

    if tier == 3:
        return max_score                  # 20 pts
    elif tier == 2:
        return max_score * 0.7            # 14 pts
    elif tier == 1:
        return max_score * 0.4            #  8 pts
    else:
        return max_score * 0.25           #  5 pts — unknown source


def score_title_signals(article: NewsArticle) -> float:
    """
    Score based on "power words" in the title.

    Titles containing words like "launches", "breakthrough",
    "announces" signal that this is a significant story.

    Scoring:
        Each power word found → 5 pts
        Maximum              → 15 pts

    Args:
        article: The article to score.

    Returns:
        A score between 0 and 15.
    """
    max_score = WEIGHTS["title_signals"]
    title_lower = article.title.lower()

    power_word_count = 0
    for word in TITLE_POWER_WORDS:
        if word in title_lower:
            power_word_count += 1

    score = min(power_word_count * 5, max_score)
    return score


def calculate_total_score(article: NewsArticle) -> float:
    """
    Calculate the total relevance score for an article.

    Combines all four scoring factors:
        keyword_relevance (0-40) + recency (0-25) +
        source_quality (0-20)   + title_signals (0-15)
        = Total score out of 100

    Args:
        article: The article to score.

    Returns:
        A total score between 0 and 100.
    """
    score = (
        score_keyword_relevance(article) +
        score_recency(article) +
        score_source_quality(article) +
        score_title_signals(article)
    )
    return round(score, 1)


def rank_and_select(articles: List[NewsArticle], top_n: int) -> List[NewsArticle]:
    """
    Score all articles and select the top N.

    Each article gets a score from 0-100 based on four factors.
    We then sort by score (highest first) and return the top N.

    Args:
        articles: The filtered list of relevant articles.
        top_n:    How many top stories to select.

    Returns:
        The top N articles, sorted by score (highest first).
    """
    # Score every article
    for article in articles:
        article.relevance_score = calculate_total_score(article)

    # Sort by score (highest first)
    articles_sorted = sorted(
        articles,
        key=lambda a: a.relevance_score,
        reverse=True,
    )

    # Return only the top N
    return articles_sorted[:top_n]


# ============================================================
# MAIN ENTRY POINT
# ============================================================

def filter_and_rank(articles: List[NewsArticle]) -> List[NewsArticle]:
    """
    Main function called by main.py.

    Runs the full 3-step pipeline:
        1. Deduplicate
        2. Filter for relevance
        3. Rank and select top stories

    Prints progress stats at each step so you can see how the
    list narrows down.

    Args:
        articles: The raw list of articles from news_search.py.

    Returns:
        The top ~10 most important AI/Tech articles.
    """
    raw_count = len(articles)

    print("\n" + "=" * 60)
    print("🔍 STAGE 2: FILTERING, DEDUPLICATION & RANKING")
    print("=" * 60)

    # --- Step 1: Remove duplicates ---
    print("\n📋 Step 1: Removing duplicates...")
    articles = deduplicate(articles)
    dedup_count = len(articles)
    removed_dupes = raw_count - dedup_count
    print(f"   Removed {removed_dupes} duplicate articles")

    # --- Step 2: Filter for relevance ---
    print("\n🎯 Step 2: Filtering for AI/Tech relevance...")
    articles = filter_relevant(articles)
    filtered_count = len(articles)
    removed_irrelevant = dedup_count - filtered_count
    print(f"   Removed {removed_irrelevant} irrelevant articles")

    # --- Step 3: Rank and select top stories ---
    top_n = TARGET_STORY_COUNT
    print(f"\n🏆 Step 3: Ranking and selecting top {top_n} stories...")
    articles = rank_and_select(articles, top_n)
    print(f"   Selected {len(articles)} top stories")

    # --- Summary ---
    print(f"\n{'─' * 45}")
    print(f"   📰 RAW ARTICLES:           {raw_count:>4}")
    print(f"   🔄 AFTER DEDUPLICATION:     {dedup_count:>4}")
    print(f"   🎯 AFTER RELEVANCE FILTER:  {filtered_count:>4}")
    print(f"   🏆 TOP STORIES:             {len(articles):>4}")
    print(f"{'─' * 45}")
    print("=" * 60)

    return articles
