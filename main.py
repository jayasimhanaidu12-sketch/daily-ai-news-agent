"""
main.py - Entry Point for the Daily AI & Technology News Agent
================================================================

This is the file you run to start the agent.
"""

# --- Fix Windows console encoding for emoji/unicode ---
import sys
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

"""
THE COMPLETE PIPELINE:

    Stage 1: Fetch ~150 articles from 10 RSS feeds
    Stage 2: Deduplicate → Filter → Rank → Select top 10
    Stage 3: Summarize each story with Google Gemini AI
    Stage 4: Extract images from article pages
    Stage 5: Build HTML email and send via Gmail

HOW TO RUN:
    python main.py
"""

from datetime import datetime

from news_search import fetch_all_news
from news_filter import filter_and_rank
from ai_analyzer import analyze_and_summarize
from image_search import find_images
from email_sender import send_digest
from config import TEST_MODE


def display_top_stories(articles):
    """Display the final top stories with scores, summaries, and images."""
    if not articles:
        print("\n😕 No articles passed the filters.")
        return

    print("\n" + "=" * 60)
    print("🏆 TODAY'S TOP AI & TECHNOLOGY STORIES")
    print("=" * 60)

    for i, article in enumerate(articles, 1):
        score = article.relevance_score
        bar_length = int(score / 5)
        score_bar = "█" * bar_length + "░" * (20 - bar_length)

        print(f"\n{'─' * 55}")
        print(f"  [{i}] {article.title}")
        print(f"  ⭐ Score: {score}/100  [{score_bar}]")
        print(f"  🔗 {article.url}")
        print(f"  📡 {article.source}")
        if article.published:
            print(f"  📅 {article.published.strftime('%Y-%m-%d %H:%M UTC')}")
        if article.summary:
            summary = article.summary[:250]
            if len(article.summary) > 250:
                summary += "..."
            print(f"  🧠 {summary}")
        if article.image_url:
            print(f"  🖼️  Image: ✅")
        if article.author:
            print(f"  ✍️  {article.author}")

    print(f"\n{'─' * 55}")


def main():
    """
    Main function — orchestrates the entire agent pipeline.

    Runs all 5 stages in order:
    1. Fetch → 2. Filter → 3. Summarize → 4. Images → 5. Send
    """
    start_time = datetime.now()

    # Header
    print("\n" + "╔" + "═" * 58 + "╗")
    print("║" + " 🤖 DAILY AI & TECHNOLOGY NEWS AGENT ".center(58) + "║")
    print("║" + " ⚡ All Stages Active ⚡ ".center(58) + "║")
    print("║" + f" {start_time.strftime('%Y-%m-%d %H:%M:%S')} ".center(58) + "║")
    print("╚" + "═" * 58 + "╝")

    if TEST_MODE:
        print("\n🧪 Running in TEST MODE")

    # ====================================================
    # STAGE 1: Fetch news from RSS feeds
    # ====================================================
    articles = fetch_all_news()

    # ====================================================
    # STAGE 2: Filter, deduplicate & rank
    # ====================================================
    articles = filter_and_rank(articles)

    # ====================================================
    # STAGE 3: AI summarization
    # ====================================================
    articles = analyze_and_summarize(articles)

    # ====================================================
    # STAGE 4: Extract images
    # ====================================================
    articles = find_images(articles)

    # ====================================================
    # DISPLAY: Show top stories
    # ====================================================
    display_top_stories(articles)

    # ====================================================
    # STAGE 5: Send email digest
    # ====================================================
    send_digest(articles)

    # Final status
    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"\n✅ Agent run complete in {elapsed:.1f} seconds!")
    print(f"   Top stories: {len(articles)}")
    print(f"   Test mode: {'ON' if TEST_MODE else 'OFF'}")
    print()

    return articles


if __name__ == "__main__":
    main()
