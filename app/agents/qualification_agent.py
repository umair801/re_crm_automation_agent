"""
Lead Qualification Agent using LangGraph + GPT-4o.
Extracts 4-pillar qualification data from conversation transcripts.
Pillars: Motivation, Timeline, Asking Price, Property Condition.
"""

import json
import structlog
from typing import Any, TypedDict
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from app.models.qualification import (
    QualificationResult,
    QualificationPillar,
    PipelineStage,
    QualificationRequest,
)
from app.clients.supabase_client import SupabaseClient
from app.utils.config import settings

logger = structlog.get_logger(__name__)


# ------------------------------------------------------------------
# LANGGRAPH STATE
# ------------------------------------------------------------------

class QualificationState(TypedDict):
    """State object passed between LangGraph nodes."""
    request: QualificationRequest
    raw_gpt_response: dict[str, Any]
    qualification_result: QualificationResult | None
    error: str | None


# ------------------------------------------------------------------
# SYSTEM PROMPT
# ------------------------------------------------------------------

QUALIFICATION_SYSTEM_PROMPT = """
You are an expert real estate wholesaling analyst. Your job is to analyze 
conversation transcripts between a wholesaler and a motivated seller, and 
extract qualification data across 4 pillars.

For each pillar, extract the relevant information and assign a score from 0 to 25.

PILLAR SCORING GUIDE:

1. MOTIVATION (0-25):
   - 25: Extreme urgency, facing foreclosure, divorce, death, job loss, or relocation
   - 20: High motivation, wants to sell quickly, tired landlord, inherited property
   - 15: Moderate motivation, willing to sell but not desperate
   - 10: Low motivation, testing the market, not sure about selling
   - 0: No motivation detected or refuses to share reason

2. TIMELINE (0-25):
   - 25: Needs to close within 2 weeks
   - 20: Wants to close within 30 days
   - 15: Open to closing within 60-90 days
   - 10: No specific timeline, open to offers
   - 0: Timeline is 6+ months away or not discussed

3. ASKING PRICE (0-25):
   - 25: Price is at or below 65% of estimated ARV (After Repair Value)
   - 20: Price is 65-70% of ARV, strong deal potential
   - 15: Price is 70-75% of ARV, possible deal with negotiation
   - 10: Price is 75-80% of ARV, thin margins
   - 0: Price is above 80% ARV, no deal potential or price not discussed

4. PROPERTY CONDITION (0-25):
   - 25: Major repairs needed (foundation, roof, structural), distressed property
   - 20: Significant cosmetic repairs needed, outdated systems
   - 15: Moderate repairs, needs updating
   - 10: Minor repairs only, move-in ready with small fixes
   - 0: Fully renovated, no repairs needed or condition not discussed

TOTAL SCORE INTERPRETATION:
- 75-100: HOT LEAD - Pursue immediately
- 50-74: WARM LEAD - Follow up within 24 hours
- 25-49: COLD LEAD - Add to nurture sequence
- 0-24: DEAD LEAD - Archive

Respond ONLY with a valid JSON object. No markdown, no explanation outside JSON.

JSON FORMAT:
{
  "motivation": {
    "value": "extracted motivation text or null",
    "score": 0,
    "reasoning": "why this score"
  },
  "timeline": {
    "value": "extracted timeline text or null",
    "score": 0,
    "reasoning": "why this score"
  },
  "asking_price": {
    "value": "extracted price text or null",
    "score": 0,
    "reasoning": "why this score"
  },
  "property_condition": {
    "value": "extracted condition text or null",
    "score": 0,
    "reasoning": "why this score"
  },
  "summary": "2-3 sentence summary of this lead"
}
"""


# ------------------------------------------------------------------
# LANGGRAPH NODES
# ------------------------------------------------------------------

async def extract_qualification_node(state: QualificationState) -> QualificationState:
    """Node 1: Send transcript to GPT-4o and extract 4-pillar data."""
    try:
        request = state["request"]
        llm = ChatOpenAI(
            model="gpt-4o",
            api_key=settings.OPENAI_API_KEY,
            temperature=0,
        )

        user_message = f"""
Contact Name: {request.contact_name or 'Unknown'}
Property Address: {request.property_address or 'Not provided'}

CONVERSATION TRANSCRIPT:
{request.transcript}

Extract the 4-pillar qualification data from this transcript.
"""

        messages = [
            SystemMessage(content=QUALIFICATION_SYSTEM_PROMPT),
            HumanMessage(content=user_message),
        ]

        response = await llm.ainvoke(messages)
        raw_text = response.content.strip()

        # Strip markdown code fences if GPT wraps response in them
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]

        parsed = json.loads(raw_text)
        logger.info("gpt4o_extraction_success", contact_id=request.ghl_contact_id)

        return {**state, "raw_gpt_response": parsed, "error": None}

    except json.JSONDecodeError as e:
        logger.error("gpt4o_json_parse_error", error=str(e))
        return {**state, "raw_gpt_response": {}, "error": f"JSON parse error: {e}"}
    except Exception as e:
        logger.error("gpt4o_extraction_error", error=str(e))
        return {**state, "raw_gpt_response": {}, "error": str(e)}


