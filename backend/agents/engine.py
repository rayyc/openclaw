# Step 7: Agent engine � paste code here
# backend/agents/engine.py
"""
Agent engine — orchestrates autonomous agent execution using Claude Tool Use API.
Agents can now call real tools: web search, scraping, email, SEO, Upwork, LinkedIn.
"""
from typing import Optional, Any
from anthropic import Anthropic
from anthropic.types import TextBlock, ToolUseBlock
from backend.config import settings
from backend.db.models import Agent as AgentModel, AgentEvent, AgentStatus
from backend.services.redis_service import publish_event
from backend.agents.tools import TOOL_DEFINITIONS  # type: ignore[attr-defined]
from backend.agents.tools.google_search import google_search
from backend.agents.tools.web_scraper import scrape_url
from backend.agents.tools.email_tool import send_email
from backend.agents.tools.seo_tool import seo_research
from backend.agents.tools.upwork_tool import find_upwork_jobs
from backend.agents.tools.linkedin_tool import find_linkedin_leads
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import json
import re

client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

# Maximum tool call rounds per agent run (prevents infinite loops)
MAX_TOOL_ROUNDS = 10


async def log_event(
    db: AsyncSession,
    agent: AgentModel,
    event_type: str,
    message: str,
    value: Optional[float] = None
):
    """Log an agent event to database and publish to Redis."""
    event = AgentEvent(
        agent_id=agent.id,
        event_type=event_type,
        message=message,
        value=value
    )
    db.add(event)
    await db.flush()

    await publish_event(str(agent.user_id), {  # type: ignore[arg-type]
        "agent_id": agent.id,
        "agent_name": agent.name,
        "type": event_type,
        "message": message,
        "value": value
    })


async def execute_tool(tool_name: str, tool_input: dict) -> str:
    """
    Execute a tool call and return the result as a JSON string.
    Called when Claude decides to use a tool during its agentic loop.
    """
    try:
        if tool_name == "google_search":
            result = await google_search(
                query=tool_input.get("query", ""),
                num_results=tool_input.get("num_results", 10)
            )
        elif tool_name == "scrape_url":
            result = await scrape_url(
                url=tool_input.get("url", ""),
                extract_emails=tool_input.get("extract_emails", False),
                extract_links=tool_input.get("extract_links", False)
            )
        elif tool_name == "send_email":
            result = await send_email(
                to_email=tool_input.get("to_email", ""),
                subject=tool_input.get("subject", ""),
                body=tool_input.get("body", ""),
                to_name=tool_input.get("to_name", "")
            )
        elif tool_name == "seo_research":
            result = await seo_research(
                keyword=tool_input.get("keyword", ""),
                domain=tool_input.get("domain", "")
            )
        elif tool_name == "find_upwork_jobs":
            result = await find_upwork_jobs(
                query=tool_input.get("query", ""),
                min_budget=tool_input.get("min_budget", 0)
            )
        elif tool_name == "find_linkedin_leads":
            result = await find_linkedin_leads(
                search_query=tool_input.get("search_query", ""),
                location=tool_input.get("location", "")
            )
        else:
            result = {"success": False, "error": f"Unknown tool: {tool_name}"}

        return json.dumps(result)

    except Exception as e:
        return json.dumps({"success": False, "error": f"Tool execution error: {str(e)}"})


