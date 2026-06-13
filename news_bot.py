import os
import smtplib
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from email.mime.text import MIMEText
import requests

SOURCES = [
    {
        "name": "BBC News",
        "url": "https://feeds.bbci.co.uk/news/rss.xml",
    },
    {
        "name": "The Hindu",
        "url": "https://www.thehindu.com/feeder/default.rss",
    },
    {
        "name": "The Guardian",
        "url": "https://www.theguardian.com/international/rss",
    }
]

def clean_html(text):
    if not text:
        return ""
    # Remove HTML tags
    clean = re.sub(r'<[^>]+>', '', text)
    # Normalize whitespace
    clean = " ".join(clean.split())
    return clean

def clean_description(text):
    cleaned = clean_html(text)
    if len(cleaned) > 200:
        cleaned = cleaned[:197] + "..."
    return cleaned

def format_pubdate(pubdate_str):
    if not pubdate_str:
        return "Time unavailable"
    try:
        dt = parsedate_to_datetime(pubdate_str)
        now = datetime.now(timezone.utc)
        diff = now - dt
        seconds = diff.total_seconds()
        if seconds < 0:
            seconds = 0
        
        minutes = int(seconds / 60)
        hours = int(minutes / 60)
        days = int(hours / 24)

        if days > 0:
            if days == 1:
                return "1 day ago"
            if days > 3:
                return dt.strftime("%d %b %Y")
            return f"{days} days ago"
        elif hours > 0:
            if hours == 1:
                return "1 hr ago"
            return f"{hours} hrs ago"
        elif minutes > 0:
            if minutes == 1:
                return "1 min ago"
            return f"{minutes} mins ago"
        else:
            return "Just now"
    except Exception as e:
        print(f"Error parsing date '{pubdate_str}': {e}")
        return "Time unavailable"

def fetch_feed_articles(source_name, source_url):
    articles = []
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        resp = requests.get(source_url, headers=headers, timeout=15)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        items = root.findall(".//item")
        
        for item in items[:5]:
            title = item.find("title")
            link = item.find("link")
            desc = item.find("description")
            pub_date = item.find("pubDate")

            title_text = title.text.strip() if title is not None and title.text else "No Title"
            link_text = link.text.strip() if link is not None and link.text else "#"
            desc_text = desc.text.strip() if desc is not None and desc.text else ""
            pub_date_text = pub_date.text.strip() if pub_date is not None and pub_date.text else ""

            articles.append({
                "title": title_text,
                "link": link_text,
                "description": clean_description(desc_text),
                "pub_date": format_pubdate(pub_date_text)
            })
    except Exception as e:
        print(f"Error fetching from {source_name}: {e}")
        articles.append({
            "title": f"Failed to load latest articles from {source_name}",
            "link": "#",
            "description": f"Could not retrieve feed: {str(e)}",
            "pub_date": "Time unavailable"
        })
    
    # Ensure we have at least one entry if feed was empty
    if not articles:
        articles.append({
            "title": f"No articles found for {source_name}",
            "link": "#",
            "description": "The feed did not contain any items at this time.",
            "pub_date": "Time unavailable"
        })
    return articles

def generate_html_email(news_data):
    today_str = datetime.now().strftime("%A, %d %B %Y")
    
    sections_html = []
    for source_name, articles in news_data.items():
        articles_html = []
        for art in articles:
            desc_part = f'<div style="margin-top: 4px; font-size: 14px; color: #444; line-height: 1.4;">{art["description"]}</div>' if art["description"] else ''
            item_html = f"""
                <tr>
                  <td style="padding: 14px 0; border-bottom: 1px solid #e8e8e8;">
                    <a href="{art['link']}" style="color: #1a1a1a; font-size: 16px; font-weight: 600; text-decoration: none;">
                      {art['title']}
                    </a>
                    {desc_part}
                    <div style="margin-top: 6px; font-size: 13px; color: #666;">
                      {art['pub_date']} &middot;
                      <a href="{art['link']}" style="color: #0066cc; text-decoration: none;">Read article</a>
                    </div>
                  </td>
                </tr>
            """
            articles_html.append(item_html)
            
        section_html = f"""
            <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 28px;">
              <tr>
                <td style="font-size: 20px; font-weight: 700; color: #111; padding-bottom: 10px; border-bottom: 3px solid #111;">
                  {source_name}
                </td>
              </tr>
              {"".join(articles_html)}
            </table>
        """
        sections_html.append(section_html)
        
    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Morning News Digest</title>
</head>
<body style="margin: 0; padding: 0; background: #f4f4f4; font-family: Georgia, 'Times New Roman', serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background: #f4f4f4; padding: 24px 0;">
    <tr>
      <td align="center">
        <table width="640" cellpadding="0" cellspacing="0" style="background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
          <tr>
            <td style="background: #111; color: #fff; padding: 28px 32px;">
              <div style="font-size: 28px; font-weight: 700; letter-spacing: 0.5px;">Pulse</div>
              <div style="font-size: 15px; margin-top: 8px; opacity: 0.9;">Morning News Digest &mdash; {today_str}</div>
            </td>
          </tr>
          <tr>
            <td style="padding: 28px 32px;">
              {"".join(sections_html)}
            </td>
          </tr>
          <tr>
            <td style="padding: 18px 32px; background: #fafafa; font-size: 12px; color: #888; border-top: 1px solid #eee;">
              Sources: BBC News, The Hindu, The Guardian. Sent automatically by Pulse.
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""
    return html

def send_email(subject, html_content):
    sender = os.environ.get("EMAIL_SENDER")
    password = os.environ.get("EMAIL_PASSWORD")
    recipient = os.environ.get("EMAIL_RECIPIENT", sender)

    if not sender or not password:
        print("EMAIL_SENDER and/or EMAIL_PASSWORD environment variables not set. Skipping email send.")
        return False

    password = password.replace(" ", "")
    msg = MIMEText(html_content, "html", "utf-8")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, recipient, msg.as_string())
        print("News digest email sent successfully.")
        return True
    except smtplib.SMTPAuthenticationError as e:
        print("Gmail login failed. Set EMAIL_PASSWORD to a Gmail App Password.")
        print(e)
        return False
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def run():
    print("Pulse News Digest Scraper starting...")
    news_data = {}
    for source in SOURCES:
        name = source["name"]
        url = source["url"]
        print(f"Fetching headlines from {name}...")
        news_data[name] = fetch_feed_articles(name, url)
        
    html_content = generate_html_email(news_data)
    
    # Save the output HTML file locally
    output_filename = "news_digest.html"
    try:
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"Successfully saved locally to {output_filename}")
    except Exception as e:
        print(f"Error saving HTML file locally: {e}")
        
    # Send email
    subject = "Morning News Digest"
    send_email(subject, html_content)
    print("Pulse News Digest Scraper run complete.")

if __name__ == "__main__":
    run()
