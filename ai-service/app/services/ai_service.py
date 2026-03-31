import os
import json
import asyncio
import httpx

from app.providers.groq_provider import GroQProvider
from app.providers.github_provider import GitHubModelsProvider
from app.services.prompt_builder import build_system_prompt, build_user_prompt
from app.services.state_filter import filter_state_for_ai
from app.services.action_validator import validate_actions
from app.models.ai_request import AIRequest
from app.models.ai_response import AIResponse, AIAction

class AIService:
    def __init__(self):
        self.providers = []

        groq_key = os.getenv("GROQ_API_KEY")
        groq_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        if groq_key:
            self.providers.append(GroQProvider(groq_key, groq_model))

        gh_token = os.getenv("GITHUB_MODELS_TOKEN")
        gh_model = os.getenv("GITHUB_MODELS_MODEL", "gpt-4o")
        if gh_token:
            self.providers.append(GitHubModelsProvider(gh_token, gh_model))
            
    async def get_ai_turn(self, request: AIRequest, ai_player_id: str = "ai_0") -> AIResponse:
        visible_state = filter_state_for_ai(request.game_state, ai_player_id)
        
        system_prompt = build_system_prompt(request.personality, request.difficulty)
        user_prompt = build_user_prompt(visible_state, request.available_actions)
        
        raw_response = await self.call_with_fallback(system_prompt, user_prompt)
        parsed = self.parse_response(raw_response)
        
        if not parsed:
            actions = self.heuristic_actions(request)
            return AIResponse(
                actions=[AIAction(**a) for a in actions],
                reasoning="AI service error / LLM fail - defaulting to heuristic actions",
                analysis="Service unavailable"
            )
            
        raw_actions = parsed.get("actions", [])
        validated = validate_actions(raw_actions, request.game_state, ai_player_id)
        
        return AIResponse(
            actions=[AIAction(**a) for a in validated],
            reasoning=parsed.get("reasoning", ""),
            analysis=parsed.get("analysis", "")
        )

    async def call_with_fallback(self, system_prompt: str, user_prompt: str) -> str:
        for provider in self.providers:
            try:
                result = await provider.generate(system_prompt, user_prompt)
                return result
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    continue
                elif e.response.status_code >= 500:
                    try:
                        return await provider.generate(system_prompt, user_prompt)
                    except:
                        continue
            except Exception:
                continue
                
        return '{"actions": [{"type": "endTurn"}], "reasoning": "All AI models unavailable", "analysis": "N/A"}'

    def parse_response(self, raw: str):
        if not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            start = raw.find("{")
            end = raw.rfind("}")
            if start != -1 and end != -1 and start < end:
                try:
                    return json.loads(raw[start:end+1])
                except json.JSONDecodeError:
                    pass
        return None

    def heuristic_actions(self, request: AIRequest):
        available = request.available_actions
        actions = []
        if available.get("can_research"):
            tech = available["can_research"][0]
            actions.append({"type": "selectResearch", "details": {"techId": tech, "field": "physics", "level": 1}})
            
        if available.get("can_colonize"):
            point = available["can_colonize"][0]
            fleet_id = None
            fleets = request.game_state.get("players", {}).get("ai_0", {}).get("fleets", [])
            if fleets:
                fleet_id = fleets[0].get("id")
            if fleet_id:
                actions.append({
                    "type": "colonizePlanet",
                    "details": {"fleetId": fleet_id, "planetIndex": point}
                })
                
        actions.append({"type": "endTurn"})
        return actions

