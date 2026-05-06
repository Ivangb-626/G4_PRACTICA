"""
antaran_service.py — Ataques aleatorios Antaranos, Portal Dimensional y asalto al sistema Antara.
"""
from __future__ import annotations

import json
import random
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

with (DATA_DIR / "difficulty.json").open("r", encoding="utf-8") as f:
    DIFFICULTY = json.load(f)


def _difficulty_record(diff: str) -> dict:
    rec = DIFFICULTY.get(diff or "officer", {})
    if "alias_of" in rec:
        return DIFFICULTY.get(rec["alias_of"], {})
    return rec


def schedule_initial_attack(game_state: dict) -> None:
    if not game_state.get("antaran_attacks_enabled", True):
        game_state["antaran_next_attack_turn"] = None
        return
    # First attack between turn 100 and 150 in canonical MOO2; we keep low for short games
    base = max(50, game_state.get("antaran_next_attack_turn") or 100)
    game_state["antaran_next_attack_turn"] = base + random.randint(0, 20)


def generate_attack_fleet(turn: int, difficulty: str = "officer") -> dict:
    """Genera una flota Antarana cuya potencia escala con el turno."""
    rec = _difficulty_record(difficulty)
    strength_mult = rec.get("antaran_strength_mult", 1.0)
    tier = min(5, 1 + turn // 60)
    composition = []
    if tier >= 1:
        composition.append({"type": "antaran_destroyer", "count": int(2 * strength_mult)})
    if tier >= 2:
        composition.append({"type": "antaran_cruiser", "count": int(1 * strength_mult)})
    if tier >= 3:
        composition.append({"type": "antaran_cruiser", "count": int(2 * strength_mult)})
    if tier >= 4:
        composition.append({"type": "antaran_battleship", "count": int(1 * strength_mult)})
    if tier >= 5:
        composition.append({"type": "antaran_titan", "count": 1})
    return {
        "id": f"antaran_attack_{turn}",
        "name": "Antaran Raid",
        "owner": "antaranos",
        "ships": [c for c in composition if c.get("count", 0) > 0],
        "destination": None,
        "eta_turns": None,
    }


def select_target_colony(game_state: dict) -> dict:
    """Elige una colonia al azar entre todos los imperios."""
    pool = []
    for emp in [game_state.get("player"), *game_state.get("ai_players", [])]:
        if not emp:
            continue
        for c in emp.get("colonies", []):
            pool.append({"empire_id": emp.get("id", "player"), "colony": c})
    return random.choice(pool) if pool else None


def execute_attack(game_state: dict) -> dict:
    """Resuelve un ataque Antarano contra una colonia aleatoria."""
    from app.services.combat_service import resolve_combat
    target = select_target_colony(game_state)
    if not target:
        return {"type": "antaran_no_target"}

    fleet = generate_attack_fleet(game_state.get("turn", 1), game_state.get("difficulty", "officer"))
    colony = target["colony"]
    empire_id = target["empire_id"]
    empire = game_state.get("player") if empire_id == "player" else next((ai for ai in game_state.get("ai_players", []) if ai["id"] == empire_id), None)

    # Defender: any fleets at the same star system + colony orbital defense
    defender_ships = []
    if empire:
        for fl in empire.get("fleets", []):
            if fl.get("star_system_id") == colony.get("star_system_id"):
                defender_ships.extend(fl.get("ships", []))
    defender_bundle = {"ships": defender_ships}

    result = resolve_combat({"ships": fleet["ships"]}, defender_bundle, defender_orbital_defense=colony.get("orbital_defense", 0))

    if result["winner"] == "attacker" and empire:
        # Antarans destroy the colony entirely
        empire["colonies"] = [c for c in empire.get("colonies", []) if c.get("id") != colony.get("id")]
        return {"type": "antaran_attack_success", "destroyed_colony": colony.get("id"), "empire": empire_id, "log": result.get("log", [])}
    return {"type": "antaran_attack_repelled", "empire": empire_id, "log": result.get("log", [])}


def build_dimensional_portal(game_state: dict, owner_id: str = "player", colony_id: str = None) -> dict:
    if not game_state.get("antaran_attacks_enabled", True):
        return {"success": False, "reason": "Antaran Attacks disabled"}
    if game_state.get("dimensional_portal_built"):
        return {"success": False, "reason": "Portal already built"}
    empire = game_state.get("player") if owner_id == "player" else next((ai for ai in game_state.get("ai_players", []) if ai["id"] == owner_id), None)
    if not empire:
        return {"success": False, "reason": "Empire not found"}

    techs = {t.get("tech_id") for t in empire.get("technologies", {}).get("researched", []) if t.get("status") != "discarded"}
    if "dimensional_portal_tech" not in techs:
        return {"success": False, "reason": "Dimensional Portal tech not researched"}

    cost_bc = 1000
    if empire["resources"].get("bc", 0) < cost_bc:
        return {"success": False, "reason": f"Need {cost_bc} BC"}
    empire["resources"]["bc"] -= cost_bc
    game_state["dimensional_portal_built"] = True
    game_state["dimensional_portal_colony"] = colony_id
    return {"success": True, "message": "Dimensional Portal constructed"}


def attack_antaran_homeworld(game_state: dict, owner_id: str = "player", fleet_id: str = None) -> dict:
    from app.services.combat_service import resolve_combat
    if not game_state.get("dimensional_portal_built"):
        return {"success": False, "reason": "Dimensional Portal not built"}
    empire = game_state.get("player") if owner_id == "player" else next((ai for ai in game_state.get("ai_players", []) if ai["id"] == owner_id), None)
    if not empire:
        return {"success": False, "reason": "Empire not found"}
    fleet = next((f for f in empire.get("fleets", []) if f["id"] == fleet_id), None) if fleet_id else None
    if not fleet:
        return {"success": False, "reason": "Fleet required for the assault"}

    rec = _difficulty_record(game_state.get("difficulty", "officer"))
    mult = rec.get("antaran_strength_mult", 1.0)
    antaran_defense = {
        "ships": [
            {"type": "antaran_titan", "count": max(1, int(1 * mult))},
            {"type": "antaran_battleship", "count": max(2, int(3 * mult))},
            {"type": "antaran_cruiser", "count": max(3, int(5 * mult))},
        ],
    }
    result = resolve_combat({"ships": fleet["ships"]}, antaran_defense, defender_orbital_defense=300)
    if result["winner"] == "attacker":
        game_state["antaran_homeworld_conquered"] = True
        game_state["victory_condition"] = "Antaran"
        return {"success": True, "result": result, "victory": "Antaran"}
    return {"success": False, "result": result}


def maybe_trigger_attack(game_state: dict) -> list:
    """Llamado cada turno por el motor; si toca, dispara un ataque."""
    events = []
    if not game_state.get("antaran_attacks_enabled", True):
        return events
    next_t = game_state.get("antaran_next_attack_turn")
    if next_t is None or game_state["turn"] < next_t:
        return events

    ev = execute_attack(game_state)
    events.append(ev)
    # Reschedule
    game_state["antaran_next_attack_turn"] = game_state["turn"] + max(20, 40 - game_state["turn"] // 20)
    if game_state["turn"] % 20 == 0:
        game_state["antaran_attack_level"] = min(10, game_state.get("antaran_attack_level", 1) + 1)
    return events
