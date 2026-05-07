"""
ai_service.py — Cliente HTTP del microservicio `ai-service`.

Decisiones (turno, diplomacia, tactica, voto del Senado, espionaje) se delegan
al microservicio via HTTP. Si la red falla, se usa un fallback heuristico.

Variables de entorno relevantes:
- AI_SERVICE_URL      (default http://mmoh-ai-service:8000)
- AI_SERVICE_TIMEOUT  (default 8.0)
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

import httpx


AI_SERVICE_URL = os.environ.get("AI_SERVICE_URL", "http://ai-service:8001")
AI_SERVICE_TIMEOUT = float(os.environ.get("AI_SERVICE_TIMEOUT", "8.0"))


class AIService:
    """Wrapper sincrono y asincrono. game_service.py llama get_ai_turn() async."""

    def __init__(self):
        self.url = AI_SERVICE_URL
        self.timeout = AI_SERVICE_TIMEOUT

    # ---------- Async helpers ----------
    async def _post_async(self, path: str, payload: dict) -> dict:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(f"{self.url}{path}", json=payload)
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            return {"_error": str(e)}

    def _post_sync(self, path: str, payload: dict) -> dict:
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(f"{self.url}{path}", json=payload)
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            return {"_error": str(e)}

    # ---------- Public API ----------
    async def get_ai_turn(self, request: dict) -> dict:
        """Delegate to ai-service /ai/turn. request must include game_state, available_actions."""
        ai_player = request.get("game_state", {}).get("ai_player", {}) or {}
        personality = ai_player.get("personality") or request.get("personality", "balanced")
        difficulty = request.get("difficulty", "officer")

        payload = {
            "state": _summarize_state(request.get("game_state", {}), request.get("available_actions", {})),
            "personality": personality,
            "difficulty": difficulty,
        }
        result = await self._post_async("/ai/turn", payload)

        if "_error" in result or not result.get("actions"):
            return self.heuristic_actions(request)

        actions = self.validate_actions(result.get("actions", []), request.get("game_state", {}), ai_player.get("id", "ai_0"))
        return {
            "actions": actions,
            "reasoning": result.get("reasoning", "AI service decision"),
            "analysis": result.get("analysis", ""),
        }

    def evaluate_diplomacy(self, ai_player: dict, proposal: dict, relation_value: int = 30) -> dict:
        payload = {
            "ai_player_id": ai_player.get("id"),
            "personality": ai_player.get("personality") or ai_player.get("race", {}).get("ai_personality", "balanced"),
            "proposal": proposal,
            "relation_value": relation_value,
        }
        result = self._post_sync("/ai/diplomacy", payload)
        if "_error" in result:
            return {"accept": False, "reason": "AI service unreachable"}
        return result

    def evaluate_council_vote(self, ai_player: dict, candidates: list, relations: dict) -> dict:
        payload = {
            "ai_player_id": ai_player.get("id"),
            "personality": ai_player.get("personality") or ai_player.get("race", {}).get("ai_personality", "balanced"),
            "candidates": candidates,
            "relations": relations,
        }
        result = self._post_sync("/ai/council_vote", payload)
        if "_error" in result:
            return {"choice": None, "reason": "AI service unreachable"}
        return result

    def decide_tactical_action(self, state: dict, unit_uid: str, personality: str = "balanced") -> dict:
        payload = {"state": state, "unit_uid": unit_uid, "personality": personality}
        result = self._post_sync("/ai/tactical", payload)
        if "_error" in result:
            return {"type": "wait"}
        return result.get("action", {"type": "wait"})

    def evaluate_espionage(self, ai_player: dict, possible_targets: list) -> dict:
        payload = {
            "ai_player_id": ai_player.get("id"),
            "personality": ai_player.get("personality") or ai_player.get("race", {}).get("ai_personality", "balanced"),
            "possible_targets": possible_targets,
        }
        result = self._post_sync("/ai/espionage", payload)
        if "_error" in result:
            return {"mission": None, "target": None}
        return result

    # ---------- Validation & fallback ----------
    def validate_actions(self, actions, game_state, ai_player_id) -> list:
        if not isinstance(actions, list):
            return [{"type": "endTurn"}]
        valid = []
        for action in actions:
            if not isinstance(action, dict) or "type" not in action:
                continue
            valid.append(action)
            if action["type"] == "endTurn":
                break
        if not any(a.get("type") == "endTurn" for a in valid):
            valid.append({"type": "endTurn"})
        return valid

    def heuristic_actions(self, request: dict) -> dict:
        """Fallback if ai-service is unreachable."""
        available = request.get("available_actions", {})
        actions: List[Dict[str, Any]] = []

        if available.get("can_colonize"):
            point = available["can_colonize"][0]
            actions.append({"type": "colonizePlanet", "details": {"fleetId": point.get("fleetId"), "planetIndex": point.get("planetIndex", 0)}})

        if available.get("can_research"):
            tech = available["can_research"][0]
            actions.append({"type": "selectResearch", "details": {"techId": tech.get("id") or tech.get("tech_id"), "field": tech.get("field"), "level": tech.get("level")}})

        if available.get("available_buildings"):
            for colony_id, options in available["available_buildings"].items():
                if options:
                    actions.append({"type": "addBuildQueue", "details": {"colonyId": colony_id, "itemType": "building", "itemId": options[0].get("id")}})
                    break

        if available.get("available_ships") and not any(a["type"] == "addBuildQueue" for a in actions):
            for colony_id, options in available["available_ships"].items():
                if not options:
                    continue
                preferred = next((s for s in options if s.get("type") == "colony_ship"), None)
                choice = preferred or options[0]
                actions.append({"type": "addBuildQueue", "details": {"colonyId": colony_id, "itemType": "ship", "itemId": choice.get("type")}})
                break

        if available.get("can_move"):
            move = available["can_move"][0]
            actions.append({"type": "moveFleet", "details": {"fleetId": move.get("fleetId"), "destination": move.get("destination")}})

        actions.append({"type": "endTurn"})
        return {"actions": actions, "reasoning": "Heuristic fallback (ai-service unreachable)", "analysis": ""}


def _summarize_state(game_state: dict, available: dict) -> dict:
    """Resumen compacto enviado al ai-service. Evita payloads enormes."""
    ai_player = game_state.get("ai_player", {}) or {}
    return {
        "turn": game_state.get("turn"),
        "bc": ai_player.get("resources", {}).get("bc"),
        "colonies": [
            {
                "id": c.get("id"),
                "star_system_id": c.get("star_system_id"),
                "population": c.get("population", {}),
                "buildings": c.get("buildings", []),
                "build_queue": c.get("build_queue", [])[:3],
            }
            for c in ai_player.get("colonies", [])[:10]
        ],
        "fleets": [
            {
                "id": f.get("id"),
                "star_system_id": f.get("star_system_id"),
                "destination": f.get("destination"),
                "ships": f.get("ships", []),
            }
            for f in ai_player.get("fleets", [])[:10]
        ],
        "researched": [
            t.get("tech_id") for t in ai_player.get("technologies", {}).get("researched", []) if t.get("status") != "discarded"
        ][:30],
        "current_research": ai_player.get("technologies", {}).get("current_research"),
        "available_actions": {
            "can_colonize": (available.get("can_colonize") or [])[:5],
            "can_research_count": len(available.get("can_research") or []),
            "available_buildings": {k: [b.get("id") for b in v[:3]] for k, v in (available.get("available_buildings") or {}).items()},
            "available_ships": {k: [s.get("type") for s in v[:3]] for k, v in (available.get("available_ships") or {}).items()},
            "can_move": (available.get("can_move") or [])[:5],
        },
    }
