
import os
import re
import time
import smtplib
import requests
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib.parse import urlparse, parse_qs, urljoin
from datetime import datetime, timezone

# ------------- Settings -------------
QUERY = os.environ.get("JOB_QUERY", '("Planning Engineer" OR "Project Planning Engineer")')
REGIONS = os.environ.get("JOB_REGIONS", "Saudi Arabia,Remote").split(",")
SITES = os.environ.get("JOB_SITES", "linkedin.com/jobs,indeed.com,bayt.com,gulftalent.com,glassdoor.com").split(",")
RESULTS_LIMIT = int(os.environ.get("RESULTS_LIMIT", "40"))  # total emails to send
PAUSE_BETWEEN_QUERIES = float(os.environ.get("PAUSE_SECONDS", "1.0"))
TIME_FILTER = os.environ.get("TIME_FILTER", "d")  # h (hour), d (day), w (week), m (month)

SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "465"))
EMAIL_USER = os.environ["EMAIL_USER"]
EMAIL_PASS = os.environ["EMAIL_PASS"]
EMAIL_RECEIVER = os.environ["EMAIL_RECEIVER"]

# ------------- Helpers -------------
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/119.0.0.0 Safari/537.36"
    )
}

def clean_google_url(href: str) -> str:
    """Extract the real URL from a Google result link like '/url?q=...&sa=U&...'."""
    if not href:
        return ""
    if href.startswith("/url?"):
        q = parse_qs(urlparse(href).query)
        if "q" in q:
            return q["q"][0]
    return href

def domain_of(url: str) -> str:
    try:
        return urlparse(url).netloc.replace("www.", "")
    except Exception:
        return ""

def google_search(query: str, tbs_time="d"):
    # tbs=qdr:d -> past day; h,w,m are alternatives
    url = "https://www.google.com/search"
    params = {"q": query, "num": "20", "hl": "en", "tbs": f"qdr:{tbs_time}"}
    resp = requests.get(url, params=params, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    return resp.text

def parse_results(html, allowed_domains):
    soup = BeautifulSoup(html, "html.parser")
    results = []
    for a in soup.select("a"):
        href = a.get("href", "")
        text = " ".join(a.get_text(" ", strip=True).split())
        url = clean_google_url(href)
        if not url.startswith("http"):
            continue
        d = domain_of(url)
        if not d or all(ad not in d for ad in allowed_domains):
            continue
        # Simple noise filters
        if "webcache.googleusercontent.com" in url or "/policies" in url:
            continue
        # Some titles are too generic
        if len(text) < 12:
            continue
        results.append({"title": text, "url": url, "domain": d})
    return results

def dedupe(results):
    seen = set()
    unique = []
    for r in results:
        key = (r["domain"], r["title"].lower())
        if key in seen:
            continue
        seen.add(key)
        unique.append(r)
    return unique

def fetch_jobs():
    collected = []
    for region in REGIONS:
        query = f'{QUERY} site:({" OR ".join(SITES)}) "{region}"'
        try:
            html = google_search(query, tbs_time=TIME_FILTER)
            items = parse_results(html, allowed_domains=SITES)
            collected.extend(items)
        except Exception as e:
            collected.append({"title": f"[Error fetching results for {region}: {e}]", "url": "", "domain": ""})
        time.sleep(PAUSE_BETWEEN_QUERIES)
    collected = dedupe(collected)
    # Cap to limit
    return collected[:RESULTS_LIMIT]

def build_email_html(jobs):
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    groups = {}
    for j in jobs:
        groups.setdefault(j["domain"], []).append(j)
    sections = []
    for dom, items in sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        lis = "\n".join(f"<li><a href='{j['url']}' target='_blank' rel='noopener'>{j['title']}</a></li>" for j in items)
        sections.append(f"<h3 style='margin:16px 0'>{dom}</h3><ul>{lis}</ul>")
    body = f"""
    <div>
      <h2 style="margin:0 0 8px">Planning Engineer Jobs — Daily Digest</h2>
      <p style="margin:0 0 16px; font-size:14px; color:#555">Generated: {now_utc}</p>
      {''.join(sections) if sections else '<p>No results found today.</p>'}
      <hr/>
      <p style="font-size:12px; color:#777">Filters: QUERY={QUERY}, REGIONS={REGIONS}, SITES={SITES}, TIME_FILTER={TIME_FILTER}</p>
    </div>
    """
    return body

def send_email_html(subject, html):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_USER
    msg["To"] = EMAIL_RECEIVER
    msg.attach(MIMEText(html, "html"))
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, EMAIL_RECEIVER, msg.as_string())

if __name__ == "__main__":
    jobs = fetch_jobs()
    html = build_email_html(jobs)
    send_email_html(
        subject=f"Daily Planning Engineer Jobs — {datetime.utcnow().strftime('%Y-%m-%d')}",
        html=html,
    )
