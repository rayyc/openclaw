# backend/agents/tools/web_scraper.py
"""
Web scraper tool using ScraperAPI for proxy rotation + BeautifulSoup for parsing.
Allows agents to extract content, emails, and links from any webpage.
"""
import httpx
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from backend.config import settings


def extract_emails_from_text(text: str) -> list[str]:
    """Extract all email addresses from a block of text."""
    pattern = r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Z|a-z]{2,}\b'
    emails  = re.findall(pattern, text)
    filtered: list[str] = []
    seen: set[str] = set()
    skip_domains = {"example.com", "test.com", "yourdomain.com", "email.com", "sentry.io"}
    for email in emails:
        email_lower = email.lower()
        domain = email_lower.split("@")[-1]
        if email_lower not in seen and domain not in skip_domains:
            seen.add(email_lower)
            filtered.append(email_lower)
    return filtered


async def scrape_url(
    url: str,
    extract_emails: bool = False,
    extract_links: bool = False
) -> dict:
    """
    Scrape a webpage and return its content.

    Args:
        url: Full URL to scrape
        extract_emails: Whether to extract email addresses
        extract_links: Whether to extract all links

    Returns:
        dict with keys: success, url, title, text, emails, links, error
    """
    if not settings.SCRAPER_API_KEY:
        scraper_url = url
        params: dict = {}
    else:
        scraper_url = "http://api.scraperapi.com"
        params = {
            "api_key": settings.SCRAPER_API_KEY,
            "url":     url,
            "render":  "false"
        }

    try:
        async with httpx.AsyncClient(timeout=45, follow_redirects=True) as client:
            if params:
                response = await client.get(scraper_url, params=params)
            else:
                response = await client.get(
                    scraper_url,
                    headers={
                        "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
                        "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.5",
                    }
                )
            response.raise_for_status()
            html = response.text

        soup = BeautifulSoup(html, "lxml")

        # Remove noise tags
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        # Title
        title = ""
        if soup.title:
            title = soup.title.get_text(strip=True)

        # Clean text
        text = soup.get_text(separator=" ", strip=True)
        text = re.sub(r'\s+', ' ', text).strip()
        text_preview = text[:5000]

        # Extract emails
        emails: list[str] = []
        if extract_emails:
            emails = extract_emails_from_text(text)
            for a in soup.find_all("a"):
                # ── Use .attrs dict to avoid BeautifulSoup _AttributeValue
                #    typing issues with Pylance ────────────────────────────────
                href_raw = a.attrs.get("href", "")
                href = str(href_raw) if href_raw else ""
                if href.startswith("mailto:"):
                    email = href.replace("mailto:", "").split("?")[0].strip().lower()
                    if email and email not in emails:
                        emails.append(email)

        # Extract links
        links: list[dict] = []
        if extract_links:
            base_domain = urlparse(url).netloc
            for a in soup.find_all("a"):
                # ── Use .attrs dict for href to avoid urljoin type error ───────
                href_raw = a.attrs.get("href", "")
                href = str(href_raw) if href_raw else ""
                if not href:
                    continue
                full_url = urljoin(url, href)
                parsed   = urlparse(full_url)
                if parsed.scheme in ("http", "https"):
                    links.append({
                        "text":     a.get_text(strip=True)[:100],
                        "url":      full_url,
                        "internal": parsed.netloc == base_domain
                    })

            # Deduplicate
            seen_urls: set[str] = set()
            unique_links: list[dict] = []
            for link in links:
                if link["url"] not in seen_urls:
                    seen_urls.add(link["url"])
                    unique_links.append(link)
            links = unique_links[:50]

        return {
            "success":    True,
            "url":        url,
            "title":      title,
            "text":       text_preview,
            "word_count": len(text.split()),
            "emails":     emails,
            "links":      links,
            "error":      None
        }

    except httpx.HTTPStatusError as e:
        return {
            "success": False,
            "url":     url,
            "title":   "",
            "text":    "",
            "emails":  [],
            "links":   [],
            "error":   f"HTTP {e.response.status_code} when scraping {url}"
        }
    except Exception as e:
        return {
            "success": False,
            "url":     url,
            "title":   "",
            "text":    "",
            "emails":  [],
            "links":   [],
            "error":   f"Scraping failed: {str(e)}"
        }