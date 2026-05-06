import json
from ai import ai_complete

def decide_turn(state, personality, difficulty):
    summary = _summarize_state(state)
    prompt = f"You are an AI player in a 4X space game."
    prompt += f"\nPersonality: {personality}, Difficulty: {difficulty}"
    prompt += f"\nGame state:\n{json.dumps(summary)}"
    prompt += "\nReturn a JSON array of actions (e.g. manage_colony, select_research, move_fleet, colonize)."
    prompt += "\nResponse must be valid JSON only."

    raw = ai_complete(prompt)
    if raw:
        try:
            # Strip markdown code blocks if present
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

    return _rule_based_turn(state)

def _summarize_state(state):
    """Builds a compact summary for the LLM."""
    return {
        "turn": state.get("turn"),
        "bc": state.get("bc"),
        "colonies": [
            {
                "id": c.get("id"),
                "star_idx": c.get("star_index"),
                "pop": c.get("population"),
                "assignment": {"f": c.get("farmers"), "w": c.get("workers"), "s": c.get("scientists")},
                "buildings": c.get("buildings", []),
                "queue": c.get("build_queue", [])[:3]
            } for c in state.get("colonies", [])
        ],
        "fleets": [
            {
                "id": f.get("id"),
                "star_idx": f.get("star_index"),
                "transit": f.get("in_transit"),
                "dest": f.get("destination"),
                "eta": f.get("eta"),
                "ships": f.get("ships")
            } for f in state.get("fleets", [])
        ],
        "researched": state.get("tech_state", {}).get("researched", []),
        "available_techs": state.get("available_techs", [])[:20],
        "galaxy_explored": [s for s in state.get("galaxy", {}).get("stars", []) if "player" in s.get("explored_by", [])],
        "relations": state.get("relations", [])
    }

def _rule_based_turn(state):
    """Deterministic fallback when LLM fails."""
    actions = []
    
    # 1. Manage colonies
    for colony in state.get("colonies", []):
        # Build research lab if missing
        if "research_lab" not in colony.get("buildings", []) and not any(i.get("id") == "research_lab" for i in colony.get("build_queue", [])):
            actions.append({"type": "manage_colony", "colony_id": colony["id"], "build_queue": [{"id": "research_lab", "type": "building"}]})
            
    # 2. Select research
    if not state.get("tech_state", {}).get("current_research") and state.get("available_techs"):
        actions.append({"type": "select_research", "tech_id": state["available_techs"][0]})
        
    return actions
