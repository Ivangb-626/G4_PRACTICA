"""
score_service.py — Calculo de puntuacion final.

Formula:
  base = max(0, 500 - turns)
  + captured_colonists * 2
  + own_population * 1
  + hyper_advanced_techs * 5
  + rivals_eliminated * 50
  + (guardian_defeated ? 100 : 0)
  + (antarans_defeated ? 200 : 0)
  + galactic_ruler_bonus (50 ajustado, 100 amplio)
final = subtotal * custom_race_multiplier
"""
from __future__ import annotations


def calculate_final_score(game_state: dict, owner_id: str = "player") -> dict:
    if owner_id == "player":
        empire = game_state.get("player", {})
    else:
        empire = next((ai for ai in game_state.get("ai_players", []) if ai["id"] == owner_id), None) or {}

    turn = game_state.get("turn", 1)
    base = max(0, 500 - turn)

    own_pop = sum(
        c.get("population", {}).get("total", 0) if isinstance(c.get("population"), dict) else 0
        for c in empire.get("colonies", [])
    )

    captured = empire.get("stats", {}).get("captured_colonists", 0)
    rivals = empire.get("stats", {}).get("rivals_eliminated", 0)

    techs = empire.get("technologies", {}).get("researched", [])
    hyper_count = sum(1 for t in techs if t.get("level", 0) >= 8 and t.get("status") != "discarded")

    guardian = 100 if game_state.get("orion_guardian_defeated") and empire.get("stats", {}).get("defeated_guardian", False) else 0
    if not empire.get("stats", {}).get("defeated_guardian", False) and game_state.get("orion_guardian_defeated") and owner_id == "player":
        guardian = 100  # heuristic if no per-empire stat
    antarans = 200 if game_state.get("antaran_homeworld_conquered") else 0
    council_bonus = empire.get("stats", {}).get("council_bonus", 0)

    breakdown = {
        "base": base,
        "captured_colonists": captured * 2,
        "own_population": own_pop,
        "hyper_advanced_techs": hyper_count * 5,
        "rivals_eliminated": rivals * 50,
        "guardian_defeated": guardian,
        "antarans_defeated": antarans,
        "galactic_ruler": council_bonus,
    }
    subtotal = sum(breakdown.values())

    multiplier = empire.get("custom_race_multiplier", 1.0)
    final = int(round(subtotal * multiplier))

    return {
        "breakdown": breakdown,
        "subtotal": subtotal,
        "custom_race_multiplier": multiplier,
        "final": final,
        "owner": owner_id,
        "victory_condition": game_state.get("victory_condition"),
    }
