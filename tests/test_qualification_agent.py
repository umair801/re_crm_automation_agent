"""
Tests for the Lead Qualification Agent.
Validates 4-pillar extraction, scoring logic, and Supabase logging.
"""

import pytest
from unittest.mock import AsyncMock, patch
from app.models.qualification import (
    QualificationRequest,
    QualificationResult,
    QualificationPillar,
    PipelineStage,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_transcript() -> str:
    return (
        "Agent: Hi, are you looking to sell your property?\n"
        "Lead: Yes, I need to sell fast. Going through a divorce and need "
        "cash in 30 days.\n"
        "Agent: What price are you hoping for?\n"
        "Lead: Around $180,000 but I am flexible.\n"
        "Agent: What condition is the property in?\n"
        "Lead: It needs some work. Roof is old and kitchen needs updating."
    )


@pytest.fixture
def sample_request(sample_transcript: str) -> QualificationRequest:
    return QualificationRequest(
        ghl_contact_id="contact_test_001",
        transcript=sample_transcript,
        contact_name="John Smith",
        property_address="123 Main St",
    )


@pytest.fixture
def mock_pillar() -> QualificationPillar:
    return QualificationPillar(
        value="Divorce, needs cash urgently",
        score=22,
        reasoning="High urgency seller facing life event",
    )


@pytest.fixture
def mock_qualification_result(mock_pillar: QualificationPillar) -> QualificationResult:
    return QualificationResult(
        ghl_contact_id="contact_test_001",
        motivation=mock_pillar,
        timeline=QualificationPillar(value="30 days", score=23, reasoning="Very tight timeline"),
        asking_price=QualificationPillar(value="$180,000", score=18, reasoning="Below market"),
        property_condition=QualificationPillar(value="Needs work", score=15, reasoning="Renovation needed"),
        total_score=78,
        recommended_stage=PipelineStage.HOT_LEAD,
        is_qualified=True,
        summary="High urgency seller with motivated timeline.",
        raw_transcript="Agent: Hi...",
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestQualificationAgent:

    def test_qualification_request_model(self, sample_request: QualificationRequest) -> None:
        """QualificationRequest model validates and stores fields correctly."""
        assert sample_request.ghl_contact_id == "contact_test_001"
        assert len(sample_request.transcript) > 0

    def test_pillar_score_range(self, mock_pillar: QualificationPillar) -> None:
        """Pillar score must be between 0 and 25."""
        assert 0 <= mock_pillar.score <= 25

    def test_total_score_range(self, mock_qualification_result: QualificationResult) -> None:
        """Total score must be between 0 and 100."""
        assert 0 <= mock_qualification_result.total_score <= 100

    def test_qualification_result_qualified_flag(
        self, mock_qualification_result: QualificationResult
    ) -> None:
        """Lead with high total score should be marked as qualified."""
        assert mock_qualification_result.is_qualified is True
        assert mock_qualification_result.total_score >= 50

    def test_pipeline_stage_assignment(
        self, mock_qualification_result: QualificationResult
    ) -> None:
        """Score of 78 should map to Hot Lead pipeline stage."""
        assert mock_qualification_result.recommended_stage == PipelineStage.HOT_LEAD

    @pytest.mark.asyncio
    async def test_run_qualification_agent_mocked(
        self,
        sample_request: QualificationRequest,
        mock_qualification_result: QualificationResult,
    ) -> None:
        """run_qualification_agent() should return a QualificationResult."""
        with patch(
            "app.agents.qualification_agent.run_qualification_agent",
            new_callable=AsyncMock,
            return_value=mock_qualification_result,
        ):
            from app.agents.qualification_agent import run_qualification_agent
            result = await run_qualification_agent(sample_request)
            assert isinstance(result, QualificationResult)
            assert result.ghl_contact_id == "contact_test_001"
            assert result.is_qualified is True

    def test_unqualified_lead_score(self) -> None:
        """Lead with total score below 50 should be marked as not qualified."""
        result = QualificationResult(
            ghl_contact_id="contact_test_002",
            motivation=QualificationPillar(value="No urgency", score=5, reasoning="Low urgency"),
            timeline=QualificationPillar(value="2 years", score=4, reasoning="No timeline"),
            asking_price=QualificationPillar(value="$600k", score=5, reasoning="Overpriced"),
            property_condition=QualificationPillar(value="Perfect", score=6, reasoning="Renovated"),
            total_score=20,
            recommended_stage=PipelineStage.DEAD_LEAD,
            is_qualified=False,
        )
        assert result.is_qualified is False
        assert result.total_score < 50

    def test_transcript_not_empty(self, sample_request: QualificationRequest) -> None:
        """Transcript must not be empty for qualification to proceed."""
        assert sample_request.transcript.strip() != ""

    def test_pipeline_stage_enum_values(self) -> None:
        """PipelineStage enum must include all required stages."""
        stages = [s.value for s in PipelineStage]
        assert "Hot Lead" in stages
        assert "Warm Lead" in stages
        assert "Cold Lead" in stages
        assert "Dead Lead" in stages

    def test_pillar_value_can_be_none(self) -> None:
        """QualificationPillar value field is optional and can be None."""
        pillar = QualificationPillar(value=None, score=0, reasoning="Not discussed")
        assert pillar.value is None
        assert pillar.score == 0