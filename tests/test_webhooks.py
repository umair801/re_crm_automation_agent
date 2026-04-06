"""
Tests for FastAPI webhook endpoints.
Validates event routing, payload parsing, and response codes.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app.main import app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def contact_created_payload() -> dict:
    return {
        "type": "ContactCreate",
        "locationId": "loc_test_001",
        "contactId": "contact_test_001",
        "contact": {
            "id": "contact_test_001",
            "firstName": "Jane",
            "lastName": "Doe",
            "phone": "+14155559876",
            "email": "jane.doe@example.com",
        },
    }


@pytest.fixture
def conversation_message_payload() -> dict:
    return {
        "type": "ConversationProviderInboundMessage",
        "locationId": "loc_test_001",
        "conversationId": "conv_test_001",
        "contactId": "contact_test_001",
        "message": {
            "id": "msg_001",
            "body": "I want to sell my house fast.",
            "direction": "inbound",
            "messageType": "SMS",
        },
    }


@pytest.fixture
def missed_call_payload() -> dict:
    return {
        "type": "MissedCall",
        "locationId": "loc_test_001",
        "contactId": "contact_test_001",
        "phone": "+14155559876",
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestWebhookEndpoints:

    def test_health_check(self, client: TestClient) -> None:
        """Health check endpoint should return 200 with status healthy."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_check_has_version(self, client: TestClient) -> None:
        """Health check should include version and brand fields."""
        response = client.get("/health")
        data = response.json()
        assert "version" in data
        assert data["brand"] == "Datawebify"

    def test_webhook_contact_created(
        self, client: TestClient, contact_created_payload: dict
    ) -> None:
        """ContactCreate webhook should return 200 with received status."""
        with patch(
            "app.api.webhooks.SupabaseClient.write_audit_log",
            new_callable=AsyncMock,
            return_value=None,
        ):
            response = client.post("/webhooks/ghl", json=contact_created_payload)
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "received"
            assert data["event_type"] == "ContactCreate"

    def test_webhook_conversation_message(
        self, client: TestClient, conversation_message_payload: dict
    ) -> None:
        """ConversationProviderInboundMessage webhook should return 200."""
        with patch(
            "app.api.webhooks.SupabaseClient.write_audit_log",
            new_callable=AsyncMock,
            return_value=None,
        ):
            response = client.post("/webhooks/ghl", json=conversation_message_payload)
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "received"
            assert data["event_type"] == "ConversationProviderInboundMessage"

    def test_webhook_missed_call(
        self, client: TestClient, missed_call_payload: dict
    ) -> None:
        """MissedCall webhook should return 200 with correct event type."""
        with patch(
            "app.api.webhooks.SupabaseClient.write_audit_log",
            new_callable=AsyncMock,
            return_value=None,
        ):
            response = client.post("/webhooks/ghl", json=missed_call_payload)
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "received"
            assert data["event_type"] == "MissedCall"

    def test_webhook_unknown_event_type(self, client: TestClient) -> None:
        """Unknown event type should still return 200 with received status."""
        payload = {
            "type": "UnknownEventXYZ",
            "locationId": "loc_test_001",
        }
        response = client.post("/webhooks/ghl", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "received"
        assert data["event_type"] == "UnknownEventXYZ"

    def test_webhook_returns_event_type(
        self, client: TestClient, contact_created_payload: dict
    ) -> None:
        """Webhook response must echo back the event_type from the payload."""
        with patch(
            "app.api.webhooks.SupabaseClient.write_audit_log",
            new_callable=AsyncMock,
            return_value=None,
        ):
            response = client.post("/webhooks/ghl", json=contact_created_payload)
            data = response.json()
            assert data["event_type"] == contact_created_payload["type"]

    def test_webhook_missing_type_defaults_to_unknown(
        self, client: TestClient
    ) -> None:
        """Payload without type field should still return 200, event_type = unknown."""
        response = client.post("/webhooks/ghl", json={"locationId": "loc_test_001"})
        assert response.status_code == 200
        data = response.json()
        assert data["event_type"] == "unknown"

    def test_qualification_endpoint_reachable(self, client: TestClient) -> None:
        """Qualification endpoint should be reachable and return non-404."""
        with patch(
            "app.api.qualification.run_qualification_agent",
            new_callable=AsyncMock,
            return_value=None,
        ):
            payload = {
                "ghl_contact_id": "contact_test_001",
                "transcript": "I need to sell fast.",
                "contact_name": "John Smith",
                "property_address": "123 Main St",
            }
            response = client.post("/qualify/lead", json=payload)
            assert response.status_code != 404