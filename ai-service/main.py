from fastapi import FastAPI, Request, HTTPException
from ai.strategic import decide_turn
from ai.diplomacy_ai import decide_diplomacy
from ai.tactical import decide_tactical
import logging

app = FastAPI(title="MMOH AI Service")

@app.post("/ai/turn")
async def ai_turn(request: Request):
    try:
        data = await request.json()
        actions = decide_turn(
            data.get("state"),
            data.get("personality"),
            data.get("difficulty")
        )
        return {"actions": actions}
    except Exception as e:
        logging.error(f"Error in /ai/turn: {e}")
        return {"actions": []}

@app.post("/ai/diplomacy")
async def ai_diplomacy(request: Request):
    try:
        data = await request.json()
        # Fallback implemented inside decide_diplomacy
        result = decide_diplomacy(data)
        return result
    except Exception as e:
        logging.error(f"Error in /ai/diplomacy: {e}")
        return {"accept": False, "reason": "Error processing proposal"}

@app.post("/ai/tactical")
async def ai_tactical(request: Request):
    try:
        data = await request.json()
        # Fallback implemented inside decide_tactical
        action = decide_tactical(data)
        return {"action": action}
    except Exception as e:
        logging.error(f"Error in /ai/tactical: {e}")
        return {"action": {"type": "wait"}}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
