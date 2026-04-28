import json
import os

from app.providers.github_provider import GitHubModelsProvider
from app.providers.groq_provider import GroQProvider


DEFAULT_PROMPT = (
    "Eres el comandante IA en un juego 4X espacial. "
    "Debes generar una lista de acciones JSON con colonizacion, investigacion, "
    "movimiento de flotas y finalizacion de turno."
)


class AIService:
    def __init__(self):
        self.providers = []

        groq_key = os.getenv("GROQ_API_KEY")
        groq_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        if groq_key:
            self.providers.append(GroQProvider(groq_key, groq_model))

        github_token = os.getenv("GITHUB_MODELS_TOKEN")
        github_model = os.getenv("GITHUB_MODELS_MODEL", "gpt-4o")
        if github_token:
            self.providers.append(GitHubModelsProvider(github_token, github_model))

    def build_system_prompt(self, personality, difficulty):
        prompt = "Eres un jugador IA de MasterDeHostias. Decide segun personalidad y dificultad."
        if personality == "aggressive":
            prompt += " Prioriza guerra y expansion militar."
        elif personality == "defensive":
            prompt += " Prioriza seguridad y defensa."
        elif personality == "expansionist":
            prompt += " Prioriza expansion y colonizacion."
        elif personality == "researcher":
            prompt += " Prioriza investigacion y desarrollo."
        else:
            prompt += " Mantente equilibrado."
        prompt += f" Dificultad actual: {difficulty}."
        return prompt

    def build_user_prompt(self, game_state, available_actions):
        safe_state = {**game_state}
        return (
            f"Game state (turn {game_state.get('turn', '?')}):\n"
            f"{json.dumps(safe_state, indent=2)}\n"
            "Available actions:\n"
            f"- can_colonize: {available_actions.get('can_colonize')}\n"
            f"- can_research: {available_actions.get('can_research')}\n"
            f"- available_buildings: {available_actions.get('available_buildings')}\n"
            f"- available_ships: {available_actions.get('available_ships')}\n"
            f"- can_move: {available_actions.get('can_move')}\n"
            "Devuelve JSON con acciones y siempre un endTurn."
        )

    async def call_with_fallback(self, system_prompt, user_prompt):
        for provider in self.providers:
            try:
                return await provider.generate(system_prompt, user_prompt)
            except Exception:
                continue
        return ""

    def parse_response(self, raw):
        if not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            start = raw.find("{")
            end = raw.rfind("}")
            if start != -1 and end != -1 and start < end:
                try:
                    return json.loads(raw[start : end + 1])
                except json.JSONDecodeError:
                    return None
        return None

    def validate_actions(self, actions, game_state, ai_player_id):
        if not isinstance(actions, list):
            return [{"type": "endTurn"}]

        valid = []
        for action in actions:
            if not isinstance(action, dict) or "type" not in action:
                continue
            valid.append(action)
            if action["type"] == "endTurn":
                break

        if not any(action["type"] == "endTurn" for action in valid):
            valid.append({"type": "endTurn"})
        return valid

    def heuristic_actions(self, request):
        available = request.get("available_actions", {})
        actions = []

        if available.get("can_colonize"):
            point = available["can_colonize"][0]
            actions.append(
                {
                    "type": "colonizePlanet",
                    "details": {
                        "fleetId": point.get("fleetId"),
                        "planetIndex": point.get("planetIndex", 0),
                    },
                }
            )

        if available.get("can_research"):
            tech = available["can_research"][0]
            actions.append(
                {
                    "type": "selectResearch",
                    "details": {
                        "techId": tech.get("id"),
                        "field": tech.get("field"),
                        "level": tech.get("level"),
                    },
                }
            )

        if available.get("available_buildings"):
            for colony_id, options in available["available_buildings"].items():
                if options:
                    actions.append(
                        {
                            "type": "addBuildQueue",
                            "details": {
                                "colonyId": colony_id,
                                "itemType": "building",
                                "itemId": options[0].get("id"),
                            },
                        }
                    )
                    break

        if available.get("available_ships") and not any(action["type"] == "addBuildQueue" for action in actions):
            for colony_id, options in available["available_ships"].items():
                preferred = next((ship for ship in options if ship.get("type") == "colony_ship"), None)
                choice = preferred or (options[0] if options else None)
                if choice:
                    actions.append(
                        {
                            "type": "addBuildQueue",
                            "details": {
                                "colonyId": colony_id,
                                "itemType": "ship",
                                "itemId": choice.get("type"),
                            },
                        }
                    )
                    break

        if available.get("can_move"):
            move = available["can_move"][0]
            actions.append(
                {
                    "type": "moveFleet",
                    "details": {
                        "fleetId": move.get("fleetId"),
                        "destination": move.get("destination"),
                    },
                }
            )

        actions.append({"type": "endTurn"})
        return {
            "actions": actions,
            "reasoning": "Heuristic fallback acting due to missing LLM API.",
            "analysis": "No provider configured or model failed.",
        }

    async def get_ai_turn(self, request):
        game_state = request.get("game_state", {})
        ai_player = request.get("game_state", {}).get("ai_player", {})
        personality = ai_player.get("personality", request.get("personality", "balanced"))
        difficulty = request.get("difficulty", "normal")

        system_prompt = self.build_system_prompt(personality, difficulty)
        user_prompt = self.build_user_prompt(game_state, request.get("available_actions", {}))

        raw = await self.call_with_fallback(system_prompt, user_prompt)
        parsed = self.parse_response(raw)
        if not parsed or "actions" not in parsed:
            return self.heuristic_actions(request)

        valid_actions = self.validate_actions(parsed.get("actions", []), game_state, ai_player.get("id", "ai_0"))
        return {
            "actions": valid_actions,
            "reasoning": parsed.get("reasoning", "Decision determined by AI."),
            "analysis": parsed.get("analysis", ""),
        }
