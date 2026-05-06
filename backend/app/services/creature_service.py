"""
creature_service.py — Monstruos espaciales y Guardian de Orion.
"""
from __future__ import annotations

import json
import random
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

with (DATA_DIR / "space_monsters.json").open("r", encoding="utf-8") as f:
    MONSTERS = {m["id"]: m for m in json.load(f)}


def get_monster_data(kind: str) -> dict:
    return MONSTERS.get(kind, {})


def spawn_monster(system: dict, kind: str = None) -> dict:
    kind = kind or random.choice(["space_eel", "space_amoeba", "space_kraken", "space_crystal"])
    system["space_monster"] = {
        "type": kind,
        "is_travelling": random.random() < 0.25,
        "defeated": False,
    }
    return system["space_monster"]


def monster_movement(game_state: dict) -> list:
    """Algunos monstruos deambulan entre sistemas conectados."""
    events = []
    for system in game_state["galaxy"]["star_systems"]:
        m = system.get("space_monster")
        if not m or m.get("defeated") or not m.get("is_travelling"):
            continue
        if random.random() < 0.10:
            connections = system.get("connections", [])
            if connections:
                target_id = random.choice(connections)
                target = next((s for s in game_state["galaxy"]["star_systems"] if s["id"] == target_id), None)
                if target and not target.get("space_monster") and not target.get("guardian", {}).get("active"):
                    target["space_monster"] = m
                    system["space_monster"] = None
                    events.append({"type": "monster_moved", "from": system["id"], "to": target_id, "kind": m["type"]})
    return events


def resolve_monster_combat(monster_kind: str, attacker_bundle: dict, leader_bonus: int = 0):
    """Adapta el combate del bestiario a resolve_combat. leader_bonus: +Galactic Lore."""
    from app.services.combat_service import resolve_combat, SHIP_TYPES

    monster_data = MONSTERS.get(monster_kind, {})
    # Wrap monster as a synthetic ship for combat metrics
    pseudo_ship = {
        "type": f"_monster_{monster_kind}",
        "hp": monster_data.get("hp", 100),
        "armor": monster_data.get("armor", 50),
        "attack": monster_data.get("attack", 50),
        "defense": monster_data.get("defense", 30),
        "command_points": 0,
        "cost": 0,
        "speed": monster_data.get("speed", 4),
    }
    types = dict(SHIP_TYPES)
    types[pseudo_ship["type"]] = pseudo_ship

    defender = {"ships": [{"type": pseudo_ship["type"], "count": 1}]}
    # Apply leader_bonus by buffing attacker bundle attack
    attacker_clone = {
        "ships": [
            {
                "type": s["type"],
                "count": s.get("count", 0),
            }
            for s in attacker_bundle.get("ships", [])
        ]
    }
    result = resolve_combat(attacker_clone, defender, ship_types_data=types)
    return result


def defeat_monster(system: dict, empire: dict) -> dict:
    """Aplica recompensas al derrotar un monstruo."""
    m = system.get("space_monster")
    if not m or m.get("defeated"):
        return {"success": False, "reason": "No live monster here"}
    monster_data = MONSTERS.get(m["type"], {})
    m["defeated"] = True

    bc_reward = monster_data.get("destroy_reward_bc", 100)
    empire["resources"]["bc"] = empire.get("resources", {}).get("bc", 0) + bc_reward

    tech_drop = None
    drop_chance = monster_data.get("tech_drop_chance", 0)
    if random.random() < drop_chance:
        # Random tech bonus pool
        tech_drop = random.choice(["heavy_armor", "battle_scanner", "auto_repair", "structural_analyzer"])
        empire.setdefault("technologies", {}).setdefault("researched", []).append(
            {"tech_id": tech_drop, "field": "engineering", "level": 3, "status": "researched"}
        )

    return {"success": True, "monster": m["type"], "bc_reward": bc_reward, "tech_drop": tech_drop}
