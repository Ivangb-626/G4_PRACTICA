"""
tactical_combat.py — Resolucion paso a paso del combate espacial en tablero.

Modelo simplificado: posiciones X (0..30) en una linea (no hex completo, pero
suficiente para targeting/range). Cada nave tiene HP, armor, shields, attack,
defense y un arma principal con damage_min/damage_max. Soporta:
- Mover (cambia posicion)
- Disparar (calculo to-hit + escudo + armor)
- Retirar
- Resolucion automatica si se solicita

Para flujo full-IA, ai-service /ai/tactical decide cada turno.
"""
from __future__ import annotations

import json
import random
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

with (DATA_DIR / "ships.json").open("r", encoding="utf-8") as f:
    SHIP_TYPES = {item["type"]: item for item in json.load(f)}

with (DATA_DIR / "weapons.json").open("r", encoding="utf-8") as f:
    WEAPONS = json.load(f)

ALL_WEAPONS = {w["id"]: w for grp in WEAPONS.values() for w in grp}


def _make_unit(ship: dict, owner: str, position: int) -> dict:
    st = SHIP_TYPES.get(ship["type"], {})
    return {
        "uid": f"{owner}_{ship['type']}_{position}_{random.randint(1000,9999)}",
        "owner": owner,
        "type": ship["type"],
        "hp": st.get("hp", 10),
        "max_hp": st.get("hp", 10),
        "armor": st.get("armor", 0),
        "shields": st.get("hp", 10) // 4,
        "attack": st.get("attack", 5),
        "defense": st.get("defense", 0),
        "speed": st.get("speed", 2),
        "position": position,
        "alive": True,
    }


def init_combat(attacker_ships: list, defender_ships: list) -> dict:
    units = []
    pos_a, pos_b = 5, 25
    for ship in attacker_ships:
        cnt = ship.get("count", 1)
        for _ in range(cnt):
            units.append(_make_unit(ship, "attacker", pos_a))
            pos_a += 1
    for ship in defender_ships:
        cnt = ship.get("count", 1)
        for _ in range(cnt):
            units.append(_make_unit(ship, "defender", pos_b))
            pos_b -= 1

    return {
        "round": 1,
        "max_rounds": 30,
        "units": units,
        "log": [],
        "winner": None,
    }


def _alive(state: dict, owner: str) -> list:
    return [u for u in state["units"] if u["alive"] and u["owner"] == owner]


def _to_hit(attacker: dict, target: dict) -> int:
    diff = attacker["attack"] - target["defense"]
    return max(5, min(95, 50 + diff))


def _apply_damage(target: dict, dmg: int, log: list) -> None:
    if dmg <= 0:
        return
    if target["shields"] > 0:
        absorbed = min(target["shields"], dmg)
        target["shields"] -= absorbed
        dmg -= absorbed
        log.append(f"{target['type']} shields absorb {absorbed} ({target['shields']} left)")
    if dmg > 0 and target["armor"] > 0:
        absorbed = min(target["armor"], dmg)
        target["armor"] -= absorbed
        dmg -= absorbed
        log.append(f"{target['type']} armor absorbs {absorbed}")
    if dmg > 0:
        target["hp"] -= dmg
        log.append(f"{target['type']} takes {dmg} hull damage ({target['hp']} HP)")
        if target["hp"] <= 0:
            target["alive"] = False
            log.append(f"{target['type']} destroyed.")


def step_action(state: dict, unit_uid: str, action: dict) -> dict:
    unit = next((u for u in state["units"] if u["uid"] == unit_uid), None)
    if not unit or not unit["alive"]:
        return {"status": "skip"}

    if action.get("type") == "move":
        target_pos = max(0, min(30, action.get("position", unit["position"])))
        diff = abs(target_pos - unit["position"])
        if diff > unit["speed"]:
            return {"status": "rejected", "reason": "out of range"}
        unit["position"] = target_pos
        state["log"].append(f"{unit['type']} moves to {target_pos}")
        return {"status": "ok"}

    if action.get("type") == "fire":
        target_id = action.get("target_uid")
        target = next((u for u in state["units"] if u["uid"] == target_id and u["alive"]), None)
        if not target:
            return {"status": "rejected", "reason": "no target"}
        chance = _to_hit(unit, target)
        if random.randint(1, 100) > chance:
            state["log"].append(f"{unit['type']} misses {target['type']} ({chance}%)")
            return {"status": "miss"}
        dmg = random.randint(max(1, unit["attack"] // 4), unit["attack"])
        _apply_damage(target, dmg, state["log"])
        return {"status": "hit", "damage": dmg}

    if action.get("type") == "retreat":
        unit["alive"] = False
        state["log"].append(f"{unit['type']} retreats")
        return {"status": "ok"}

    return {"status": "wait"}


def auto_resolve(state: dict, max_rounds: int = None) -> dict:
    """Resolucion deterministica round-robin. Cada nave dispara al objetivo mas debil."""
    rounds = max_rounds or state.get("max_rounds", 30)
    for _ in range(rounds):
        if not _alive(state, "attacker") or not _alive(state, "defender"):
            break
        ordered = sorted([u for u in state["units"] if u["alive"]], key=lambda u: -u["speed"])
        for unit in ordered:
            if not unit["alive"]:
                continue
            opponents = _alive(state, "defender" if unit["owner"] == "attacker" else "attacker")
            if not opponents:
                continue
            target = min(opponents, key=lambda u: u["hp"] + u["shields"] + u["armor"])
            step_action(state, unit["uid"], {"type": "fire", "target_uid": target["uid"]})
        state["round"] += 1

    if _alive(state, "attacker") and not _alive(state, "defender"):
        state["winner"] = "attacker"
    elif _alive(state, "defender") and not _alive(state, "attacker"):
        state["winner"] = "defender"
    else:
        state["winner"] = "draw"
    return state
