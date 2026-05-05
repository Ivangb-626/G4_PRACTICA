import random
import uuid

MISSION_TYPES = ["sabotage", "steal_tech", "assassinate", "incite_revolt"]

def list_spies(game_state, player_id):
    player = game_state["player"] if player_id == "player" else next((p for p in game_state.get("ai_players", []) if p["id"] == player_id), None)
    if not player:
        return []
    return player.get("spies", [])

def recruit_spy(game_state, player_id):
    player = game_state["player"] if player_id == "player" else next((p for p in game_state.get("ai_players", []) if p["id"] == player_id), None)
    if not player:
        return {"error": "Player not found"}, 404
        
    cost = 50
    if player["resources"]["bc"] < cost:
        return {"error": "Not enough BC to recruit spy"}, 400
    
    player["resources"]["bc"] -= cost
    spy = {
        "id": str(uuid.uuid4()),
        "name": f"Agent {random.randint(100, 999)}",
        "skill": random.randint(10, 30),
        "status": "idle",
        "mission": None,
        "assigned_to": None
    }
    
    if "spies" not in player:
        player["spies"] = []
    
    player["spies"].append(spy)
    return {"spy": spy}, 200

def assign_mission(game_state, player_id, spy_id, target_id, mission_type):
    player = game_state["player"] if player_id == "player" else next((p for p in game_state.get("ai_players", []) if p["id"] == player_id), None)
    spies = player.get("spies", [])
    spy = next((s for s in spies if s["id"] == spy_id), None)
    
    if not spy:
        return {"error": "Spy not found"}, 404
        
    if mission_type not in MISSION_TYPES:
        return {"error": "Invalid mission type"}, 400
        
    spy["status"] = "on_mission"
    spy["mission"] = mission_type
    spy["assigned_to"] = target_id
    
    return {"spy": spy}, 200
