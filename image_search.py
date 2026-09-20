"""
image_search.py - Image Retrieval for News Stories (Stage 4)
==============================================================

Extracts Open Graph (og:image) images from article URLs.

HOW IT WORKS:
- Most news websites include an og:image meta tag in their HTML
- This tag contains the URL of the article's main image
- We fetch the article page and parse this tag using BeautifulSoup
- No API key needed — this is 100% free

WHAT IS OPEN GRAPH?
- Open Graph is a standard created by Facebook
- It defines how a webpage appears when shared on social media
- The og:image tag specifies the "preview image" for the article
- Nearly every major news site uses it

FALLBACK:
- If we can't fetch the page or find an og:image, we skip that article
- Articles without images still appear in the digest (just without an image)
"""

import requests
from bs4 import BeautifulSoup
from typing import List

from models import NewsArticle
from config import IMAGE_FETCH_TIMEOUT


def extract_og_image(url: str) -> str:
    """
    Fetch an article page and extract its Open Graph image URL.

    Steps:
    1. Send a GET request to the article URL
    2. Parse the HTML with BeautifulSoup
    3. Find the <meta property="og:image"> tag
    4. Return its content (the image URL)

    Args:
        url: The article URL to fetch.

    Returns:
        The image URL string, or empty string if not found.
    """
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=IMAGE_FETCH_TIMEOUT,
            allow_redirects=True,
        )

        if response.status_code != 200:
            return ""

        soup = BeautifulSoup(response.text, "html.parser")

        # Try og:image first (most common)
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            return og_image["content"]

        # Fallback: try twitter:image
        twitter_image = soup.find("meta", attrs={"name": "twitter:image"})
        if twitter_image and twitter_image.get("content"):
            return twitter_image["content"]

        return ""

    except Exception:
        # Network errors, timeouts, parsing errors — skip silently
        return ""


def find_images(articles: List[NewsArticle]) -> List[NewsArticle]:
    """
    Main entry point. Fetches images for all articles.

    Goes through each article and tries to extract its OG image.
    Prints progress as it goes.
    """
    print("\n" + "=" * 60)
    print("🖼️  STAGE 4: IMAGE RETRIEVAL")
    print("=" * 60)
    print(f"   Fetching images for {len(articles)} articles...")
    print()

    found_count = 0

    for i, article in enumerate(articles):
        image_url = extract_og_image(article.url)

        if image_url:
            article.image_url = image_url
            found_count += 1
            print(f"   ✅ [{i+1}/{len(articles)}] Image found: {article.title[:45]}...")
        else:
            print(f"   ⬜ [{i+1}/{len(articles)}] No image: {article.title[:45]}...")

    print(f"\n   📊 Images found: {found_count}/{len(articles)}")
    print("=" * 60)

    return articles
