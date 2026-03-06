# Step 11: Redis pub/sub � paste code here
# backend/services/redis_service.py
"""Redis pub/sub helpers — fresh connection per call for Windows Celery compatibility."""
from typing import Dict, Any, AsyncGenerator
import redis.asyncio as redis
from backend.config import settings
import json


def _get_redis() -> redis.Redis:
    """
    Create a fresh Redis client for every call.
    Module-level singletons break on Windows when Celery closes the event
    loop between tasks — the bound connection's proactor becomes None.
    A fresh client connects on the new loop with no stale state.
    """
    return redis.from_url(settings.REDIS_URL)


async def publish_event(user_id: str, event: Dict[str, Any]) -> None:
    r = _get_redis()
    try:
        await r.publish(f"events:{user_id}", json.dumps(event))
    finally:
        await r.aclose()


async def subscribe_to_events(user_id: str) -> AsyncGenerator[Dict[str, Any], None]:
    r = _get_redis()
    pubsub = r.pubsub()
    await pubsub.subscribe(f"events:{user_id}")
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                yield json.loads(message["data"])
    finally:
        await pubsub.unsubscribe(f"events:{user_id}")
        await r.aclose()