import random
from app.services.colony_service import calculate_colony_production, process_colony_construction
from app.services.research_service import ResearchService
from app.services.diplomacy_service import update_diplomacy_relations
from app.services.event_service import generate_random_events

class TurnEngine:
    @staticmethod
    def execute_turn(game_state):
        """
        Orchestrates the MOO2 turn sequence:
        1. Economy/Growth/Production
        2. Empire-wide Research
        3. Fleet Movement
        4. Combat/Creatures
        5. Diplomacy/Events
        6. AI Execution
        """
        player = game_state["player"]
        
        # 1. Colonies
        for colony in player.get("colonies", []):
            production = calculate_colony_production(colony, player, game_state)
            process_colony_construction(colony, player, game_state, production["production"])
            player["bc"] += production["bc"]
        
        # 2. Research
        ResearchService.process_research(player, player.get("research_accumulated", 0))
        
        # 3. Fleets (Movement update)
        TurnEngine._process_fleets(game_state)
        
        # 4. Events
        events = generate_random_events(game_state)
        
        # 5. Increment turn
        game_state["turn"] += 1
        
        return {"status": "success", "turn": game_state["turn"], "events": events}

    @staticmethod
    def _process_fleets(game_state):
        # Implementation to be added as combat/movement specs are integrated
        pass
