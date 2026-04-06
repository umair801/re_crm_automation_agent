"""
GoHighLevel CRM API Client
Handles all GHL API v2 communication for the Real Estate CRM Automation Agent.
"""

import httpx
import structlog
from typing import Any, Optional
from app.utils.config import settings

logger = structlog.get_logger(__name__)


class GHLAPIError(Exception):
    """Raised when GHL API returns an error response."""
    def __init__(self, status_code: int, message: str, endpoint: str):
        self.status_code = status_code
        self.message = message
        self.endpoint = endpoint
        super().__init__(f"GHL API Error {status_code} on {endpoint}: {message}")


class GHLClient:
    """
    GoHighLevel API v2 client.
    Handles contacts, opportunities, pipeline stages, and custom fields.
    """

    BASE_URL = "https://services.leadconnectorhq.com"

    def __init__(self) -> None:
        self.api_key: str = settings.GHL_API_KEY
        self.location_id: str = settings.GHL_LOCATION_ID
        self.pipeline_id: str = settings.GHL_PIPELINE_ID
        self.headers: dict[str, str] = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Version": "2021-07-28",
        }

    # ------------------------------------------------------------------
    # INTERNAL HELPERS
    # ------------------------------------------------------------------

    async def _get(self, endpoint: str, params: Optional[dict] = None) -> dict[str, Any]:
        """Execute a GET request against the GHL API."""
        url = f"{self.BASE_URL}{endpoint}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                logger.info("ghl_get_success", endpoint=endpoint, status=response.status_code)
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error("ghl_get_error", endpoint=endpoint, status=e.response.status_code, error=str(e))
                raise GHLAPIError(e.response.status_code, e.response.text, endpoint)
            except httpx.RequestError as e:
                logger.error("ghl_request_error", endpoint=endpoint, error=str(e))
                raise GHLAPIError(0, str(e), endpoint)

    async def _post(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Execute a POST request against the GHL API."""
        url = f"{self.BASE_URL}{endpoint}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                logger.info("ghl_post_success", endpoint=endpoint, status=response.status_code)
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error("ghl_post_error", endpoint=endpoint, status=e.response.status_code, error=str(e))
                raise GHLAPIError(e.response.status_code, e.response.text, endpoint)
            except httpx.RequestError as e:
                logger.error("ghl_request_error", endpoint=endpoint, error=str(e))
                raise GHLAPIError(0, str(e), endpoint)

    async def _put(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Execute a PUT request against the GHL API."""
        url = f"{self.BASE_URL}{endpoint}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.put(url, headers=self.headers, json=payload)
                response.raise_for_status()
                logger.info("ghl_put_success", endpoint=endpoint, status=response.status_code)
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error("ghl_put_error", endpoint=endpoint, status=e.response.status_code, error=str(e))
                raise GHLAPIError(e.response.status_code, e.response.text, endpoint)
            except httpx.RequestError as e:
                logger.error("ghl_request_error", endpoint=endpoint, error=str(e))
                raise GHLAPIError(0, str(e), endpoint)

    # ------------------------------------------------------------------
    # CONTACTS
    # ------------------------------------------------------------------

    async def get_contact(self, contact_id: str) -> dict[str, Any]:
        """Retrieve a single contact by ID."""
        return await self._get(f"/contacts/{contact_id}")

    async def search_contacts(self, phone: Optional[str] = None, email: Optional[str] = None) -> dict[str, Any]:
        """Search contacts by phone or email."""
        params: dict[str, Any] = {"locationId": self.location_id}
        if phone:
            params["phone"] = phone
        if email:
            params["email"] = email
        return await self._get("/contacts/search", params=params)

    async def create_contact(
        self,
        first_name: str,
        last_name: str,
        phone: str,
        email: Optional[str] = None,
        custom_fields: Optional[list[dict]] = None,
        tags: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Create a new contact in GHL."""
        payload: dict[str, Any] = {
            "firstName": first_name,
            "lastName": last_name,
            "phone": phone,
            "locationId": self.location_id,
        }
        if email:
            payload["email"] = email
        if custom_fields:
            payload["customFields"] = custom_fields
        if tags:
            payload["tags"] = tags

        return await self._post("/contacts/", payload)

    async def update_contact(
        self,
        contact_id: str,
        custom_fields: Optional[list[dict]] = None,
        tags: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Update an existing contact's fields and tags."""
        payload: dict[str, Any] = {}
        if custom_fields:
            payload["customFields"] = custom_fields
        if tags:
            payload["tags"] = tags
        payload.update(kwargs)
        return await self._put(f"/contacts/{contact_id}", payload)

    # ------------------------------------------------------------------
    # OPPORTUNITIES (PIPELINE DEALS)
    # ------------------------------------------------------------------

    async def get_opportunity(self, opportunity_id: str) -> dict[str, Any]:
        """Retrieve a single opportunity by ID."""
        return await self._get(f"/opportunities/{opportunity_id}")

    async def create_opportunity(
        self,
        contact_id: str,
        name: str,
        stage_id: str,
        monetary_value: Optional[float] = None,
        status: str = "open",
    ) -> dict[str, Any]:
        """Create a new opportunity (deal) linked to a contact."""
        payload: dict[str, Any] = {
            "pipelineId": self.pipeline_id,
            "locationId": self.location_id,
            "name": name,
            "pipelineStageId": stage_id,
            "status": status,
            "contactId": contact_id,
        }
        if monetary_value is not None:
            payload["monetaryValue"] = monetary_value

        return await self._post("/opportunities/", payload)

    async def update_opportunity_stage(
        self,
        opportunity_id: str,
        stage_id: str,
        status: Optional[str] = None,
    ) -> dict[str, Any]:
        """Move an opportunity to a different pipeline stage."""
        payload: dict[str, Any] = {"pipelineStageId": stage_id}
        if status:
            payload["status"] = status
        return await self._put(f"/opportunities/{opportunity_id}", payload)

    async def update_opportunity(
        self,
        opportunity_id: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Update any fields on an existing opportunity."""
        return await self._put(f"/opportunities/{opportunity_id}", kwargs)

    # ------------------------------------------------------------------
    # PIPELINE STAGES
    # ------------------------------------------------------------------

    async def get_pipeline_stages(self) -> dict[str, Any]:
        """Retrieve all stages in the configured pipeline."""
        return await self._get(f"/opportunities/pipelines/{self.pipeline_id}")

    # ------------------------------------------------------------------
    # CONVERSATIONS
    # ------------------------------------------------------------------

    async def send_sms(self, contact_id: str, message: str) -> dict[str, Any]:
        """Send an SMS message to a contact via GHL."""
        payload: dict[str, Any] = {
            "type": "SMS",
            "contactId": contact_id,
            "message": message,
        }
        return await self._post("/conversations/messages", payload)

    async def get_conversation(self, conversation_id: str) -> dict[str, Any]:
        """Retrieve a conversation by ID."""
        return await self._get(f"/conversations/{conversation_id}")

    async def get_contact_conversations(self, contact_id: str) -> dict[str, Any]:
        """Retrieve all conversations for a contact."""
        params = {"contactId": contact_id, "locationId": self.location_id}
        return await self._get("/conversations/search", params=params)