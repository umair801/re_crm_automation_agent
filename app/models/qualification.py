"""
Pydantic models for lead qualification data structures.
"""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class PipelineStage(str, Enum):
    """GHL pipeline stages mapped to qualification outcomes."""
    NEW_LEAD = "New Lead"
    HOT_LEAD = "Hot Lead"
    WARM_LEAD = "Warm Lead"
    COLD_LEAD = "Cold Lead"
    DEAD_LEAD = "Dead Lead"
    OFFER_SENT = "Offer Sent"
    UNDER_CONTRACT = "Under Contract"


class QualificationPillar(BaseModel):
    """A single qualification pillar with extracted value and score."""
    value: Optional[str] = Field(None, description="Extracted value from transcript")
    score: int = Field(0, ge=0, le=25, description="Score from 0 to 25")
    reasoning: Optional[str] = Field(None, description="Why this score was assigned")


class QualificationResult(BaseModel):
    """Full 4-pillar qualification result returned by the AI agent."""
    ghl_contact_id: str
    motivation: QualificationPillar
    timeline: QualificationPillar
    asking_price: QualificationPillar
    property_condition: QualificationPillar
    total_score: int = Field(0, ge=0, le=100)
    recommended_stage: PipelineStage
    is_qualified: bool
    summary: Optional[str] = None
    raw_transcript: Optional[str] = None


class QualificationRequest(BaseModel):
    """Input payload sent to the qualification agent endpoint."""
    ghl_contact_id: str
    transcript: str
    contact_name: Optional[str] = None
    property_address: Optional[str] = None