async def score_and_stage_node(state: QualificationState) -> QualificationState:
    """Node 2: Calculate total score and assign recommended pipeline stage."""
    try:
        if state.get("error"):
            return state

        raw = state["raw_gpt_response"]
        request = state["request"]

        motivation = QualificationPillar(**raw.get("motivation", {}))
        timeline = QualificationPillar(**raw.get("timeline", {}))
        asking_price = QualificationPillar(**raw.get("asking_price", {}))
        property_condition = QualificationPillar(**raw.get("property_condition", {}))

        total_score = (
            motivation.score
            + timeline.score
            + asking_price.score
            + property_condition.score
        )

        # Determine pipeline stage from total score
        if total_score >= 75:
            recommended_stage = PipelineStage.HOT_LEAD
            is_qualified = True
        elif total_score >= 50:
            recommended_stage = PipelineStage.WARM_LEAD
            is_qualified = True
        elif total_score >= 25:
            recommended_stage = PipelineStage.COLD_LEAD
            is_qualified = False
        else:
            recommended_stage = PipelineStage.DEAD_LEAD
            is_qualified = False

        result = QualificationResult(
            ghl_contact_id=request.ghl_contact_id,
            motivation=motivation,
            timeline=timeline,
            asking_price=asking_price,
            property_condition=property_condition,
            total_score=total_score,
            recommended_stage=recommended_stage,
            is_qualified=is_qualified,
            summary=raw.get("summary"),
            raw_transcript=request.transcript,
        )

        logger.info(
            "qualification_scored",
            contact_id=request.ghl_contact_id,
            total_score=total_score,
            stage=recommended_stage,
        )

        return {**state, "qualification_result": result, "error": None}

    except Exception as e:
        logger.error("scoring_error", error=str(e))
        return {**state, "qualification_result": None, "error": str(e)}


async def save_to_supabase_node(state: QualificationState) -> QualificationState:
    """Node 3: Persist qualification result and audit log to Supabase."""
    try:
        if state.get("error") or not state.get("qualification_result"):
            return state

        result: QualificationResult = state["qualification_result"]
        db = SupabaseClient()

        # Save qualification result
        await db.save_qualification_result({
            "ghl_contact_id": result.ghl_contact_id,
            "motivation": result.motivation.value,
            "motivation_score": result.motivation.score,
            "timeline": result.timeline.value,
            "timeline_score": result.timeline.score,
            "asking_price": result.asking_price.value,
            "asking_price_score": result.asking_price.score,
            "property_condition": result.property_condition.value,
            "property_condition_score": result.property_condition.score,
            "total_score": result.total_score,
            "recommended_stage": result.recommended_stage.value,
            "raw_transcript": result.raw_transcript,
            "gpt_response": state["raw_gpt_response"],
        })

        # Update lead record
        await db.update_lead(result.ghl_contact_id, {
            "qualification_score": result.total_score,
            "is_qualified": result.is_qualified,
            "current_pipeline_stage": result.recommended_stage.value,
        })

        # Write audit log
        await db.write_audit_log(
            event_type="lead_qualification_completed",
            source="langgraph",
            status="success",
            ghl_contact_id=result.ghl_contact_id,
            payload={"total_score": result.total_score, "stage": result.recommended_stage.value},
        )

        logger.info("qualification_saved_to_supabase", contact_id=result.ghl_contact_id)
        return state

    except Exception as e:
        logger.error("supabase_save_error", error=str(e))
        return {**state, "error": str(e)}


# ------------------------------------------------------------------
# BUILD THE LANGGRAPH GRAPH
# ------------------------------------------------------------------

def build_qualification_graph() -> Any:
    """Compile and return the LangGraph qualification workflow."""
    graph = StateGraph(QualificationState)

    graph.add_node("extract", extract_qualification_node)
    graph.add_node("score_and_stage", score_and_stage_node)
    graph.add_node("save_to_supabase", save_to_supabase_node)

    graph.set_entry_point("extract")
    graph.add_edge("extract", "score_and_stage")
    graph.add_edge("score_and_stage", "save_to_supabase")
    graph.add_edge("save_to_supabase", END)

    return graph.compile()


# ------------------------------------------------------------------
# PUBLIC INTERFACE
# ------------------------------------------------------------------

async def run_qualification_agent(request: QualificationRequest) -> QualificationResult:
    """
    Run the full qualification pipeline for a lead.
    Called by the FastAPI endpoint.
    """
    graph = build_qualification_graph()

    initial_state: QualificationState = {
        "request": request,
        "raw_gpt_response": {},
        "qualification_result": None,
        "error": None,
    }

    final_state = await graph.ainvoke(initial_state)

    if final_state.get("error"):
        raise RuntimeError(f"Qualification agent failed: {final_state['error']}")

    if not final_state.get("qualification_result"):
        raise RuntimeError("Qualification agent returned no result")

    return final_state["qualification_result"]