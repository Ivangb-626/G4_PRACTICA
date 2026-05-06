import json

# Personality matrices for the required races
PERSONALITIES = {
    "alkari": {
        "disposition": "defensive",
        "honorable": True,
        "expansionist": False,
        "treaty_weights": {"peace": 1.5, "alliance": 1.2, "trade": 1.0},
        "war_trigger": "provocation"
    },
    "meklar": {
        "disposition": "industrial",
        "honorable": False,
        "expansionist": True,
        "treaty_weights": {"peace": 0.8, "alliance": 0.5, "trade": 2.0},
        "war_trigger": "resource_shortage"
    },
    "trilarian": {
        "disposition": "erratic",
        "honorable": False,
        "expansionist": True,
        "treaty_weights": {"peace": 0.5, "alliance": 0.8, "trade": 1.5},
        "war_trigger": "opportunistic"
    }
}

def decide_diplomacy(data):
    """
    Decides whether to accept a diplomatic proposal based on personality.
    """
    ai_id = data.get("ai_player_id")
    proposal = data.get("proposal", {})
    personality_key = data.get("personality", "balanced").lower()
    
    personality = PERSONALITIES.get(personality_key, {"disposition": "neutral", "treaty_weights": {"peace": 1.0}})
    
    # AI logic: weight based on treaty type and race disposition
    treaty_type = proposal.get("type", "trade")
    weight = personality["treaty_weights"].get(treaty_type, 1.0)
    
    # Decision threshold
    accept = weight > 0.9
    
    return {
        "accept": accept,
        "reason": f"Strategic evaluation for {personality_key}: {weight}"
    }
