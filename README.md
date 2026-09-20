# 🤖 Daily AI & Technology News Agent

An automated Python agent that collects, filters, summarizes, and delivers a daily digest of AI and Technology news to your inbox — every morning at 8:30 AM IST, even when your laptop is off.

## ⚡ How It Works

```
RSS Feeds (10 sources, ~150 articles)
    │
    ▼
Stage 1: Collect ──→ Fetch articles from RSS feeds
    │
    ▼
Stage 2: Filter ──→ Deduplicate + relevance filter + rank
    │                (148 articles → top 10)
    ▼
Stage 3: Summarize ──→ Google Gemini AI generates summaries
    │
    ▼
Stage 4: Images ──→ Extract article images (Open Graph)
    │
    ▼
Stage 5: Send ──→ Professional HTML email via Gmail
    │
    ▼
GitHub Actions ──→ Runs daily at 8:30 AM IST (cloud)
```

## 📋 Features

| Feature | Details |
|---------|---------|
| 📡 10 RSS sources | TechCrunch, Verge, Wired, Ars Technica, MIT Tech Review, Google AI, OpenAI, NVIDIA, VentureBeat, Hacker News |
| 🔍 Smart filtering | Keyword matching, duplicate removal, irrelevant content rejection |
| 🏆 Transparent ranking | Score 0-100 based on relevance, recency, source quality, title signals |
| 🧠 AI summaries | Google Gemini (free tier) generates concise summaries |
| 🖼️ Article images | Extracted from Open Graph meta tags (no API key needed) |
| 📧 Email delivery | Professional dark-themed HTML digest via Gmail SMTP |
| ☁️ Cloud automation | GitHub Actions runs daily even when laptop is off |
| 🔒 Secure | All credentials via environment variables / GitHub Secrets |
| 🧪 Test mode | Full pipeline testing without sending emails |

## 🗂️ Project Structure

```
daily-ai-news-agent/
├── main.py              # Entry point — runs the full pipeline
├── config.py            # RSS feeds, topics, settings, credentials
├── models.py            # NewsArticle data model
├── news_search.py       # Stage 1: RSS feed fetcher
├── news_filter.py       # Stage 2: Dedup + filter + rank
├── ai_analyzer.py       # Stage 3: Gemini AI summarization
├── image_search.py      # Stage 4: OG image extraction
├── email_sender.py      # Stage 5: Gmail SMTP sender + HTML template
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variable template
├── .gitignore           # Keeps secrets out of Git
├── README.md            # This file
└── .github/workflows/
    └── daily-news.yml   # GitHub Actions daily cron job
```

## 🚀 Quick Start (Local Testing)

### 1. Clone & Setup

```bash
cd daily-ai-news-agent

# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy the template
cp .env.example .env
```

Edit `.env` and add your keys:

```env
TEST_MODE=true
GEMINI_API_KEY=your-gemini-api-key-here
GMAIL_ADDRESS=your.email@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
RECIPIENT_EMAIL=recipient@example.com
```

### 3. Run

```bash
python main.py
```

## 🔑 Getting Your API Keys (Free)

### Google Gemini API Key (Free)

1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Copy the key → set as `GEMINI_API_KEY`

### Gmail App Password (Free)

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable **2-Step Verification**
3. Go to [App Passwords](https://myaccount.google.com/apppasswords)
4. Select **Mail** → Generate
5. Copy the 16-character password → set as `GMAIL_APP_PASSWORD`

## ☁️ Deploy to GitHub Actions (Free)

This makes the agent run automatically every day at 8:30 AM IST, even when your laptop is off.

### 1. Push to GitHub

```bash
git init
git add .
git commit -m "Daily AI News Agent"
git remote add origin https://github.com/YOUR_USERNAME/daily-ai-news-agent.git
git push -u origin main
```

### 2. Add Secrets

Go to your GitHub repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Add these 4 secrets:

| Secret Name | Value |
|-------------|-------|
| `GEMINI_API_KEY` | Your Gemini API key |
| `GMAIL_ADDRESS` | your.email@gmail.com |
| `GMAIL_APP_PASSWORD` | Your 16-char app password |
| `RECIPIENT_EMAIL` | Where to send the digest |

### 3. Test It

Go to **Actions** tab → **Daily AI News Digest** → **Run workflow** → **Run**

Watch the logs to verify everything works!

### 4. Done!

The agent will now run automatically every day at 8:30 AM IST.

## 🧪 Testing

```bash
# Test mode (default) — prints to terminal, no email sent
TEST_MODE=true python main.py

# Production mode — actually sends the email
TEST_MODE=false python main.py
```

## 📄 License

This project is for personal and educational use.
