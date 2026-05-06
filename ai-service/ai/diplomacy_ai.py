"""
diplomacy_ai.py — IA diplomatica del juego. Combina personalidad por raza con
una rejilla de pesos por tipo de tratado y opcionalmente apoya con LLM si
disponible.
"""
import json
from ai import ai_complete


PERSONALITIES = {
    "alkari": {
        "disposition": "defensive",
        "honorable": True,
        "expansionist": False,
        "treaty_weights": {"non_aggression_pact": 1.5, "alliance": 1.2, "trade_treaty": 1.0, "research_pact": 1.1, "tribute": 0.6},
        "war_trigger": "provocation",
    },
    "meklar": {
        "disposition": "industrial",
        "honorable": False,
        "expansionist": True,
        "treaty_weights": {"non_aggression_pact": 0.8, "alliance": 0.5, "trade_treaty": 2.0, "research_pact": 1.5, "tribute": 0.8},
        "war_trigger": "resource_shortage",
    },
    "trilarian": {
        "disposition": "erratic",
        "honorable": False,
        "expansionist": True,
        "treaty_weights": {"non_aggression_pact": 0.7, "alliance": 0.8, "trade_treaty": 1.4, "research_pact": 1.6, "tribute": 0.9},
        "war_trigger": "opportunistic",
    },
    "balanced": {
        "treaty_weights": {"non_aggression_pact": 1.0, "alliance": 1.0, "trade_treaty": 1.0, "research_pact": 1.0, "tribute": 0.7},
    },
}


def decide_diplomacy(data: dict) -> dict:
    proposal = data.get("proposal", {}) or {}
    personality_key = (data.get("personality") or "balanced").lower()
    relation_value = data.get("relation_value", 30)
    treaty_type = proposal.get("type", "trade_treaty")

    personality = PERSONALITIES.get(personality_key, PERSONALITIES["balanced"])
    weight = personality["treaty_weights"].get(treaty_type, 1.0)

    # Try LLM for a richer reason if available
    llm_text = ""
    try:
        prompt = (
            "You are an alien empire's diplomat in a 4X game. "
            f"Race: {personality_key}. Relation value (0-100): {relation_value}. "
            f"Proposal: {json.dumps(proposal)}. "
            "Decide accept (true/false) and a one-sentence reason. Return JSON like {\"accept\":true, \"reason\":\"...\"}."
        )
        raw = ai_complete(prompt)
        if raw:
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1].rsplit("\n", 1)[0]
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict) and "accept" in parsed:
                return {"accept": bool(parsed.get("accept")), "reason": parsed.get("reason", "")}
    except Exception:
        pass

    # Heuristic fallback
    threshold = max(20, 60 - int(weight * 30))
    accept = relation_value >= threshold
    return {
        "accept": accept,
        "reason": f"{personality_key} weight={weight:.2f} vs threshold {threshold} (relation {relation_value})",
    }
