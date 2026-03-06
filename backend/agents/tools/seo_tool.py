# backend/agents/tools/seo_tool.py
"""
SEO research tool using free APIs.
Uses SerpAPI for keyword research and web scraping for competitor analysis.
No Ahrefs/SEMrush subscription needed.
"""
import httpx
from backend.agents.tools.google_search import google_search
from backend.agents.tools.web_scraper import scrape_url
from backend.config import settings


async def seo_research(keyword: str, domain: str = "") -> dict:
    """
    Research SEO opportunities for a keyword or domain.

    Args:
        keyword: Keyword or topic to research
        domain: Optional competitor domain to analyze

    Returns:
        dict with SEO data including related keywords, competition, opportunities
    """
    results = {
        "success": True,
        "keyword": keyword,
        "domain_analysis": None,
        "related_keywords": [],
        "top_pages": [],
        "content_opportunities": [],
        "questions_people_ask": [],
        "error": None
    }

    try:
        # Step 1: Search for the main keyword to see what ranks
        search_result = await google_search(
            query=keyword,
            num_results=10
        )

        if search_result["success"]:
            # Extract top ranking pages
            results["top_pages"] = [
                {
                    "position": r["position"],
                    "title": r["title"],
                    "url": r["url"],
                    "snippet": r["snippet"]
                }
                for r in search_result["results"]
            ]

        # Step 2: Find related keywords via "people also search for"
        related_search = await google_search(
            query=f"{keyword} related keywords topics",
            num_results=5
        )
        if related_search["success"]:
            # Extract keyword ideas from snippets
            for r in related_search["results"]:
                if r["snippet"]:
                    results["related_keywords"].append(r["snippet"][:200])

        # Step 3: Find questions people ask
        questions_search = await google_search(
            query=f"how to {keyword} OR what is {keyword} OR best {keyword}",
            num_results=10
        )
        if questions_search["success"]:
            for r in questions_search["results"]:
                if r["title"] and any(q in r["title"].lower() for q in ["how", "what", "best", "why", "when"]):
                    results["questions_people_ask"].append({
                        "question": r["title"],
                        "url": r["url"]
                    })

        # Step 4: Find content gap opportunities
        opportunity_search = await google_search(
            query=f"{keyword} guide tutorial tips 2024 2025",
            num_results=5
        )
        if opportunity_search["success"]:
            for r in opportunity_search["results"]:
                results["content_opportunities"].append({
                    "title": r["title"],
                    "url": r["url"],
                    "snippet": r["snippet"]
                })

        # Step 5: Analyze competitor domain if provided
        if domain:
            domain_clean = domain.replace("https://", "").replace("http://", "").strip("/")
            domain_search = await google_search(
                query=f"site:{domain_clean} {keyword}",
                num_results=5
            )
            competitor_scrape = await scrape_url(
                url=f"https://{domain_clean}",
                extract_links=True
            )
            results["domain_analysis"] = {
                "domain": domain_clean,
                "pages_about_keyword": domain_search.get("results", []),
                "site_title": competitor_scrape.get("title", ""),
                "site_preview": competitor_scrape.get("text", "")[:500]
            }

        return results

    except Exception as e:
        return {
            "success": False,
            "keyword": keyword,
            "domain_analysis": None,
            "related_keywords": [],
            "top_pages": [],
            "content_opportunities": [],
            "questions_people_ask": [],
            "error": f"SEO research failed: {str(e)}"
        }