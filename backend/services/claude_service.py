"""Anthropic API wrapper"""
from typing import List, Dict, Any, Optional
from anthropic import Anthropic
from backend.config import settings

client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)


def create_message(messages: List[Dict[str, Any]], model: str = "claude-opus-4-6", max_tokens: int = 2000) -> str:
    """Create a message using Claude"""
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=messages  # type: ignore[arg-type]
    )
    # Handle various content block types from Claude
    if hasattr(response.content[0], 'text'):
        return response.content[0].text  # type: ignore[union-attr]
    return ""


def parse_agent_response(content: str) -> Optional[Dict[str, Any]]:
    """Parse structured response from agent"""
    import json
    import re
    json_match = re.search(r'\{.*\}', content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            return None
    return None