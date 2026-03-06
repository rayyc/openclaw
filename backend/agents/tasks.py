# Step 8: Celery background tasks � paste code here
# backend/agents/tasks.py
from celery import Celery
from backend.config import settings

celery_app = Celery(
    "openclaw",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

def _get_async_db_url() -> str:
    """
    Ensure the database URL uses the asyncpg driver.
    settings.DATABASE_URL may be postgresql:// (psycopg2) or
    postgresql+asyncpg:// depending on how config.py is set.
    create_async_engine REQUIRES the asyncpg variant.
    """
    url = settings.DATABASE_URL
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


@celery_app.task
def run_agent_task(agent_id: str):
    import asyncio
    import sys

    async def _run():
        from sqlalchemy.ext.asyncio import (
            create_async_engine,
            AsyncSession,
            async_sessionmaker
        )
        from backend.db.models import Agent, AgentType
        from sqlalchemy import select

        # Use asyncpg URL — psycopg2 URL causes InvalidRequestError
        async_url = _get_async_db_url()

        engine = create_async_engine(
            async_url,
            pool_size=1,
            max_overflow=0,
            pool_pre_ping=True
        )

        SessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        try:
            async with SessionLocal() as db:
                result = await db.execute(select(Agent).where(Agent.id == agent_id))
                agent  = result.scalar_one_or_none()

                if agent is None:
                    print(f"[CELERY] Agent {agent_id} not found in database")
                    return

                agent_type = agent.agent_type

                if agent_type == AgentType.TRADING:  # type: ignore[comparison-overlap]
                    from backend.agents.trading_engine import run_trading_agent
                    await run_trading_agent(agent, db)
                else:
                    from backend.agents.engine import run_agent
                    await run_agent(agent, db)

        except Exception as e:
            print(f"[CELERY] Task failed for agent {agent_id}: {e}")
            raise
        finally:
            await engine.dispose()

    # ── Windows: fresh event loop per task ────────────────────────────────────
    if sys.platform == "win32":
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_run())
        finally:
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()
            asyncio.set_event_loop(None)
    else:
        asyncio.run(_run())