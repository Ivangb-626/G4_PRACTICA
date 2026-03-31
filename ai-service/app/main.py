from fastapi import FastAPI
from app.services.ai_service import AIService
from app.models.ai_request import AIRequest
from app.models.ai_response import AIResponse

app = FastAPI(title="MasterDeHostias AI Service")
ai_service = AIService()

@app.get("/health")
def health_check():
    return {"status": "ok", "providers_loaded": len(ai_service.providers)}

@app.post("/api/ai/turn", response_model=AIResponse)
async def ai_turn(request: AIRequest):
    return await ai_service.get_ai_turn(request)

