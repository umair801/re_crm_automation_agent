"""
Supabase database client.
Handles all read/write operations for leads, conversations, qualification results, pipeline events, and audit logs.
"""

import structlog
from typing import Any, Optional
from supabase import create_client, Client
from app.utils.config import settings

logger = structlog.get_logger(__name__)


class SupabaseClientError(Exception):
    """Raised when a Supabase operation fails."""
    pass


class SupabaseClient:
    """Centralized Supabase database client for all table operations."""

    def __init__(self) -> None:
        self.client: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY,
        )

    # ------------------------------------------------------------------
    # LEADS
    # ------------------------------------------------------------------

    async def upsert_lead(self, lead_data: dict[str, Any]) -> dict[str, Any]:
        """Insert or update a lead record by ghl_contact_id."""
        try:
            response = (
                self.client.table("crm_leads")
                .upsert(lead_data, on_conflict="ghl_contact_id")
                .execute()
            )
            logger.info("lead_upserted", ghl_contact_id=lead_data.get("ghl_contact_id"))
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error("lead_upsert_error", error=str(e))
            raise SupabaseClientError(f"Failed to upsert lead: {e}")

    async def get_lead_by_contact_id(self, ghl_contact_id: str) -> Optional[dict[str, Any]]:
        """Fetch a lead record by GHL contact ID."""
        try:
            response = (
                self.client.table("crm_leads")
                .select("*")
                .eq("ghl_contact_id", ghl_contact_id)
                .single()
                .execute()
            )
            return response.data
        except Exception as e:
            logger.warning("lead_not_found", ghl_contact_id=ghl_contact_id, error=str(e))
            return None

    async def update_lead(self, ghl_contact_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        """Update specific fields on a lead record."""
        try:
            response = (
                self.client.table("crm_leads")
                .update(updates)
                .eq("ghl_contact_id", ghl_contact_id)
                .execute()
            )
            logger.info("lead_updated", ghl_contact_id=ghl_contact_id)
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error("lead_update_error", error=str(e))
            raise SupabaseClientError(f"Failed to update lead: {e}")

    # ------------------------------------------------------------------
    # CONVERSATIONS
    # ------------------------------------------------------------------

    async def log_conversation(self, conversation_data: dict[str, Any]) -> dict[str, Any]:
        """Log a single conversation message."""
        try:
            response = (
                self.client.table("crm_conversations")
                .insert(conversation_data)
                .execute()
            )
            logger.info("conversation_logged", ghl_contact_id=conversation_data.get("ghl_contact_id"))
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error("conversation_log_error", error=str(e))
            raise SupabaseClientError(f"Failed to log conversation: {e}")

    async def get_conversations_by_contact(self, ghl_contact_id: str) -> list[dict[str, Any]]:
        """Retrieve all conversation messages for a contact."""
        try:
            response = (
                self.client.table("crm_conversations")
                .select("*")
                .eq("ghl_contact_id", ghl_contact_id)
                .order("sent_at", desc=False)
                .execute()
            )
            return response.data or []
        except Exception as e:
            logger.error("conversation_fetch_error", error=str(e))
            raise SupabaseClientError(f"Failed to fetch conversations: {e}")

    # ------------------------------------------------------------------
    # QUALIFICATION RESULTS
    # ------------------------------------------------------------------

    async def save_qualification_result(self, result_data: dict[str, Any]) -> dict[str, Any]:
        """Save a GPT-4o qualification result for a lead."""
        try:
            response = (
                self.client.table("crm_qualification_results")
                .insert(result_data)
                .execute()
            )
            logger.info("qualification_saved", ghl_contact_id=result_data.get("ghl_contact_id"))
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error("qualification_save_error", error=str(e))
            raise SupabaseClientError(f"Failed to save qualification result: {e}")

    async def get_latest_qualification(self, ghl_contact_id: str) -> Optional[dict[str, Any]]:
        """Retrieve the most recent qualification result for a contact."""
        try:
            response = (
                self.client.table("crm_qualification_results")
                .select("*")
                .eq("ghl_contact_id", ghl_contact_id)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error("qualification_fetch_error", error=str(e))
            raise SupabaseClientError(f"Failed to fetch qualification: {e}")

    # ------------------------------------------------------------------
    # PIPELINE EVENTS
    # ------------------------------------------------------------------

    async def log_pipeline_event(self, event_data: dict[str, Any]) -> dict[str, Any]:
        """Log a pipeline stage change event."""
        try:
            response = (
                self.client.table("crm_pipeline_events")
                .insert(event_data)
                .execute()
            )
            logger.info("pipeline_event_logged", ghl_contact_id=event_data.get("ghl_contact_id"))
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error("pipeline_event_log_error", error=str(e))
            raise SupabaseClientError(f"Failed to log pipeline event: {e}")

    # ------------------------------------------------------------------
    # AUDIT LOG
    # ------------------------------------------------------------------

    async def write_audit_log(
        self,
        event_type: str,
        source: str,
        status: str,
        ghl_contact_id: Optional[str] = None,
        lead_id: Optional[str] = None,
        payload: Optional[dict] = None,
        error_message: Optional[str] = None,
    ) -> dict[str, Any]:
        """Write an entry to the audit log."""
        try:
            entry: dict[str, Any] = {
                "event_type": event_type,
                "source": source,
                "status": status,
            }
            if ghl_contact_id:
                entry["ghl_contact_id"] = ghl_contact_id
            if lead_id:
                entry["lead_id"] = lead_id
            if payload:
                entry["payload"] = payload
            if error_message:
                entry["error_message"] = error_message

            response = (
                self.client.table("crm_audit_log")
                .insert(entry)
                .execute()
            )
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error("audit_log_error", error=str(e))
            raise SupabaseClientError(f"Failed to write audit log: {e}")