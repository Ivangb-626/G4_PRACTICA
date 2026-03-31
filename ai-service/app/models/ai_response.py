from pydantic import BaseModel
from typing import Dict, List, Any, Optional

class AIAction(BaseModel):
    type: str
    details: Optional[Dict[str, Any]] = None

class AIResponse(BaseModel):
    actions: List[AIAction]
    reasoning: str
    analysis: str
