# backend/agents/tools/google_search.py
"""
Google Search tool using SerpAPI.
Allows agents to search Google and get real results.
"""
import httpx
from backend.config import settings


async def google_search(query: str, num_results: int = 10) -> dict:
    """
    Search Google via SerpAPI and return structured results.
    
    Args:
        query: Search query string
        num_results: Number of results to return (max 20)
    
    Returns:
        dict with keys: success, results, error
    """
    if not settings.SERPAPI_KEY:
        return {
            "success": False,
            "results": [],
            "error": "SERPAPI_KEY not configured"
        }

    num_results = min(num_results, 20)

    params = {
        "api_key": settings.SERPAPI_KEY,
        "engine": "google",
        "q": query,
        "num": num_results,
        "hl": "en",
        "gl": "us"
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                "https://serpapi.com/search",
                params=params
            )
            response.raise_for_status()
            data = response.json()

        results = []

        # Extract organic results
        for item in data.get("organic_results", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "snippet": item.get("snippet", ""),
                "position": item.get("position", 0)
            })

        # Extract knowledge graph if available
        knowledge = data.get("knowledge_graph", {})
        knowledge_summary = ""
        if knowledge:
            knowledge_summary = f"{knowledge.get('title', '')} - {knowledge.get('description', '')}"

        return {
            "success": True,
            "query": query,
            "total_results": data.get("search_information", {}).get("total_results", "unknown"),
            "results": results,
            "knowledge_summary": knowledge_summary,
            "error": None
        }

    except httpx.HTTPStatusError as e:
        return {
            "success": False,
            "results": [],
            "error": f"SerpAPI HTTP error: {e.response.status_code} - {e.response.text}"
        }
    except Exception as e:
        return {
            "success": False,
            "results": [],
            "error": f"Search failed: {str(e)}"
        }