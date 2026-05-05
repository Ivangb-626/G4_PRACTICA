import uuid
import random

LEADER_TEMPLATES = [
    {
        "id": "ld_01", "name": "Kodos", "title": "Fleet Admiral", "type": "fleet",
        "bonuses": {"attack_bonus_pct": 10}, "description": "Experienced admiral",
        "hire_cost": 100, "upkeep": 2
    },
    {
        "id": "ld_02", "name": "Aethel", "title": "Administrator", "type": "colony",
        "bonuses": {"production_bonus_pct": 15}, "description": "Efficient manager",
        "hire_cost": 120, "upkeep": 3
    }
]

def get_hired_leaders(game_state, player_id):
    player = game_state["player"] if player_id == "player" else next((p for p in game_state.get("ai_players", []) if p["id"] == player_id), None)
    return player.get("leaders", []) if player else []

def get_available_leaders(game_state):
    return LEADER_TEMPLATES

def hire_leader(game_state, player_id, leader_template_id):
    player = game_state["player"] if player_id == "player" else next((p for p in game_state.get("ai_players", []) if p["id"] == player_id), None)
    template = next((t for t in LEADER_TEMPLATES if t["id"] == leader_template_id), None)
    
    if not player or not template:
        return {"error": "Invalid player or leader ID"}, 400
        
    if player["resources"]["bc"] < template["hire_cost"]:
        return {"error": "Not enough BC"}, 400
        
    player["resources"]["bc"] -= template["hire_cost"]
    
    new_leader = template.copy()
    new_leader["uid"] = str(uuid.uuid4())
    new_leader["assigned_to"] = None
    
    player.setdefault("leaders", []).append(new_leader)
    return {"leader": new_leader}, 200

def assign_leader(game_state, player_id, leader_uid, target_id):
    player = game_state["player"] if player_id == "player" else next((p for p in game_state.get("ai_players", []) if p["id"] == player_id), None)
    leader = next((l for l in player.get("leaders", []) if l.get("uid") == leader_uid), None)
    
    if not leader:
        return {"error": "Leader not found"}, 404
        
    leader["assigned_to"] = target_id
    return {"leader": leader}, 200

def unassign_leader(game_state, player_id, leader_uid):
    player = game_state["player"] if player_id == "player" else next((p for p in game_state.get("ai_players", []) if p["id"] == player_id), None)
    leader = next((l for l in player.get("leaders", []) if l.get("uid") == leader_uid), None)
    
    if not leader:
        return {"error": "Leader not found"}, 404
        
    leader["assigned_to"] = None
    return {"leader": leader}, 200
