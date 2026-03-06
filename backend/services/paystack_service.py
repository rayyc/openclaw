"""Paystack integration helpers

Minimal helpers to initialize a Paystack transaction and verify webhooks.
"""
import hashlib
import hmac
import json
import uuid
from typing import Any, Dict, Optional

import httpx
from backend.config import settings

PAYSTACK_BASE = "https://api.paystack.co"


async def initialize_transaction(
    amount: float,
    currency: str,
    email: str,
    reference: str,
    callback_url: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Initialize a Paystack transaction.

    Paystack expects amount in the smallest currency unit (e.g., kobo for NGN).
    We'll convert by multiplying by 100 and casting to int. Adjust if needed.
    """
    if not settings.PAYSTACK_SECRET_KEY:
        raise ValueError("PAYSTACK_SECRET_KEY is not configured in environment variables")
    
    url = f"{PAYSTACK_BASE}/transaction/initialize"
    headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}", "Content-Type": "application/json"}
    payload = {
        "amount": int(amount * 100),
        "currency": currency,
        "email": email,
        "reference": reference,
        "callback_url": callback_url,
        "metadata": metadata or {},
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, json=payload, headers=headers)
        if not resp.is_success:
            error_detail = resp.text
            try:
                error_json = resp.json()
                error_detail = error_json.get("message") or error_detail
            except:
                pass
            raise httpx.HTTPStatusError(
                f"Paystack API Error ({resp.status_code}): {error_detail}",
                request=resp.request,
                response=resp
            )
        return resp.json()


async def verify_transaction(reference: str) -> Dict[str, Any]:
    url = f"{PAYSTACK_BASE}/transaction/verify/{reference}"
    headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json()


def verify_webhook_signature(signature_header: Optional[str], body: bytes) -> bool:
    """Verify Paystack webhook signature.

    Paystack signs the request body using HMAC-SHA512 with the secret key and
    returns the signature in the `x-paystack-signature` header.
    """
    if not signature_header or not settings.PAYSTACK_SECRET_KEY:
        return False

    computed = hmac.new(settings.PAYSTACK_SECRET_KEY.encode(), body, hashlib.sha512).hexdigest()
    return hmac.compare_digest(computed, signature_header)


def generate_reference(user_id: str, tier: str) -> str:
    return f"{user_id}-{tier}-{uuid.uuid4().hex[:8]}"
