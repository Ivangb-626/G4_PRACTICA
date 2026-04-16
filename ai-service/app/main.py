from typing import Any, Dict, List

from fastapi import FastAPI
from pydantic import BaseModel
from app.services.ai_service import AIService
from app.models.ai_request import AIRequest
from app.models.ai_response import AIResponse

app = FastAPI(title="MasterDeHostias AI Service")
ai_service = AIService()


class AIDiplomacyRequest(BaseModel):
    game_id: str
    ai_player_id: str
    proposal: Dict[str, Any]
    relations: List[Dict[str, Any]] = []
    personality: str = "balanced"


class AIDiplomacyResponse(BaseModel):
    accept: bool
    reason: str


class AITacticalRequest(BaseModel):
    game_id: str
    session_id: str
    ai_player_id: str
    state: Dict[str, Any]


class AITacticalResponse(BaseModel):
    action: Dict[str, Any]

@app.get("/health")
def health_check():
    return {"status": "ok", "providers_loaded": len(ai_service.providers)}

@app.post("/api/ai/turn", response_model=AIResponse)
async def ai_turn(request: AIRequest):
    try:
        return await ai_service.get_ai_turn(request)
    except Exception:
        return AIResponse(
            actions=[{"type": "endTurn", "details": None}],
            reasoning="AI service error - defaulting to safe action",
            analysis="Model unavailable",
        )


@app.post("/ai/turn", response_model=AIResponse)
async def ai_turn_public(request: AIRequest):
    return await ai_turn(request)


@app.post("/ai/diplomacy", response_model=AIDiplomacyResponse)
async def ai_diplomacy(request: AIDiplomacyRequest):
    try:
        prompt = (
            "You are an AI diplomacy assistant in a 4X strategy game. "
            "Return JSON object with keys: accept (boolean), reason (string). "
            f"Personality: {request.personality}. "
            f"Proposal: {request.proposal}. Relations: {request.relations}"
        )
        raw = await ai_service.call_with_fallback("Return strict JSON only.", prompt)
        parsed = ai_service.parse_response(raw) or {}
        return AIDiplomacyResponse(
            accept=bool(parsed.get("accept", False)),
            reason=str(parsed.get("reason", "Error processing proposal")),
        )
    except Exception:
        return AIDiplomacyResponse(
            accept=False,
            reason="Error processing proposal",
        )


@app.post("/ai/tactical", response_model=AITacticalResponse)
async def ai_tactical(request: AITacticalRequest):
    try:
        prompt = (
            "You are an AI tactical combat assistant in a 4X strategy game. "
            "Return JSON object with key action. "
            "action must be an object with at least {type: string}. "
            f"State: {request.state}"
        )
        raw = await ai_service.call_with_fallback("Return strict JSON only.", prompt)
        parsed = ai_service.parse_response(raw) or {}
        action = parsed.get("action")
        if not isinstance(action, dict) or not action.get("type"):
            action = {"type": "wait"}
        return AITacticalResponse(action=action)
    except Exception:
        return AITacticalResponse(action={"type": "wait"})

