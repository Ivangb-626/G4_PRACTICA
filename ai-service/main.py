from fastapi import FastAPI, Request
from ai.strategic import decide_turn
from ai.diplomacy_ai import decide_diplomacy
from ai.tactical import decide_tactical
import logging

app = FastAPI(title="MOO2 AI Service")


@app.get("/")
async def root():
    return {"status": "ok", "service": "moo2-ai-service"}


@app.post("/ai/turn")
async def ai_turn(request: Request):
    try:
        data = await request.json()
        actions = decide_turn(
            data.get("state"),
            data.get("personality"),
            data.get("difficulty"),
        )
        return {"actions": actions}
    except Exception as e:
        logging.exception("ai_turn error")
        return {"actions": [], "error": str(e)}


@app.post("/ai/diplomacy")
async def ai_diplomacy(request: Request):
    try:
        data = await request.json()
        result = decide_diplomacy(data)
        return result
    except Exception as e:
        logging.exception("ai_diplomacy error")
        return {"accept": False, "reason": f"Error: {e}"}


@app.post("/ai/tactical")
async def ai_tactical(request: Request):
    try:
        data = await request.json()
        action = decide_tactical(data)
        return {"action": action}
    except Exception as e:
        logging.exception("ai_tactical error")
        return {"action": {"type": "wait"}, "error": str(e)}


@app.post("/ai/council_vote")
async def ai_council_vote(request: Request):
    """Decide el voto del SENADO para una raza IA, dado dos candidatos."""
    try:
        data = await request.json()
        candidates = data.get("candidates", [])
        relations = data.get("relations", {})  # {candidate_id: relation_value}
        personality = (data.get("personality") or "balanced").lower()
        if not candidates or len(candidates) < 2:
            return {"choice": None, "reason": "Not enough candidates"}
        a, b = candidates[0], candidates[1]
        ra = relations.get(a, 30)
        rb = relations.get(b, 30)
        if abs(ra - rb) < 8 or max(ra, rb) < 20:
            return {"choice": None, "reason": "Abstain (insufficient distinction)"}
        choice = a if ra > rb else b
        return {"choice": choice, "reason": f"Best relation ({choice}) for {personality}"}
    except Exception as e:
        logging.exception("ai_council_vote error")
        return {"choice": None, "reason": f"Error: {e}"}


@app.post("/ai/espionage")
async def ai_espionage(request: Request):
    """Sugerencia de mision para un espia (AI propio o evaluacion para AI rival)."""
    try:
        data = await request.json()
        targets = data.get("possible_targets", [])
        if not targets:
            return {"mission": None, "target": None}
        # Personality drives mission preference
        personality = (data.get("personality") or "balanced").lower()
        mission = "steal_tech"
        if personality in ("alkari",):
            mission = "sabotage"
        if personality in ("meklar",):
            mission = "steal_tech"
        if personality in ("trilarian",):
            mission = "frame"
        return {"mission": mission, "target": targets[0]}
    except Exception as e:
        logging.exception("ai_espionage error")
        return {"mission": None, "target": None, "error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
