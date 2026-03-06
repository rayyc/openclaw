# backend/agents/tools/email_tool.py
"""
Email sending tool using Resend API.
Allows agents to send cold outreach emails and follow-ups.
"""
import httpx
from backend.config import settings


async def send_email(
    to_email: str,
    subject: str,
    body: str,
    to_name: str = ""
) -> dict:
    """
    Send an email via Resend API.

    Args:
        to_email: Recipient email address
        subject: Email subject line
        body: Email body (plain text or HTML)
        to_name: Optional recipient name for personalization

    Returns:
        dict with keys: success, message_id, error
    """
    if not settings.RESEND_API_KEY:
        return {
            "success": False,
            "message_id": None,
            "error": "RESEND_API_KEY not configured"
        }

    # Format recipient
    to_address = f"{to_name} <{to_email}>" if to_name else to_email

    # Auto-detect if body is HTML
    is_html = "<" in body and ">" in body

    payload = {
        "from": settings.RESEND_FROM_EMAIL,
        "to": [to_address],
        "subject": subject,
    }

    if is_html:
        payload["html"] = body
    else:
        # Convert plain text to simple HTML for better deliverability
        html_body = body.replace("\n", "<br>")
        payload["html"] = f"<div style='font-family: Arial, sans-serif; font-size: 14px; line-height: 1.6;'>{html_body}</div>"
        payload["text"] = body

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            response.raise_for_status()
            data = response.json()

        return {
            "success": True,
            "message_id": data.get("id"),
            "to": to_email,
            "subject": subject,
            "error": None
        }

    except httpx.HTTPStatusError as e:
        error_detail = ""
        try:
            error_detail = e.response.json().get("message", e.response.text)
        except Exception:
            error_detail = e.response.text
        return {
            "success": False,
            "message_id": None,
            "error": f"Resend API error: {error_detail}"
        }
    except Exception as e:
        return {
            "success": False,
            "message_id": None,
            "error": f"Email sending failed: {str(e)}"
        }