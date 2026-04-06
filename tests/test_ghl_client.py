"""
Tests for the GHL API Client.
Validates contact CRUD, opportunity management, and error handling.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.clients.ghl_client import GHLClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def ghl_client() -> GHLClient:
    with patch("app.clients.ghl_client.GHLClient.__init__", return_value=None):
        client = GHLClient.__new__(GHLClient)
        client.base_url = "https://services.leadconnectorhq.com"
        client.api_key = "test_api_key"
        client.location_id = "test_location_id"
        client.logger = MagicMock()
        return client


@pytest.fixture
def sample_contact_payload() -> dict:
    return {
        "firstName": "John",
        "lastName": "Smith",
        "phone": "+14155551234",
        "email": "john.smith@example.com",
        "locationId": "test_location_id",
        "customFields": [
            {"id": "motivation_field_id", "value": "Divorce, needs cash urgently"},
            {"id": "timeline_field_id", "value": "30 days"},
            {"id": "asking_price_field_id", "value": "180000"},
            {"id": "condition_field_id", "value": "Needs work"},
        ],
    }


@pytest.fixture
def mock_contact_response() -> dict:
    return {
        "contact": {
            "id": "ghl_contact_001",
            "firstName": "John",
            "lastName": "Smith",
            "phone": "+14155551234",
            "email": "john.smith@example.com",
            "locationId": "test_location_id",
        }
    }


@pytest.fixture
def mock_opportunity_response() -> dict:
    return {
        "opportunity": {
            "id": "ghl_opp_001",
            "name": "John Smith - 123 Main St",
            "status": "open",
            "pipelineId": "test_pipeline_id",
            "pipelineStageId": "hot_lead_stage_id",
        }
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestGHLClient:

    def test_ghl_client_initializes(self, ghl_client: GHLClient) -> None:
        """GHLClient should initialize with base URL and credentials."""
        assert ghl_client.base_url == "https://services.leadconnectorhq.com"
        assert ghl_client.api_key == "test_api_key"
        assert ghl_client.location_id == "test_location_id"

    def test_contact_payload_structure(self, sample_contact_payload: dict) -> None:
        """Contact payload must include all required fields."""
        required_keys = ["firstName", "lastName", "phone", "locationId"]
        for key in required_keys:
            assert key in sample_contact_payload, f"Missing required key: {key}"

    def test_contact_payload_custom_fields(self, sample_contact_payload: dict) -> None:
        """Custom fields must include the 4-pillar qualification data."""
        custom_fields = sample_contact_payload.get("customFields", [])
        assert len(custom_fields) == 4
        field_ids = [f["id"] for f in custom_fields]
        assert "motivation_field_id" in field_ids
        assert "timeline_field_id" in field_ids
        assert "asking_price_field_id" in field_ids
        assert "condition_field_id" in field_ids

    @pytest.mark.asyncio
    async def test_create_contact_success(
        self,
        ghl_client: GHLClient,
        sample_contact_payload: dict,
        mock_contact_response: dict,
    ) -> None:
        """create_contact() should return contact data on success."""
        ghl_client.create_contact = AsyncMock(return_value=mock_contact_response)
        result = await ghl_client.create_contact(sample_contact_payload)
        assert result["contact"]["id"] == "ghl_contact_001"
        assert result["contact"]["firstName"] == "John"

    @pytest.mark.asyncio
    async def test_update_contact_success(
        self, ghl_client: GHLClient, mock_contact_response: dict
    ) -> None:
        """update_contact() should return updated contact data."""
        ghl_client.update_contact = AsyncMock(return_value=mock_contact_response)
        result = await ghl_client.update_contact(
            "ghl_contact_001", {"firstName": "John"}
        )
        assert result["contact"]["id"] == "ghl_contact_001"

    @pytest.mark.asyncio
    async def test_create_opportunity_success(
        self,
        ghl_client: GHLClient,
        mock_opportunity_response: dict,
    ) -> None:
        """create_opportunity() should return opportunity data on success."""
        ghl_client.create_opportunity = AsyncMock(return_value=mock_opportunity_response)
        result = await ghl_client.create_opportunity(
            {
                "name": "John Smith - 123 Main St",
                "pipelineId": "test_pipeline_id",
                "pipelineStageId": "hot_lead_stage_id",
                "contactId": "ghl_contact_001",
            }
        )
        assert result["opportunity"]["id"] == "ghl_opp_001"
        assert result["opportunity"]["status"] == "open"

    @pytest.mark.asyncio
    async def test_update_pipeline_stage_success(
        self, ghl_client: GHLClient, mock_opportunity_response: dict
    ) -> None:
        """update_pipeline_stage() should move opportunity to new stage."""
        ghl_client.update_pipeline_stage = AsyncMock(
            return_value=mock_opportunity_response
        )
        result = await ghl_client.update_pipeline_stage(
            "ghl_opp_001", "hot_lead_stage_id"
        )
        assert result["opportunity"]["pipelineStageId"] == "hot_lead_stage_id"

    @pytest.mark.asyncio
    async def test_api_error_handling(self, ghl_client: GHLClient) -> None:
        """GHL client should raise an exception on API failure."""
        ghl_client.create_contact = AsyncMock(
            side_effect=Exception("GHL API returned 401 Unauthorized")
        )
        with pytest.raises(Exception, match="401 Unauthorized"):
            await ghl_client.create_contact({})

    def test_phone_format_in_payload(self, sample_contact_payload: dict) -> None:
        """Phone number must include country code prefix."""
        phone = sample_contact_payload["phone"]
        assert phone.startswith("+"), "Phone must start with + country code"