"""Agent tool exports and Anthropic tool definitions."""

from .email_tool import send_email
from .google_search import google_search
from .linkedin_tool import find_linkedin_leads
from .seo_tool import seo_research
from .upwork_tool import find_upwork_jobs
from .web_scraper import scrape_url

TOOL_DEFINITIONS = [
    {
        "name": "google_search",
        "description": "Search the web for public information using a search engine API.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to run.",
                },
                "num_results": {
                    "type": "integer",
                    "description": "How many results to return. Defaults to 10.",
                    "default": 10,
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "scrape_url",
        "description": "Fetch and extract text from a web page, optionally including links and email addresses.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The full URL to scrape.",
                },
                "extract_emails": {
                    "type": "boolean",
                    "description": "Whether to extract email addresses from the page.",
                    "default": False,
                },
                "extract_links": {
                    "type": "boolean",
                    "description": "Whether to extract links from the page.",
                    "default": False,
                },
            },
            "required": ["url"],
        },
    },
    {
        "name": "send_email",
        "description": "Send an email to a recipient using a configured email provider.",
        "input_schema": {
            "type": "object",
            "properties": {
                "to_email": {
                    "type": "string",
                    "description": "Recipient email address.",
                },
                "subject": {
                    "type": "string",
                    "description": "Email subject line.",
                },
                "body": {
                    "type": "string",
                    "description": "Email body content.",
                },
                "to_name": {
                    "type": "string",
                    "description": "Optional recipient name.",
                    "default": "",
                },
            },
            "required": ["to_email", "subject", "body"],
        },
    },
    {
        "name": "seo_research",
        "description": "Research SEO opportunities or competitor information for a keyword or domain.",
        "input_schema": {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "The keyword or topic to research.",
                },
                "domain": {
                    "type": "string",
                    "description": "Optional competitor domain to analyze.",
                    "default": "",
                },
            },
            "required": ["keyword"],
        },
    },
    {
        "name": "find_upwork_jobs",
        "description": "Find freelance job postings on Upwork that match a query.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query for the kind of job to find.",
                },
                "min_budget": {
                    "type": "integer",
                    "description": "Minimum budget in USD to filter by.",
                    "default": 0,
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "find_linkedin_leads",
        "description": "Find LinkedIn profiles or companies that match a target search query.",
        "input_schema": {
            "type": "object",
            "properties": {
                "search_query": {
                    "type": "string",
                    "description": "The search query for the lead to find.",
                },
                "location": {
                    "type": "string",
                    "description": "Optional location to narrow the search.",
                    "default": "",
                },
            },
            "required": ["search_query"],
        },
    },
]

__all__ = [
    "TOOL_DEFINITIONS",
    "google_search",
    "scrape_url",
    "send_email",
    "seo_research",
    "find_upwork_jobs",
    "find_linkedin_leads",
]
