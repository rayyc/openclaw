from fastapi import APIRouter, Request, Depends, HTTPException
from backend.config import settings
from backend.db.database import get_db
from backend.db.models import User, SubscriptionTier
from backend.api.middleware import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.services import paystack_service as ps
import json
import httpx
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["billing"])

# Configure your price amounts (USD)
PRICE_AMOUNTS = {
    "starter": 29.0,
    "empire": 99.0,
    "unlimited": 299.0,
}

TIER_LIMITS = {"starter": 2, "empire": 10, "unlimited": 999}

@router.post("/checkout/{tier}")
async def create_checkout(
    tier: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if tier not in PRICE_AMOUNTS:
        raise HTTPException(400, "Invalid tier")

    # Admins skip payment
    if current_user.is_admin:  # type: ignore
        logger.info(f"Admin {current_user.id} accessing tier {tier} without payment")
        return {"checkout_url": None, "message": "Admin access - no payment required"}

    amount = PRICE_AMOUNTS[tier]

    try:
        reference = ps.generate_reference(str(current_user.id), tier)
        logger.info(f"Initializing Paystack transaction for user {current_user.id}, tier {tier}, amount {amount}")
        
        resp = await ps.initialize_transaction(
            amount=amount,
            currency="USD",
            email=str(current_user.email),  # type: ignore
            reference=reference,
            callback_url=f"{settings.FRONTEND_URL}/dashboard?upgraded=true",
            metadata={"user_id": str(current_user.id), "tier": tier},
        )

        # Paystack returns authorization URL in resp['data']['authorization_url']
        link = None
        if isinstance(resp, dict):
            link = resp.get("data", {}).get("authorization_url")

        if not link:
            logger.error(f"No authorization URL in Paystack response: {resp}")
            raise HTTPException(500, "Failed to create Paystack checkout link")

        logger.info(f"Paystack checkout created successfully for user {current_user.id}")
        return {"checkout_url": link}
    except httpx.HTTPStatusError as e:
        error_msg = f"Paystack API error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(400, error_msg)
    except ValueError as e:
        error_msg = f"Configuration error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(500, error_msg)
    except Exception as e:
        error_msg = f"Payment error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(400, error_msg)

@router.post("/webhook")
async def paystack_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    # Paystack sends JSON webhook payloads and signs the raw body using HMAC-SHA512
    raw = await request.body()
    sig = request.headers.get("x-paystack-signature")

    if not ps.verify_webhook_signature(sig, raw):
        raise HTTPException(400, "Invalid webhook signature")

    payload = json.loads(raw.decode()) if raw else {}
    event = payload.get("event") or payload.get("event_name")
    data = payload.get("data") or {}

    # Paystack emits 'charge.success' on successful payments
    if event in ("charge.success", "charge.completed") or data.get("status") == "success":
        meta = data.get("metadata") or {}
        user_id = meta.get("user_id")
        tier = meta.get("tier")

        if user_id and tier:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if user is not None:  # type: ignore
                user.tier = SubscriptionTier(tier)  # type: ignore
                user.agent_limit = TIER_LIMITS.get(tier, 1)  # type: ignore
                user.stripe_customer_id = data.get("customer", {}).get("id") if isinstance(data.get("customer"), dict) else None  # type: ignore
                user.stripe_subscription_id = data.get("id") or data.get("reference")  # type: ignore
                await db.commit()

    return {"received": True}
