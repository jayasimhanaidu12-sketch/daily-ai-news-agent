"""
ai_analyzer.py - AI-Powered Summarization (Stage 3)
=====================================================

Uses Google Gemini (free tier) to generate concise summaries
of the top news stories.

HOW IT WORKS:
1. Sends each article's title + description to Gemini
2. Gemini returns a 2-3 sentence summary
3. The summary is stored in article.summary

FREE TIER LIMITS (Gemini 2.0 Flash):
- 15 requests per minute
- 1,500 requests per day
- More than enough for 10 articles/day

FALLBACK:
- If no API key is set, uses the RSS description as-is
- If an API call fails, falls back gracefully
"""

import time
from typing import List

from models import NewsArticle
from config import GEMINI_API_KEY, GEMINI_MODEL


def _summarize_with_gemini(articles: List[NewsArticle]) -> List[NewsArticle]:
    """
    Use Google Gemini to summarize each article.

    Sends a prompt to Gemini asking for a concise, factual summary.
    Includes a 2-second delay between calls to respect rate limits.
    """
    import google.generativeai as genai

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(GEMINI_MODEL)

    for i, article in enumerate(articles):
        try:
            prompt = (
                "You are a professional technology news editor. "
                "Summarize this AI/technology news article in exactly 2-3 sentences. "
                "Be factual, concise, and highlight why this matters.\n\n"
                f"Title: {article.title}\n"
                f"Source: {article.source}\n"
                f"Description: {article.description}\n\n"
                "Summary:"
            )

            response = model.generate_content(prompt)
            summary = response.text.strip()

            # Clean up the summary
            if summary:
                article.summary = summary
                print(f"   ✅ [{i+1}/{len(articles)}] Summarized: {article.title[:50]}...")
            else:
                article.summary = article.description[:300]
                print(f"   ⚠️  [{i+1}/{len(articles)}] Empty response, using description")

            # Rate limiting: wait between API calls
            if i < len(articles) - 1:
                time.sleep(2)

        except Exception as e:
            # If Gemini fails for one article, use the description
            article.summary = article.description[:300]
            print(f"   ⚠️  [{i+1}/{len(articles)}] API error, using description: {e}")

    return articles


def _summarize_fallback(articles: List[NewsArticle]) -> List[NewsArticle]:
    """
    Fallback summarization when no AI API key is available.

    Uses the first 300 characters of the RSS description.
    This ensures the agent still works without an API key.
    """
    for article in articles:
        desc = article.description.strip()
        if desc:
            # Use description, truncated to ~300 chars at a sentence boundary
            if len(desc) > 300:
                # Try to cut at a sentence boundary
                cut = desc[:300].rfind(". ")
                if cut > 100:
                    article.summary = desc[:cut + 1]
                else:
                    article.summary = desc[:300] + "..."
            else:
                article.summary = desc
        else:
            article.summary = article.title

    return articles


def analyze_and_summarize(articles: List[NewsArticle]) -> List[NewsArticle]:
    """
    Main entry point. Summarizes articles using Gemini AI
    or falls back to description extraction.
    """
    print("\n" + "=" * 60)
    print("🧠 STAGE 3: AI SUMMARIZATION")
    print("=" * 60)

    if GEMINI_API_KEY:
        print(f"   Using: Google Gemini ({GEMINI_MODEL})")
        print(f"   Articles to summarize: {len(articles)}")
        print()
        articles = _summarize_with_gemini(articles)
    else:
        print("   ⚠️  No GEMINI_API_KEY found — using description fallback")
        print("   💡 Set GEMINI_API_KEY in .env for AI-powered summaries")
        articles = _summarize_fallback(articles)

    print(f"\n   ✅ All {len(articles)} articles summarized")
    print("=" * 60)

    return articles
