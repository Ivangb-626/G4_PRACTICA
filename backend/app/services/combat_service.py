"""
combat_service.py — Resolucion automatica de combates espaciales y terrestres.
"""
from __future__ import annotations

import json
import random
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

with (DATA_DIR / "ships.json").open("r", encoding="utf-8") as f:
    SHIP_TYPES = {item["type"]: item for item in json.load(f)}


def _ship_power(ship_type: dict) -> float:
    hp = ship_type.get("hp", 0)
    armor = ship_type.get("armor", 0)
    attack = ship_type.get("attack", 0)
    defense = ship_type.get("defense", 0)
    return hp + armor * 0.5 + attack * 1.2 + defense * 0.3


def _bundle_power(bundle: dict, ship_types: dict) -> float:
    total = 0.0
    for ship in bundle.get("ships", []):
        st = ship_types.get(ship["type"])
        if not st:
            continue
        total += _ship_power(st) * ship.get("count", 0)
    return total


def _apply_losses(bundle: dict, loss_ratio: float, ship_types: dict) -> list:
    if loss_ratio <= 0:
        return list(bundle.get("ships", []))
    remaining = []
    ordered = sorted(
        list(bundle.get("ships", [])),
        key=lambda s: ship_types.get(s["type"], {}).get("cost", 0),
    )
    losses_pct = min(loss_ratio, 1.0)
    for ship in ordered:
        cnt = ship.get("count", 0)
        kept = max(0, cnt - int(round(cnt * losses_pct)))
        if kept > 0:
            remaining.append({"type": ship["type"], "count": kept})
    return remaining


def resolve_combat(attacker_bundle: dict, defender_bundle: dict, defender_orbital_defense: int = 0, ship_types_data: dict = None) -> dict:
    types = ship_types_data or SHIP_TYPES
    atk_power = _bundle_power(attacker_bundle, types)
    def_power = _bundle_power(defender_bundle, types) + (defender_orbital_defense or 0)

    if atk_power <= 0 and def_power <= 0:
        return {"winner": "draw", "attacker_remaining": [], "defender_remaining": [], "log": []}

    atk_roll = atk_power * random.uniform(0.7, 1.3)
    def_roll = def_power * random.uniform(0.7, 1.3)

    log = [f"Atk power={atk_power:.1f} (roll {atk_roll:.1f}) vs Def power={def_power:.1f} (roll {def_roll:.1f})"]

    if atk_roll >= def_roll:
        winner = "attacker"
        loss_atk = min(0.6, def_roll / max(atk_roll, 1.0) * 0.7)
        loss_def = 1.0
    else:
        winner = "defender"
        loss_atk = 1.0
        loss_def = min(0.6, atk_roll / max(def_roll, 1.0) * 0.7)

    atk_remaining = _apply_losses(attacker_bundle, loss_atk, types)
    def_remaining = _apply_losses(defender_bundle, loss_def, types)
    log.append(f"Winner: {winner}. Atk losses {loss_atk*100:.0f}%, Def losses {loss_def*100:.0f}%.")

    return {
        "winner": winner,
        "attacker_remaining": atk_remaining,
        "defender_remaining": def_remaining,
        "log": log,
    }


def resolve_ground_combat(marines_attacker: int, attacker_bonus: int, target_colony: dict, defender_bonus: int) -> dict:
    pop = target_colony.get("population", {})
    pop_total = pop.get("total", 1) if isinstance(pop, dict) else 1
    defender_marines = max(1, target_colony.get("ground_defense", 0) + int(pop_total))
    atk_power = max(0, marines_attacker) * (1 + attacker_bonus / 100.0)
    def_power = defender_marines * (1 + defender_bonus / 100.0)

    if atk_power <= 0:
        return {"winner": "defender", "attacker_remaining": 0, "defender_remaining": defender_marines}

    atk_roll = atk_power * random.uniform(0.85, 1.15)
    def_roll = def_power * random.uniform(0.85, 1.15)

    if atk_roll >= def_roll:
        survival = max(0.1, 1.0 - def_roll / max(atk_roll, 1.0))
        atk_remaining = max(1, int(round(marines_attacker * survival)))
        return {"winner": "attacker", "attacker_remaining": atk_remaining, "defender_remaining": 0}
    survival = max(0.1, 1.0 - atk_roll / max(def_roll, 1.0))
    return {
        "winner": "defender",
        "attacker_remaining": 0,
        "defender_remaining": max(1, int(round(defender_marines * survival))),
    }
