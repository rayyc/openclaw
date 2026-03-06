"""Agent routes"""
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from backend.db.database import get_db
from backend.db.models import Agent, AgentEvent, User, SubscriptionTier, AgentType
from backend.api.middleware import get_current_user
from backend.agents.tasks import run_agent_task
from pydantic import BaseModel


router = APIRouter(prefix="/agents", tags=["agents"])


TIER_LIMITS = {
    SubscriptionTier.FREE:      1,
    SubscriptionTier.STARTER:   2,
    SubscriptionTier.EMPIRE:    10,
    SubscriptionTier.UNLIMITED: 999,
    SubscriptionTier.ADMIN:     999,
}


# ── Request models ─────────────────────────────────────────────────────────────

class DeployAgentRequest(BaseModel):
    """Deploy a standard agent (web search, email, SEO, Upwork, LinkedIn)."""
    name: str
    role: str
    goal: str
    backstory: str
    desires: Dict[str, int] = {
        "greed": 50,
        "autonomy": 50,
        "expansion": 50,
        "curiosity": 50
    }


class DeployTradingAgentRequest(BaseModel):
    """Deploy a trading agent (Deriv MT5 forex and commodities)."""
    name: str
    goal: str
    # Which pairs to trade — validated against allowed symbols
    trading_pairs: List[str] = ["EURUSD", "XAUUSD"]
    # conservative = 0.01 lots | moderate = 0.05 lots | aggressive = 0.10 lots
    stake_level: str = "conservative"


# ── Allowed trading symbols ────────────────────────────────────────────────────
ALLOWED_TRADING_PAIRS = {
    # Forex majors
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF",
    "AUDUSD", "USDCAD", "NZDUSD",
    # Forex minors
    "EURGBP", "EURJPY", "GBPJPY",
    "EURCAD", "GBPCAD", "AUDCAD",
    # Commodities
    "XAUUSD", "XAGUSD", "USOIL", "UKOIL",
}

ALLOWED_STAKE_LEVELS = {"conservative", "moderate", "aggressive"}


# ── Helper ─────────────────────────────────────────────────────────────────────

async def check_agent_limit(db: AsyncSession, user: User) -> None:
    """Raise 403 if user has reached their agent limit."""
    if user.is_admin:  # type: ignore
        return  # admins unlimited
    result = await db.execute(select(Agent).where(Agent.user_id == user.id))
    existing = result.scalars().all()
    limit = TIER_LIMITS.get(user.tier, 1)  # type: ignore
    if len(existing) >= limit:
        raise HTTPException(
            403,
            f"Your {user.tier.value} plan allows {limit} agent(s). Upgrade to deploy more."  # type: ignore
        )


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.post("/deploy")
async def deploy_agent(
    payload: DeployAgentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Deploy a standard agent with tool access (search, email, SEO, Upwork, LinkedIn)."""
    await check_agent_limit(db, current_user)

    agent = Agent(
        user_id=current_user.id,
        name=payload.name,
        role=payload.role,
        goal=payload.goal,
        backstory=payload.backstory,
        desires=payload.desires,
        agent_type=AgentType.STANDARD,
        stake_level="conservative",  # not used for standard agents
        trading_pairs=[],
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)

    run_agent_task.delay(str(agent.id))
    return {
        "agent_id": agent.id,
        "agent_type": "standard",
        "status": "deploying",
        "message": f"{agent.name} is awakening"
    }


@router.post("/deploy/trading")
async def deploy_trading_agent(
    payload: DeployTradingAgentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Deploy a trading agent that trades forex and commodities on Deriv MT5."""
    await check_agent_limit(db, current_user)

    # Validate trading pairs
    invalid_pairs = [p for p in payload.trading_pairs if p.upper() not in ALLOWED_TRADING_PAIRS]
    if invalid_pairs:
        raise HTTPException(
            400,
            f"Invalid trading pairs: {invalid_pairs}. "
            f"Allowed: {sorted(ALLOWED_TRADING_PAIRS)}"
        )

    # Validate stake level
    if payload.stake_level not in ALLOWED_STAKE_LEVELS:
        raise HTTPException(
            400,
            f"Invalid stake_level '{payload.stake_level}'. "
            f"Must be one of: {sorted(ALLOWED_STAKE_LEVELS)}"
        )

    # Normalize pairs to uppercase
    pairs = [p.upper() for p in payload.trading_pairs]

    agent = Agent(
        user_id=current_user.id,
        name=payload.name,
        role="Forex & Commodities Trader",
        goal=payload.goal,
        backstory=(
            f"An expert AI trader specializing in forex pairs and commodities. "
            f"Trading {', '.join(pairs)} with {payload.stake_level} risk. "
            f"Uses multi-timeframe analysis, technical indicators, and news sentiment "
            f"to identify high-confidence trade setups on Deriv MT5."
        ),
        desires={
            "greed": 60,
            "autonomy": 80,
            "expansion": 50,
            "curiosity": 70,
            "stake_level": payload.stake_level
        },
        agent_type=AgentType.TRADING,
        trading_pairs=pairs,
        stake_level=payload.stake_level,
        memory=[],
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)

    run_agent_task.delay(str(agent.id))
    return {
        "agent_id": agent.id,
        "agent_type": "trading",
        "trading_pairs": pairs,
        "stake_level": payload.stake_level,
        "status": "deploying",
        "message": f"{agent.name} connecting to Deriv MT5..."
    }


@router.get("/")
async def list_agents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all agents for the current user."""
    result = await db.execute(select(Agent).where(Agent.user_id == current_user.id))
    agents = result.scalars().all()
    return agents


@router.get("/{agent_id}/events")
async def get_events(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get recent events for a specific agent."""
    agent_result = await db.execute(
        select(Agent).where(and_(Agent.id == agent_id, Agent.user_id == current_user.id))
    )
    agent = agent_result.scalar_one_or_none()
    if agent is None:  # type: ignore
        raise HTTPException(404, "Agent not found")

    events_result = await db.execute(
        select(AgentEvent)
        .where(AgentEvent.agent_id == agent_id)
        .order_by(AgentEvent.created_at.desc())
        .limit(50)
    )
    return events_result.scalars().all()


@router.post("/{agent_id}/run")
async def trigger_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Manually trigger an agent run."""
    result = await db.execute(
        select(Agent).where(and_(Agent.id == agent_id, Agent.user_id == current_user.id))
    )
    agent = result.scalar_one_or_none()
    if agent is None:  # type: ignore
        raise HTTPException(404, "Agent not found")

    run_agent_task.delay(str(agent.id))
    return {"status": "running", "agent_id": agent_id}


@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an agent and all its events."""
    result = await db.execute(
        select(Agent).where(and_(Agent.id == agent_id, Agent.user_id == current_user.id))
    )
    agent = result.scalar_one_or_none()
    if agent is None:  # type: ignore
        raise HTTPException(404, "Agent not found")

    await db.delete(agent)
    await db.commit()
    return {"deleted": True}