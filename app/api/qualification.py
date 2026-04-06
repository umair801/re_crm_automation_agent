"""
FastAPI router for lead qualification endpoints.
"""

import structlog
from fastapi import APIRouter, HTTPException
from app.models.qualification import QualificationRequest, QualificationResult
from app.agents.qualification_agent import run_qualification_agent

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/qualify", tags=["Qualification"])


@router.post("/lead", response_model=QualificationResult)
async def qualify_lead(request: QualificationRequest) -> QualificationResult:
    """
    Receive a conversation transcript from n8n and run the
    GPT-4o 4-pillar qualification agent.
    Returns qualification score and recommended pipeline stage.
    """
    logger.info("qualification_request_received", contact_id=request.ghl_contact_id)

    try:
        result = await run_qualification_agent(request)
        logger.info(
            "qualification_completed",
            contact_id=request.ghl_contact_id,
            score=result.total_score,
            stage=result.recommended_stage,
        )
        return result

    except RuntimeError as e:
        logger.error("qualification_failed", contact_id=request.ghl_contact_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        logger.error("qualification_unexpected_error", error=str(e))
        raise HTTPException(status_code=500, detail="Unexpected error during qualification")