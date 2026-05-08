"""
tactical.py — Decision tactica de combate por turno (LLM con fallback).
"""
import json
import random
from ai import ai_complete


def decide_tactical(data: dict) -> dict:
    state = data.get("state", {})
    unit_uid = data.get("unit_uid")
    personality = (data.get("personality") or "balanced").lower()

    summary = _summarize(state, unit_uid)
    prompt = (
        "You command one ship in a turn-based hex space combat. "
        f"Personality: {personality}. Decide ONE action for unit '{unit_uid}'. "
        "Valid actions: {\"type\":\"fire\",\"target_uid\":...}, {\"type\":\"move\",\"position\":N}, {\"type\":\"retreat\"}, {\"type\":\"wait\"}.\n"
        f"State summary:\n{json.dumps(summary)}\n"
        "Return JSON only."
    )
    raw = ai_complete(prompt)
    if raw:
        try:
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1].rsplit("\n", 1)[0]
            data_action = json.loads(cleaned)
            if isinstance(data_action, dict) and "type" in data_action:
                return data_action
        except Exception:
            pass

    return _fallback(state, unit_uid, personality)


def _summarize(state: dict, unit_uid: str) -> dict:
    units = state.get("units", [])
    me = next((u for u in units if u.get("uid") == unit_uid), None)
    if not me:
        return {"error": "unit not found"}
    enemies = [u for u in units if u.get("alive") and u.get("owner") != me.get("owner")]
    return {
        "me": {"hp": me.get("hp"), "armor": me.get("armor"), "shields": me.get("shields"), "position": me.get("position"), "speed": me.get("speed"), "attack": me.get("attack")},
        "enemies": [
            {"uid": e["uid"], "type": e.get("type"), "hp": e.get("hp"), "armor": e.get("armor"), "shields": e.get("shields"), "position": e.get("position")}
            for e in enemies
        ],
        "round": state.get("round"),
    }


def _fallback(state: dict, unit_uid: str, personality: str) -> dict:
    units = state.get("units", [])
    me = next((u for u in units if u.get("uid") == unit_uid), None)
    if not me:
        return {"type": "wait"}
    
    enemies = [u for u in units if u.get("alive") and u.get("owner") != me.get("owner")]
    if not enemies:
        return {"type": "wait"}

    my_pos = me.get("position", 0)
    my_speed = me.get("speed", 1)
    
    # Prioritize targets:
    # Aggressive: closest, then weakest
    # Balanced: closest
    # Defensive: furthest, then weakest (if low HP)
    
    target_enemy = None
    if personality == "aggressive":
        target_enemy = min(enemies, key=lambda u: (abs(u.get("position", 0) - my_pos), u.get("hp", 0)))
    elif personality == "defensive":
        if me.get("hp", 0) < me.get("max_hp", 1) * 0.5: # If damaged, try to retreat
            # Move away from closest enemy
            closest_enemy = min(enemies, key=lambda u: abs(u.get("position", 0) - my_pos))
            if closest_enemy.get("position", 0) < my_pos: # Enemy is to my left
                new_pos = min(11, my_pos + my_speed) # Move right
            else: # Enemy is to my right
                new_pos = max(0, my_pos - my_speed) # Move left
            return {"type": "move", "position": new_pos}
        else: # Not damaged, act balanced
            target_enemy = min(enemies, key=lambda u: abs(u.get("position", 0) - my_pos))
    else: # Balanced
        target_enemy = min(enemies, key=lambda u: abs(u.get("position", 0) - my_pos))

    if target_enemy:
        target_pos = target_enemy.get("position", 0)
        
        # If in range, fire
        # Simplified range: assume all weapons have a range, just check adjacency or close enough for now
        if abs(target_pos - my_pos) <= me.get("range", 1): # Assume 'range' property exists for simplification
            return {"type": "fire", "target_uid": target_enemy["uid"]}
        else: # Not in range, move closer
            if target_pos > my_pos:
                new_pos = min(11, my_pos + my_speed)
            else:
                new_pos = max(0, my_pos - my_speed)
            return {"type": "move", "position": new_pos}

    return {"type": "wait"}
