import httpx
from app.models.game import GameModel

class DiplomacyService:
    @staticmethod
    def negotiate_with_ai(game_id, player_id, ai_id, proposal):
        """
        Interacts with the ai-service for diplomatic decisions.
        """
        # Fetch AI personality from game state
        game = GameModel.get_game(None, game_id) # Simplify for example
        if not game: return {"accept": False}
        
        ai_player = next((ai for ai in game["game_state"].get("ai_players", []) if ai["id"] == ai_id), None)
        personality = ai_player.get("personality", "balanced") if ai_player else "balanced"
        
        try:
            # Call ai-service
            response = httpx.post(
                "http://mmoh-ai-service:8000/ai/diplomacy",
                json={
                    "game_id": game_id,
                    "ai_player_id": ai_id,
                    "proposal": proposal,
                    "personality": personality
                },
                timeout=5.0
            )
            return response.json()
        except Exception as e:
            print(f"Diplomacy AI error: {e}")
            return {"accept": False, "reason": "AI Service unreachable"}