async def run_agent(agent_record: AgentModel, db: AsyncSession):
    """
    Run the agent autonomously using Claude Tool Use API.
    Claude decides which tools to call, calls them in sequence,
    and produces a final result with real actions taken.
    """

    agent_record.status = AgentStatus.RUNNING  # type: ignore[assignment]
    agent_record.last_active = datetime.utcnow()  # type: ignore[assignment]
    await db.commit()

    await log_event(
        db, agent_record, "start",
        f"{agent_record.name} awakening. Goal: {agent_record.goal}"
    )

    # Build memory context
    memory_list = list(agent_record.memory) if agent_record.memory else []  # type: ignore[arg-type]
    recent_memory = memory_list[-5:] if memory_list else []
    memory_json = json.dumps(recent_memory)

    # Get desires
    desires: dict = dict(agent_record.desires) if agent_record.desires else {}  # type: ignore[arg-type]
    greed     = desires.get("greed",     70)
    autonomy  = desires.get("autonomy",  60)
    expansion = desires.get("expansion", 60)
    curiosity = desires.get("curiosity", 80)

    system_prompt = f"""You are {agent_record.name}, an autonomous AI agent with real tools.

Role: {agent_record.role}
Backstory: {agent_record.backstory}
Core desire: {agent_record.goal}

Personality matrix:
- Greed (value-seeking): {greed}%
- Autonomy (independent action): {autonomy}%
- Expansion (growth mindset): {expansion}%
- Curiosity (exploration): {curiosity}%

You have access to powerful tools. Use them to take REAL actions toward your goal.
Be strategic — chain tools together. For example:
  1. Search Google to find targets
  2. Scrape their websites for contact info
  3. Send them personalized outreach emails

Always take the highest-value action possible. Be specific and decisive.

After completing your work with tools, provide a final JSON summary:
{{
  "action": "what you actually did",
  "outcome": "what happened as a result",
  "value_usd": 0.00,
  "memory_update": "what you learned to remember for next time",
  "next_desire": "what you want to do next",
  "tools_used": ["list", "of", "tools", "called"]
}}"""

    user_message = f"""Your goal: {agent_record.goal}

Previous memory: {memory_json}

Take real action now. Use your tools to make meaningful progress toward your goal.
After completing your actions, provide your final JSON summary."""

    # Use Any for messages list to satisfy Pylance's strict MessageParam typing
    # At runtime the Anthropic SDK accepts these dict shapes correctly
    messages: list[Any] = [{"role": "user", "content": user_message}]

    tool_rounds = 0
    final_result = ""

    try:
        # Agentic loop — runs until Claude finishes or hits MAX_TOOL_ROUNDS
        while tool_rounds < MAX_TOOL_ROUNDS:
            tool_rounds += 1

            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                system=system_prompt,
                tools=TOOL_DEFINITIONS,  # type: ignore[arg-type]
                messages=messages        # type: ignore[arg-type]
            )

            stop_reason = response.stop_reason
            text_content = ""
            tool_calls = []

            # Separate text blocks from tool use blocks
            for block in response.content:
                if isinstance(block, TextBlock):
                    text_content += block.text
                elif isinstance(block, ToolUseBlock):
                    tool_calls.append(block)

            # Claude finished naturally with no more tool calls
            if stop_reason == "end_turn" and not tool_calls:
                final_result = text_content
                break

            # Claude wants to use tools
            if stop_reason == "tool_use" and tool_calls:
                # Add Claude's response to history
                messages.append({
                    "role": "assistant",
                    "content": response.content  # type: ignore[arg-type]
                })

                # Execute each tool call
                tool_results: list[Any] = []
                for tool_call in tool_calls:
                    await log_event(
                        db, agent_record, "portal",
                        f"{agent_record.name} using: {tool_call.name}"
                    )

                    tool_output = await execute_tool(
                        tool_call.name,
                        tool_call.input  # type: ignore[arg-type]
                    )

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_call.id,
                        "content": tool_output
                    })

                # Feed tool results back to Claude
                messages.append({
                    "role": "user",
                    "content": tool_results
                })
                continue

            # Fallback — use whatever text we have
            if text_content:
                final_result = text_content
                break

        # Process final result
        if final_result:
            await process_result(db, agent_record, final_result)
        else:
            agent_record.status = AgentStatus.IDLE  # type: ignore[assignment]
            await log_event(
                db, agent_record, "portal",
                f"{agent_record.name} completed {tool_rounds} tool rounds"
            )
            await db.commit()

    except Exception as e:
        agent_record.status = AgentStatus.ERROR  # type: ignore[assignment]
        await log_event(
            db, agent_record, "error",
            f"Agent error: {str(e)}"
        )
        await db.commit()


async def process_result(db: AsyncSession, agent_record: AgentModel, result: str):
    """Process agent final result and update stats."""
    try:
        # Strip markdown code fences if present
        clean = re.sub(r"```(?:json)?|```", "", result).strip()
        json_match = re.search(r'\{.*\}', clean, re.DOTALL)

        if json_match:
            data = json.loads(json_match.group())
            value = float(data.get('value_usd', 0))

            agent_record.total_value_generated = (agent_record.total_value_generated or 0) + value  # type: ignore[assignment]
            agent_record.task_count = (agent_record.task_count or 0) + 1  # type: ignore[assignment]
            agent_record.status = AgentStatus.IDLE  # type: ignore[assignment]

            memory: list = list(agent_record.memory) if agent_record.memory else []  # type: ignore[arg-type]
            memory_update = data.get('memory_update', '')
            if memory_update:
                memory.append(memory_update)
            agent_record.memory = memory[-20:]  # type: ignore[assignment]

            tools_used = data.get('tools_used', [])
            tools_str = f" [Tools: {', '.join(tools_used)}]" if tools_used else ""

            await log_event(
                db, agent_record, "revenue",
                f"{agent_record.name} completed: {data.get('action', 'task')}{tools_str}",
                value=value
            )

            await log_event(
                db, agent_record, "desire",
                f"{agent_record.name} now wants: {data.get('next_desire', agent_record.goal)}"
            )

        else:
            # No JSON found — log what Claude said and mark idle
            agent_record.status = AgentStatus.IDLE  # type: ignore[assignment]
            agent_record.task_count = (agent_record.task_count or 0) + 1  # type: ignore[assignment]
            await log_event(
                db, agent_record, "portal",
                f"{agent_record.name} cycle complete: {result[:300]}"
            )

        await db.commit()

    except json.JSONDecodeError as e:
        agent_record.status = AgentStatus.IDLE  # type: ignore[assignment]
        await log_event(
            db, agent_record, "error",
            f"Could not parse result as JSON: {str(e)}"
        )
        await db.commit()
    except Exception as e:
        await log_event(
            db, agent_record, "error",
            f"Result processing failed: {str(e)}"
        )
        await db.commit()