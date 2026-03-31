from pydantic import BaseModel
from typing import Dict, List, Any, Optional

class AIRequest(BaseModel):
    game_state: Dict[str, Any]
    personality: str
    difficulty: str
    available_actions: Dict[str, Any]
