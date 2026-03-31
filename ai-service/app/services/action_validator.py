def validate_single_action(action: dict, game_state: dict, ai_player_id: str) -> bool:
    """Validate that moving fleets, managing colonies, etc. makes sense."""
    action_type = action.get("type")
    details = action.get("details", {})

    if action_type == "manageColony":
        if "colonyId" not in details: return False
        return True
        
    elif action_type == "selectResearch":
        if "techId" not in details: return False
        return True
        
    elif action_type == "moveFleet":
        if "fleetId" not in details or "destination" not in details: return False
        return True
        
    elif action_type == "colonizePlanet":
        if "fleetId" not in details or "planetIndex" not in details: return False
        return True
        
    elif action_type in ["buildShip", "buildBuilding"]:
        return True
        
    elif action_type == "attackSystem":
        return True
        
    elif action_type == "endTurn":
        return True
        
    elif action_type in ["proposeTreaty", "declareWar"]:
        return True

    return False

def validate_actions(actions: list[dict], game_state: dict, ai_player_id: str) -> list[dict]:
    """Validate sequence of actions and ensure ending with endTurn."""
    valid = []
    
    for action in actions:
        if isinstance(action, dict) and validate_single_action(action, game_state, ai_player_id):
            valid.append(action)

    # Ensure endTurn is at the very end
    if not any(a.get("type") == "endTurn" for a in valid):
        valid.append({"type": "endTurn"})
        
    return valid
