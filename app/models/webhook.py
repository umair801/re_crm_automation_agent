"""
Pydantic models for incoming GHL webhook payloads.
"""

from pydantic import BaseModel
from typing import Any, Optional


class GHLWebhookPayload(BaseModel):
    """Base model for all incoming GHL webhook events."""
    type: str
    locationId: Optional[str] = None
    contactId: Optional[str] = None
    conversationId: Optional[str] = None
    messageId: Optional[str] = None
    body: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    data: Optional[dict[str, Any]] = None


class ConversationSyncRequest(BaseModel):
    """Payload for syncing an AI agent message into GHL inbox."""
    ghl_contact_id: str
    message: str
    direction: str = "outbound"
    channel: str = "sms"