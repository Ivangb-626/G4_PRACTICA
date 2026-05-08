import json
import math
from ai import ai_complete

def decide_turn(state, personality, difficulty, available_actions=None):
    """
    Main entry point. `state` comes from the backend as:
    {"turn": N, "ai_player": {colonies, fleets, technologies, resources, race, ...}}
    `available_actions` is a dict of valid moves computed by the backend.
    """
    if not state:
        return []

    summary = _summarize_state(state)
    prompt = f"You are an AI player in a 4X space game."
    prompt += f"\nPersonality: {personality}, Difficulty: {difficulty}"
    prompt += f"\nGame state:\n{json.dumps(summary)}"
    if available_actions:
        prompt += f"\nAvailable actions:\n{json.dumps(available_actions)}"
    prompt += "\nReturn a JSON array of actions (e.g. manage_colony, select_research, move_fleet, colonize)."
    prompt += "\nResponse must be valid JSON only."

    raw = ai_complete(prompt)
    if raw:
        try:
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1].rsplit("\n", 1)[0]
            
            actions = json.loads(cleaned)
            if isinstance(actions, dict) and "actions" in actions:
                return actions["actions"]
            if isinstance(actions, list):
                return actions
        except Exception as e:
            print(f"JSON parse error: {e}")

    return _rule_based_turn(state, available_actions)

def _summarize_state(state):
    """Builds a compact summary for the LLM.
    Navigates the nested ai_player structure correctly."""
    ai = state.get("ai_player", {})
    return {
        "turn": state.get("turn"),
        "bc": ai.get("resources", {}).get("bc", 0),
        "colonies": [
            {
                "id": c.get("id"),
                "star_system_id": c.get("star_system_id"),
                "pop": c.get("population", {}).get("total", 0),
                "max_pop": c.get("population", {}).get("max", 0),
                "assignment": {
                    "f": c.get("population", {}).get("farmers", 0),
                    "w": c.get("population", {}).get("workers", 0),
                    "s": c.get("population", {}).get("scientists", 0)
                },
                "buildings": c.get("buildings", []),
                "queue": c.get("build_queue", [])[:3]
            } for c in ai.get("colonies", [])
        ],
        "fleets": [
            {
                "id": f.get("id"),
                "star_system_id": f.get("star_system_id"),
                "in_transit": f.get("destination") is not None,
                "dest": f.get("destination"),
                "eta": f.get("eta_turns"),
                "ships": f.get("ships")
            } for f in ai.get("fleets", [])
        ],
        "researched": [t.get("tech_id") for t in ai.get("technologies", {}).get("researched", []) if t.get("status") != "discarded"],
        "current_research": ai.get("technologies", {}).get("current_research"),
    }

def _rule_based_turn(state, available_actions=None):
    """Deterministic fallback when LLM fails.
    Uses available_actions from the backend for valid moves."""
    actions = []
    ai = state.get("ai_player", {}) if state else {}
    avail = available_actions or {}
    
    # 1. Select research if none active
    if not ai.get("technologies", {}).get("current_research"):
        can_research = avail.get("can_research", [])
        if can_research:
            # Prefer cheaper techs first
            tech = min(can_research, key=lambda t: t.get("research_cost", 9999))
            actions.append({"type": "selectResearch", "details": {"techId": tech.get("id") or tech.get("tech_id")}})

    # 2. Manage colony build queues
    for colony in ai.get("colonies", []):
        cid = colony.get("id")
        buildings = colony.get("buildings", [])
        queue = colony.get("build_queue", [])
        
        if queue:
            continue  # Already building something

        # Get available buildings for this colony from backend
        colony_buildings = avail.get("available_buildings", {}).get(cid, [])
        colony_ships = avail.get("available_ships", {}).get(cid, [])
        
        # Priority: research_lab > automated_factory > marine_barracks > frigate
        priority_buildings = ["research_lab", "automated_factory", "marine_barracks", "hydroponic_farm"]
        queued = False
        for bid in priority_buildings:
            if bid not in buildings and any(b.get("id") == bid for b in colony_buildings):
                actions.append({"type": "addBuildQueue", "details": {"colonyId": cid, "itemType": "building", "itemId": bid}})
                queued = True
                break
        
        # If no priority building, build a frigate
        if not queued and colony_ships:
            actions.append({"type": "addBuildQueue", "details": {"colonyId": cid, "itemType": "ship", "itemId": "frigate"}})

    # 3. Colonize if possible
    can_colonize = avail.get("can_colonize", [])
    for col_action in can_colonize[:1]:  # Colonize one at a time
        actions.append({"type": "colonizePlanet", "details": {
            "fleetId": col_action.get("fleetId"),
            "planetIndex": col_action.get("planetIndex"),
        }})

    # 4. Explore with fleets
    can_move = avail.get("can_move", [])
    moved_fleets = set()
    for move in can_move:
        fid = move.get("fleetId")
        if fid in moved_fleets:
            continue
        # Prioritize unexplored systems (priority 0)
        if move.get("priority", 1) == 0:
            actions.append({"type": "moveFleet", "details": {
                "fleetId": fid,
                "destination": move.get("destination"),
            }})
            moved_fleets.add(fid)
        
    return actions
