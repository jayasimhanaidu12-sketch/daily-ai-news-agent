"""
config.py - Configuration for the Daily AI News Agent
=======================================================

Central control panel for all settings:
- RSS feed URLs and source tiers
- AI/Tech topic keywords
- Agent behavior settings
- API credentials (loaded from environment variables)

SECURITY: All secrets come from environment variables.
Never hard-code API keys, passwords, or tokens here.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# RSS FEED SOURCES
# ============================================================

RSS_FEEDS = [
    {
        "name": "TechCrunch - AI",
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
        "category": "AI",
    },
    {
        "name": "The Verge - Tech",
        "url": "https://www.theverge.com/rss/index.xml",
        "category": "Technology",
    },
    {
        "name": "Ars Technica - Technology",
        "url": "https://feeds.arstechnica.com/arstechnica/technology-lab",
        "category": "Technology",
    },
    {
        "name": "Wired - AI",
        "url": "https://www.wired.com/feed/tag/ai/latest/rss",
        "category": "AI",
    },
    {
        "name": "VentureBeat",
        "url": "https://venturebeat.com/feed/",
        "category": "AI & Technology",
    },
    {
        "name": "MIT Technology Review - AI",
        "url": "https://www.technologyreview.com/feed/",
        "category": "AI Research",
    },
    {
        "name": "Google AI Blog",
        "url": "https://blog.google/technology/ai/rss/",
        "category": "AI Research",
    },
    {
        "name": "OpenAI Blog",
        "url": "https://openai.com/blog/rss.xml",
        "category": "AI Research",
    },
    {
        "name": "NVIDIA Blog - AI",
        "url": "https://blogs.nvidia.com/feed/",
        "category": "AI & Hardware",
    },
    {
        "name": "Hacker News - Best",
        "url": "https://hnrss.org/best",
        "category": "Tech Community",
    },
]

# ============================================================
# TOPICS & KEYWORDS
# ============================================================

TOPICS = [
    "Artificial Intelligence",
    "Generative AI",
    "AI Agents",
    "Large Language Models",
    "Machine Learning",
    "Robotics",
    "Cloud Computing",
    "Semiconductors",
    "Cybersecurity",
    "AI research",
    "Major technology companies",
    "Technology launches",
]

RELEVANCE_KEYWORDS = [
    # AI & ML
    "artificial intelligence", "machine learning", "deep learning",
    "neural network", "large language model", "LLM", "GPT",
    "generative AI", "AI agent", "transformer", "diffusion model",
    "natural language processing", "NLP", "computer vision",
    "reinforcement learning", "foundation model",
    # Companies & Products
    "OpenAI", "Google DeepMind", "Anthropic", "Meta AI",
    "Microsoft", "NVIDIA", "Apple", "Amazon", "Tesla",
    "ChatGPT", "Gemini", "Claude", "Llama", "Mistral",
    "Copilot", "Sora", "Midjourney", "Stable Diffusion",
    # Hardware & Infrastructure
    "GPU", "TPU", "semiconductor", "chip", "processor",
    "quantum computing", "cloud computing",
    # Other Tech
    "robotics", "autonomous", "cybersecurity", "blockchain",
    "startup", "funding", "acquisition",
]

# ============================================================
# AGENT SETTINGS
# ============================================================

MAX_ARTICLES_PER_FEED = 20
NEWS_LOOKBACK_HOURS = 24
TARGET_STORY_COUNT = 10

# Test mode: when True, prints to terminal instead of sending email
TEST_MODE = os.getenv("TEST_MODE", "true").lower() == "true"

# ============================================================
# GEMINI AI SETTINGS (Stage 3)
# ============================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.0-flash"

# ============================================================
# IMAGE SETTINGS (Stage 4)
# ============================================================

# Timeout in seconds when fetching article pages for OG images
IMAGE_FETCH_TIMEOUT = 8

# ============================================================
# GMAIL SETTINGS (Stage 5)
# ============================================================
# Uses SMTP with Gmail App Passwords (simplest approach).
#
# Setup steps:
# 1. Enable 2-Step Verification on your Google account
# 2. Go to https://myaccount.google.com/apppasswords
# 3. Generate an App Password for "Mail"
# 4. Set GMAIL_ADDRESS and GMAIL_APP_PASSWORD as env vars
# ============================================================

GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", "")
