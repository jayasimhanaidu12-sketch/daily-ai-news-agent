"""
email_sender.py - Gmail Email Delivery (Stage 5)
===================================================

Sends the daily AI news digest as a professional HTML email
using Gmail SMTP with App Passwords.

HOW IT WORKS:
1. Builds an HTML email from the top articles
2. Connects to Gmail's SMTP server (smtp.gmail.com:465)
3. Authenticates with your Gmail + App Password
4. Sends the email to the recipient

SETUP (one-time):
1. Enable 2-Step Verification: https://myaccount.google.com/security
2. Create App Password: https://myaccount.google.com/apppasswords
3. Set environment variables:
   GMAIL_ADDRESS=your.email@gmail.com
   GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
   RECIPIENT_EMAIL=recipient@example.com

WHY SMTP + APP PASSWORDS?
- Simpler than OAuth2 (no token refresh, no credentials.json)
- Works perfectly in GitHub Actions
- Uses Python's built-in smtplib (no extra dependencies)
- App Passwords are secure (scoped, revocable, require 2FA)
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List

from models import NewsArticle
from config import GMAIL_ADDRESS, GMAIL_APP_PASSWORD, RECIPIENT_EMAIL, TEST_MODE


def _build_html_digest(articles: List[NewsArticle]) -> str:
    """
    Build a professional HTML email from the top articles.

    Creates a responsive, dark-themed email digest with:
    - Header with date
    - Story cards with image, title, summary, source
    - Score badges
    - Footer with attribution
    """
    today = datetime.now().strftime("%B %d, %Y")

    # Build story cards
    story_cards = ""
    for i, article in enumerate(articles, 1):
        date_str = ""
        if article.published:
            date_str = article.published.strftime("%b %d, %Y • %H:%M UTC")

        # Use summary if available, otherwise description
        body_text = article.summary if article.summary else article.description
        if not body_text:
            body_text = "Click to read the full article."

        # Image block (only if we have an image)
        image_html = ""
        if article.image_url:
            image_html = f'''
            <div style="margin-bottom:12px;">
                <img src="{article.image_url}" alt="{article.title}"
                     style="width:100%;max-height:220px;object-fit:cover;
                            border-radius:8px;display:block;" />
            </div>'''

        # Score bar visual
        score = article.relevance_score
        bar_pct = min(int(score), 100)

        story_cards += f'''
        <div style="background:#1e1e2e;border-radius:12px;padding:20px;
                     margin-bottom:16px;border:1px solid #313244;">
            <div style="display:flex;align-items:center;margin-bottom:8px;">
                <span style="background:#89b4fa;color:#1e1e2e;font-weight:700;
                             border-radius:6px;padding:3px 10px;font-size:13px;
                             margin-right:10px;">#{i}</span>
                <span style="background:#45475a;color:#a6adc8;font-size:12px;
                             border-radius:4px;padding:2px 8px;">
                    ⭐ {score}/100
                </span>
            </div>
            {image_html}
            <a href="{article.url}" style="color:#89b4fa;font-size:18px;
               font-weight:700;text-decoration:none;line-height:1.3;
               display:block;margin-bottom:8px;">
                {article.title}
            </a>
            <p style="color:#cdd6f4;font-size:14px;line-height:1.6;
                      margin:0 0 12px 0;">
                {body_text}
            </p>
            <div style="color:#6c7086;font-size:12px;">
                📡 {article.source}
                {f"&nbsp;&nbsp;•&nbsp;&nbsp;📅 {date_str}" if date_str else ""}
            </div>
        </div>'''

    # Full HTML email
    html = f'''<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width"></head>
<body style="margin:0;padding:0;background:#11111b;font-family:
             -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">

  <div style="max-width:640px;margin:0 auto;padding:24px 16px;">

    <!-- HEADER -->
    <div style="text-align:center;padding:32px 20px;background:linear-gradient(
                135deg,#1e1e2e 0%,#181825 100%);border-radius:16px;
                margin-bottom:24px;border:1px solid #313244;">
      <div style="font-size:36px;margin-bottom:8px;">🤖</div>
      <h1 style="color:#cdd6f4;font-size:22px;margin:0 0 4px 0;font-weight:700;">
        Daily AI &amp; Technology News
      </h1>
      <p style="color:#6c7086;font-size:14px;margin:0;">{today}</p>
      <p style="color:#45475a;font-size:12px;margin:8px 0 0 0;">
        {len(articles)} stories curated by your AI News Agent
      </p>
    </div>

    <!-- STORIES -->
    {story_cards}

    <!-- FOOTER -->
    <div style="text-align:center;padding:20px;color:#45475a;font-size:11px;">
      <p style="margin:0 0 4px 0;">
        Generated by Daily AI &amp; Technology News Agent
      </p>
      <p style="margin:0;">
        Powered by Google Gemini • Delivered via GitHub Actions
      </p>
    </div>

  </div>
</body>
</html>'''

    return html


def _build_plain_text_digest(articles: List[NewsArticle]) -> str:
    """
    Build a plain-text version of the digest for email clients
    that don't render HTML.
    """
    today = datetime.now().strftime("%B %d, %Y")
    lines = [
        f"🤖 Daily AI & Technology News — {today}",
        f"   {len(articles)} stories curated by your AI News Agent",
        "",
        "=" * 55,
    ]

    for i, article in enumerate(articles, 1):
        body = article.summary if article.summary else article.description
        if not body:
            body = ""
        lines.append(f"\n#{i} — {article.title}")
        lines.append(f"   ⭐ Score: {article.relevance_score}/100")
        lines.append(f"   🔗 {article.url}")
        lines.append(f"   📡 {article.source}")
        if body:
            lines.append(f"   {body[:250]}")
        lines.append("")

    lines.append("=" * 55)
    lines.append("Generated by Daily AI & Technology News Agent")

    return "\n".join(lines)


def send_digest(articles: List[NewsArticle]) -> bool:
    """
    Send the daily digest email.

    In TEST_MODE: prints the digest to terminal instead of sending.
    In production: sends via Gmail SMTP.

    Returns True if sent successfully, False otherwise.
    """
    print("\n" + "=" * 60)
    print("📧 STAGE 5: EMAIL DELIVERY")
    print("=" * 60)

    if not articles:
        print("   ⚠️  No articles to send.")
        return False

    # Build the email content
    html_content = _build_html_digest(articles)
    plain_content = _build_plain_text_digest(articles)
    today = datetime.now().strftime("%B %d, %Y")
    subject = f"🤖 Daily AI News Digest — {today}"

    # --- TEST MODE: print to terminal ---
    if TEST_MODE:
        print("   🧪 TEST MODE — printing digest to terminal\n")
        print(plain_content)
        print(f"\n   📊 HTML email size: {len(html_content):,} bytes")
        print("   💡 Set TEST_MODE=false and configure Gmail to send emails")
        print("=" * 60)
        return True

    # --- PRODUCTION MODE: send via Gmail SMTP ---
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD or not RECIPIENT_EMAIL:
        print("   ❌ Gmail not configured. Set these environment variables:")
        print("      GMAIL_ADDRESS=your.email@gmail.com")
        print("      GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx")
        print("      RECIPIENT_EMAIL=recipient@example.com")
        print("=" * 60)
        return False

    try:
        print(f"   📤 Sending to: {RECIPIENT_EMAIL}")

        # Build the MIME email (HTML + plain text fallback)
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"AI News Agent <{GMAIL_ADDRESS}>"
        msg["To"] = RECIPIENT_EMAIL

        msg.attach(MIMEText(plain_content, "plain", "utf-8"))
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        # Connect and send via Gmail SMTP
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, RECIPIENT_EMAIL, msg.as_string())

        print("   ✅ Email sent successfully!")
        print("=" * 60)
        return True

    except smtplib.SMTPAuthenticationError:
        print("   ❌ Gmail authentication failed!")
        print("      Check your GMAIL_ADDRESS and GMAIL_APP_PASSWORD")
        print("      Make sure 2-Step Verification is enabled")
        print("=" * 60)
        return False

    except Exception as e:
        print(f"   ❌ Failed to send email: {e}")
        print("=" * 60)
        return False
