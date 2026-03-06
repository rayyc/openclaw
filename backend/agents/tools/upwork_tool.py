# backend/agents/tools/upwork_tool.py
"""
Upwork job finder tool.
Scrapes Upwork public job listings since their API is invite-only.
Uses Google Search to find Upwork job postings.
"""
from backend.agents.tools.google_search import google_search
from backend.agents.tools.web_scraper import scrape_url


async def find_upwork_jobs(query: str, min_budget: int = 0) -> dict:
    """
    Find freelance jobs on Upwork matching the query.

    Args:
        query: Job search query e.g. 'AI automation python'
        min_budget: Minimum budget filter in USD

    Returns:
        dict with list of matching jobs
    """
    results = {
        "success": True,
        "query": query,
        "jobs": [],
        "total_found": 0,
        "error": None
    }

    try:
        # Search Google for Upwork jobs — more reliable than scraping Upwork directly
        search_queries = [
            f"site:upwork.com/jobs {query}",
            f"upwork.com jobs \"{query}\" hourly fixed-price",
        ]

        all_jobs = []
        seen_urls = set()

        for search_query in search_queries:
            search_result = await google_search(
                query=search_query,
                num_results=10
            )

            if not search_result["success"]:
                continue

            for item in search_result["results"]:
                url = item.get("url", "")
                title = item.get("title", "")
                snippet = item.get("snippet", "")

                # Filter to only Upwork job URLs
                if "upwork.com/jobs" not in url and "upwork.com/freelance-jobs" not in url:
                    continue

                if url in seen_urls:
                    continue
                seen_urls.add(url)

                # Extract budget from snippet if available
                budget = extract_budget_from_text(snippet)

                # Apply budget filter
                if min_budget > 0 and budget is not None and budget < min_budget:
                    continue

                all_jobs.append({
                    "title": title.replace(" | Upwork", "").replace(" - Upwork", "").strip(),
                    "url": url,
                    "description_preview": snippet,
                    "estimated_budget": budget,
                    "source": "upwork"
                })

        # Also search for remote jobs matching the query as backup
        remote_search = await google_search(
            query=f"remote freelance {query} job posting 2025",
            num_results=5
        )

        if remote_search["success"]:
            for item in remote_search["results"]:
                url = item.get("url", "")
                # Skip if already found or not a job site
                if url in seen_urls:
                    continue
                job_keywords = ["job", "freelance", "hire", "looking for", "remote"]
                if any(kw in url.lower() or kw in item.get("snippet", "").lower() for kw in job_keywords):
                    seen_urls.add(url)
                    all_jobs.append({
                        "title": item.get("title", ""),
                        "url": url,
                        "description_preview": item.get("snippet", ""),
                        "estimated_budget": extract_budget_from_text(item.get("snippet", "")),
                        "source": "web"
                    })

        results["jobs"] = all_jobs[:20]  # cap at 20 jobs
        results["total_found"] = len(all_jobs)
        return results

    except Exception as e:
        return {
            "success": False,
            "query": query,
            "jobs": [],
            "total_found": 0,
            "error": f"Job search failed: {str(e)}"
        }


def extract_budget_from_text(text: str):
    """Try to extract a dollar amount from text."""
    import re
    # Match patterns like $50, $1,000, $50/hr, $50-$100
    pattern = r'\$[\d,]+(?:\.\d{1,2})?'
    matches = re.findall(pattern, text)
    if matches:
        try:
            # Return the first match as integer
            amount = int(matches[0].replace("$", "").replace(",", "").split(".")[0])
            return amount
        except ValueError:
            return None
    return None