import os
import json
import asyncio
import random
from app.providers.groq_provider import GroQProvider
from app.providers.github_provider import GitHubModelsProvider

DEFAULT_PROMPT = """Eres el comandante IA en un juego 4X espacial. Debes generar una lista de acciones en formato JSON que incluyan colonización, investigación, movimiento de flotas y finalización de turno. Responde siempre en JSON con llaves: actions, reasoning, analysis."""


class AIService:
    def __init__(self):
        self.providers = []

        groq_key = os.getenv('GROQ_API_KEY')
        groq_model = os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')
        if groq_key:
            self.providers.append(GroQProvider(groq_key, groq_model))

        gh_token = os.getenv('GITHUB_MODELS_TOKEN')
        gh_model = os.getenv('GITHUB_MODELS_MODEL', 'gpt-4o')
        if gh_token:
            self.providers.append(GitHubModelsProvider(gh_token, gh_model))

    def build_system_prompt(self, personality: str, difficulty: str) -> str:
        base = "Eres un AI player de MasterDeHostias. Juega de acuerdo a la personalidad proporcionada y a la dificultad."
        if personality == 'aggressive':
            base += ' Prioriza ataques y producción militar.'
        elif personality == 'defensive':
            base += ' Prioriza defensas y estabilidad.'
        elif personality == 'expansionist':
            base += ' Prioriza colonización rápida.'
        elif personality == 'researcher':
            base += ' Prioriza investigación.'
        else:
            base += ' Mantente equilibrado.'
        return base

    def build_user_prompt(self, game_state: dict, available_actions: dict) -> str:
        safe_state = {**game_state}
        # in this release no filtering more allá; ya viene prefiltrado
        return (
            f"Game state (turn {game_state.get('turn', '?')}):\n"
            f"{json.dumps(safe_state, indent=2)}\n"
            "Available actions:\n"
            f"- can_colonize: {available_actions.get('can_colonize')}\n"
            f"- can_research: {available_actions.get('can_research')}\n"
            f"- available_buildings: {available_actions.get('available_buildings')}\n"
            f"- available_ships: {available_actions.get('available_ships')}\n"
            "Devuelve JSON con acciones y siempre un endTurn."
        )

    async def call_with_fallback(self, system_prompt: str, user_prompt: str) -> str:
        for provider in self.providers:
            try:
                result = await provider.generate(system_prompt, user_prompt)
                return result
            except Exception:
                continue
        # Sin modelo disponible, caer en fallback local
        return ''

    def parse_response(self, raw: str):
        if not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # intentar extraer JSON de texto libre
            start = raw.find('{')
            end = raw.rfind('}')
            if start != -1 and end != -1 and start < end:
                try:
                    return json.loads(raw[start:end+1])
                except json.JSONDecodeError:
                    pass
        return None

    def validate_actions(self, actions: list, game_state: dict, ai_player_id: str):
        if not isinstance(actions, list):
            return [{'type': 'endTurn'}]
        valid = []
        for action in actions:
            if not isinstance(action, dict) or 'type' not in action:
                continue
            if action['type'] == 'endTurn':
                valid.append({'type': 'endTurn'})
                break
            # keep all non-malformed actions as placeholders
            valid.append(action)
        if not any(a['type'] == 'endTurn' for a in valid):
            valid.append({'type': 'endTurn'})
        return valid

    def heuristic_actions(self, request: dict):
        available = request.get('available_actions', {})
        actions = []
        if available.get('can_research'):
            tech = available['can_research'][0]
            actions.append({'type': 'selectResearch', 'details': {'techId': tech, 'field': 'physics', 'level': 1}})
        if available.get('can_colonize'):
            point = available['can_colonize'][0]
            fleet_id = None
            if request.get('game_state', {}).get('ai_player', {}).get('fleets'):
                fleet_id = request['game_state']['ai_player']['fleets'][0]['id']
            if fleet_id:
                actions.append({'type': 'colonizePlanet', 'details': {'fleetId': fleet_id, 'planetIndex': 0}})
        actions.append({'type': 'endTurn'})
        return {
            'actions': actions,
            'reasoning': 'Heuristic fallback acting due to missing LLM API.',
            'analysis': 'No provider configured or model failed.'
        }

    async def get_ai_turn(self, request: dict):
        game_state = request.get('game_state', {})
        ai_player = request.get('game_state', {}).get('ai_player', {})
        personality = ai_player.get('personality', request.get('personality', 'balanced'))
        difficulty = request.get('difficulty', 'normal')

        system_prompt = self.build_system_prompt(personality, difficulty)
        user_prompt = self.build_user_prompt(game_state, request.get('available_actions', {}))

        raw = await self.call_with_fallback(system_prompt, user_prompt)
        parsed = self.parse_response(raw)
        if not parsed or 'actions' not in parsed:
            return self.heuristic_actions(request)

        valid_actions = self.validate_actions(parsed.get('actions', []), game_state, ai_player.get('id', 'ai_0'))

        return {
            'actions': valid_actions,
            'reasoning': parsed.get('reasoning', 'Decisión determinada por IA.'),
            'analysis': parsed.get('analysis', '')
        }
