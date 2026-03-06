# backend/agents/tools/linkedin_tool.py
"""
LinkedIn lead finder tool.
Uses Google Search to find LinkedIn profiles since LinkedIn's API is heavily restricted.
Respects LinkedIn's terms by only accessing publicly visible information.
"""
from backend.agents.tools.google_search import google_search
from backend.agents.tools.web_scraper import scrape_url


async def find_linkedin_leads(search_query: str, location: str = "") -> dict:
    """
    Find LinkedIn profiles matching the search query.

    Args:
        search_query: e.g. 'marketing manager SaaS startup'
        location: e.g. 'Kenya', 'United States'

    Returns:
        dict with list of LinkedIn profiles/leads
    """
    results = {
        "success": True,
        "query": search_query,
        "location": location,
        "leads": [],
        "total_found": 0,
        "error": None
    }

    try:
        # Build Google search query to find LinkedIn profiles
        location_filter = f" {location}" if location else ""
        google_queries = [
            f"site:linkedin.com/in {search_query}{location_filter}",
            f"site:linkedin.com/company {search_query}{location_filter}",
        ]

        all_leads = []
        seen_urls = set()

        for gquery in google_queries:
            search_result = await google_search(
                query=gquery,
                num_results=10
            )

            if not search_result["success"]:
                continue

            for item in search_result["results"]:
                url = item.get("url", "")
                title = item.get("title", "")
                snippet = item.get("snippet", "")

                # Only include actual LinkedIn profile/company URLs
                if "linkedin.com/in/" not in url and "linkedin.com/company/" not in url:
                    continue

                if url in seen_urls:
                    continue
                seen_urls.add(url)

                # Parse name and title from the LinkedIn result
                name, job_title, company = parse_linkedin_snippet(title, snippet)

                lead_type = "person" if "linkedin.com/in/" in url else "company"

                all_leads.append({
                    "name": name,
                    "job_title": job_title,
                    "company": company,
                    "linkedin_url": url,
                    "profile_summary": snippet,
                    "type": lead_type
                })

        # Also search for decision makers via general web search
        decision_maker_search = await google_search(
            query=f"\"{search_query}\" email contact{location_filter}",
            num_results=5
        )

        if decision_maker_search["success"]:
            for item in decision_maker_search["results"]:
                url = item.get("url", "")
                if url in seen_urls or "linkedin.com" in url:
                    continue
                # Look for pages that might have contact info
                snippet = item.get("snippet", "")
                if any(kw in snippet.lower() for kw in ["contact", "email", "@", "reach out"]):
                    all_leads.append({
                        "name": item.get("title", ""),
                        "job_title": "",
                        "company": "",
                        "linkedin_url": "",
                        "contact_url": url,
                        "profile_summary": snippet,
                        "type": "contact_page"
                    })
                    seen_urls.add(url)

        results["leads"] = all_leads[:20]  # cap at 20 leads
        results["total_found"] = len(all_leads)
        return results

    except Exception as e:
        return {
            "success": False,
            "query": search_query,
            "location": location,
            "leads": [],
            "total_found": 0,
            "error": f"LinkedIn search failed: {str(e)}"
        }


def parse_linkedin_snippet(title: str, snippet: str) -> tuple[str, str, str]:
    """
    Parse name, job title and company from LinkedIn search result.
    LinkedIn titles usually follow: "Name - Job Title at Company | LinkedIn"
    """
    name = ""
    job_title = ""
    company = ""

    # Clean title
    clean_title = title.replace(" | LinkedIn", "").replace(" - LinkedIn", "").strip()

    if " - " in clean_title:
        parts = clean_title.split(" - ", 1)
        name = parts[0].strip()
        rest = parts[1].strip()
        if " at " in rest:
            title_parts = rest.split(" at ", 1)
            job_title = title_parts[0].strip()
            company = title_parts[1].strip()
        else:
            job_title = rest

    elif clean_title:
        name = clean_title

    return name, job_title, company