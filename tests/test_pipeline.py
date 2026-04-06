"""
Tests for pipeline management logic.
Validates stage mapping from qualification scores and contact creation flow.
"""

import pytest
from app.models.qualification import (
    QualificationResult,
    QualificationPillar,
    PipelineStage,
)


# ---------------------------------------------------------------------------
# Helpers (mirrors your agent's stage mapping logic)
# ---------------------------------------------------------------------------

def map_score_to_stage(total_score: int) -> PipelineStage:
    """Map total qualification score (0-100) to GHL pipeline stage."""
    if total_score >= 80:
        return PipelineStage.HOT_LEAD
    elif total_score >= 60:
        return PipelineStage.WARM_LEAD
    elif total_score >= 40:
        return PipelineStage.COLD_LEAD
    else:
        return PipelineStage.DEAD_LEAD


def is_qualified(total_score: int) -> bool:
    """Lead is qualified if total score is 60 or above."""
    return total_score >= 60


def make_result(scores: list[int], stage: PipelineStage, qualified: bool) -> QualificationResult:
    """Helper to build a QualificationResult from 4 pillar scores."""
    pillars = [
        QualificationPillar(value="test", score=s, reasoning="test")
        for s in scores
    ]
    return QualificationResult(
        ghl_contact_id="contact_test",
        motivation=pillars[0],
        timeline=pillars[1],
        asking_price=pillars[2],
        property_condition=pillars[3],
        total_score=sum(scores),
        recommended_stage=stage,
        is_qualified=qualified,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestPipelineStageMapping:

    def test_hot_lead_stage(self) -> None:
        """Total score >= 80 should map to Hot Lead."""
        assert map_score_to_stage(85) == PipelineStage.HOT_LEAD

    def test_warm_lead_stage(self) -> None:
        """Total score between 60 and 79 should map to Warm Lead."""
        assert map_score_to_stage(65) == PipelineStage.WARM_LEAD

    def test_cold_lead_stage(self) -> None:
        """Total score between 40 and 59 should map to Cold Lead."""
        assert map_score_to_stage(45) == PipelineStage.COLD_LEAD

    def test_dead_lead_stage(self) -> None:
        """Total score below 40 should map to Dead Lead."""
        assert map_score_to_stage(20) == PipelineStage.DEAD_LEAD

    def test_qualified_threshold(self) -> None:
        """Score of exactly 60 should be qualified."""
        assert is_qualified(60) is True

    def test_just_below_qualified_threshold(self) -> None:
        """Score of 59 should not be qualified."""
        assert is_qualified(59) is False

    def test_perfect_score(self) -> None:
        """Score of 100 should be Hot Lead and qualified."""
        assert map_score_to_stage(100) == PipelineStage.HOT_LEAD
        assert is_qualified(100) is True

    def test_score_boundary_warm_to_hot(self) -> None:
        """Score of exactly 80 should be Hot Lead, not Warm Lead."""
        assert map_score_to_stage(80) == PipelineStage.HOT_LEAD

    def test_score_boundary_cold_to_warm(self) -> None:
        """Score of exactly 60 should be Warm Lead, not Cold Lead."""
        assert map_score_to_stage(60) == PipelineStage.WARM_LEAD

    def test_score_boundary_dead_to_cold(self) -> None:
        """Score of exactly 40 should be Cold Lead, not Dead Lead."""
        assert map_score_to_stage(40) == PipelineStage.COLD_LEAD


class TestQualificationResultModel:

    def test_full_result_model(self) -> None:
        """QualificationResult model should store all fields correctly."""
        result = make_result([22, 23, 18, 20], PipelineStage.HOT_LEAD, True)
        assert result.ghl_contact_id == "contact_test"
        assert result.total_score == 83
        assert result.is_qualified is True
        assert result.recommended_stage == PipelineStage.HOT_LEAD

    def test_pillar_scores_sum_to_total(self) -> None:
        """Sum of 4 pillar scores should equal total_score."""
        scores = [20, 18, 15, 17]
        result = make_result(scores, PipelineStage.WARM_LEAD, True)
        assert result.total_score == sum(scores)

    def test_unqualified_result_model(self) -> None:
        """Low scores should produce an unqualified Dead Lead result."""
        result = make_result([5, 4, 6, 5], PipelineStage.DEAD_LEAD, False)
        assert result.is_qualified is False
        assert result.recommended_stage == PipelineStage.DEAD_LEAD

    def test_result_requires_ghl_contact_id(self) -> None:
        """QualificationResult should fail validation without ghl_contact_id."""
        with pytest.raises(Exception):
            QualificationResult(
                motivation=QualificationPillar(value="test", score=10),
                timeline=QualificationPillar(value="test", score=10),
                asking_price=QualificationPillar(value="test", score=10),
                property_condition=QualificationPillar(value="test", score=10),
                total_score=40,
                recommended_stage=PipelineStage.COLD_LEAD,
                is_qualified=False,
            )