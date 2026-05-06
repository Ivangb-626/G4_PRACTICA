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
    # Aggressive personalities: target weakest. Defensive: kite.
    target = min(enemies, key=lambda u: u.get("hp", 0) + u.get("armor", 0) + u.get("shields", 0))
    if personality == "defensive" and me.get("hp", 0) < me.get("max_hp", 1) * 0.30:
        new_pos = max(0, me.get("position", 5) - me.get("speed", 1))
        return {"type": "move", "position": new_pos}
    return {"type": "fire", "target_uid": target["uid"]}
