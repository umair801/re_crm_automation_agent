"""
FastAPI router for receiving and processing GHL webhook events.
"""

import hmac
import hashlib
import structlog
from fastapi import APIRouter, HTTPException, Request, Header
from typing import Optional
from app.models.webhook import GHLWebhookPayload, ConversationSyncRequest
from app.clients.ghl_client import GHLClient
from app.clients.supabase_client import SupabaseClient
from app.utils.config import settings

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


def verify_ghl_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify the GHL webhook HMAC signature."""
    expected = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/ghl")
async def receive_ghl_webhook(
    request: Request,
    x_ghl_signature: Optional[str] = Header(None),
) -> dict:
    """
    Receive all GHL webhook events.
    Verifies signature, logs the event, and routes by event type.
    """
    raw_body = await request.body()

    # Signature verification (skip in development if secret is placeholder)
    if settings.GHL_WEBHOOK_SECRET != "your_ghl_webhook_secret_here":
        if not x_ghl_signature:
            raise HTTPException(status_code=401, detail="Missing webhook signature")
        if not verify_ghl_signature(raw_body, x_ghl_signature, settings.GHL_WEBHOOK_SECRET):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        payload_dict = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_type = payload_dict.get("type", "unknown")
    contact_id = payload_dict.get("contactId")

    logger.info("ghl_webhook_received", event_type=event_type, contact_id=contact_id)

    # Write to audit log
    db = SupabaseClient()
    await db.write_audit_log(
        event_type=f"ghl_webhook_{event_type}",
        source="ghl_webhook",
        status="success",
        ghl_contact_id=contact_id,
        payload=payload_dict,
    )

    return {
        "status": "received",
        "event_type": event_type,
        "contact_id": contact_id,
    }


@router.post("/conversation-sync")
async def sync_conversation_message(request: ConversationSyncRequest) -> dict:
    """
    Receive a message from the AI agent platform via n8n
    and post it into the GHL unified inbox.
    """
    logger.info("conversation_sync_received", contact_id=request.ghl_contact_id)

    try:
        ghl = GHLClient()
        db = SupabaseClient()

        # Send message via GHL
        await ghl.send_sms(request.ghl_contact_id, request.message)

        # Log conversation to Supabase
        await db.log_conversation({
            "ghl_contact_id": request.ghl_contact_id,
            "message_body": request.message,
            "direction": request.direction,
            "channel": request.channel,
        })

        await db.write_audit_log(
            event_type="conversation_synced",
            source="fastapi",
            status="success",
            ghl_contact_id=request.ghl_contact_id,
            payload={"message_length": len(request.message)},
        )

        return {"status": "sent", "contact_id": request.ghl_contact_id}

    except Exception as e:
        logger.error("conversation_sync_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))