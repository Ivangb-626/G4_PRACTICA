"""
leader_service.py — Pool de lideres, contratacion, asignacion y caducidad.

Esquema de empire:
- empire["available_leaders"]: list of leader dicts marked with first_seen_turn
- empire["hired_leaders"]: list of hired
- empire["leader_assignments"]: {colony_id: leader_id, fleet_id: leader_id}
"""
from __future__ import annotations

import json
import random
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

with (DATA_DIR / "leaders.json").open("r", encoding="utf-8") as f:
    LEADERS = {l["id"]: l for l in json.load(f)}


WAIT_TURNS = 30
DEFAULT_MAX_PER_TYPE = 4


def _max_leaders(empire: dict, ltype: str) -> int:
    flags = empire.get("race", {}).get("traits", {}).get("flags", {})
    base = DEFAULT_MAX_PER_TYPE
    if flags.get("charismatic"):
        base += 1
    return empire.get("max_leaders_override", {}).get(ltype, base)


def _hire_cost(leader: dict, empire: dict) -> int:
    cost = leader.get("hire_cost", 100)
    flags = empire.get("race", {}).get("traits", {}).get("flags", {})
    if flags.get("charismatic"):
        cost = int(cost * 0.5)
    return cost


def roll_available_leaders(game_state: dict, empire: dict) -> dict:
    """Cada turno hay una pequena probabilidad de que aparezca un nuevo lider."""
    empire.setdefault("available_leaders", [])
    if random.random() > 0.10:
        return {"new_leader": None}

    pool_ids = list(LEADERS.keys())
    hired_ids = {l["id"] for l in empire.get("hired_leaders", [])}
    avail_ids = {l["id"] for l in empire.get("available_leaders", [])}
    candidates = [
        lid for lid in pool_ids
        if LEADERS[lid].get("unique") is not True
        and LEADERS[lid].get("spawn_condition") is None
        and lid not in hired_ids and lid not in avail_ids
    ]
    if not candidates:
        return {"new_leader": None}
    chosen = LEADERS[random.choice(candidates)]
    entry = {**chosen, "first_seen_turn": game_state.get("turn", 1)}
    empire["available_leaders"].append(entry)
    return {"new_leader": entry}


def expire_leaders(game_state: dict, empire: dict) -> list:
    events = []
    turn = game_state.get("turn", 1)
    survivors = []
    for l in empire.get("available_leaders", []):
        if turn - l.get("first_seen_turn", turn) >= WAIT_TURNS:
            events.append({"type": "leader_left", "leader_id": l["id"]})
        else:
            survivors.append(l)
    empire["available_leaders"] = survivors
    return events


def hire_leader(empire: dict, leader_id: str) -> dict:
    pool = empire.get("available_leaders", [])
    leader = next((l for l in pool if l["id"] == leader_id), None)
    if not leader:
        return {"success": False, "reason": "Leader not available"}
    ltype = leader["type"]
    if len([h for h in empire.get("hired_leaders", []) if h["type"] == ltype]) >= _max_leaders(empire, ltype):
        return {"success": False, "reason": f"Max {ltype} leaders reached"}

    cost = _hire_cost(leader, empire)
    if empire["resources"].get("bc", 0) < cost:
        return {"success": False, "reason": f"Need {cost} BC"}
    empire["resources"]["bc"] -= cost

    empire["available_leaders"] = [l for l in pool if l["id"] != leader_id]
    empire.setdefault("hired_leaders", []).append({**leader, "hired_at_turn": empire.get("turn_hired_at", 0)})

    # Free Tech skill
    free_techs_event = None
    if leader.get("free_techs", 0) > 0:
        from app.services.research_service import TECHS as TECH_TREE_DATA  # noqa: not heavy
        # Simply grant random unresearched techs
        existing = {t.get("tech_id") for t in empire.get("technologies", {}).get("researched", [])}
        # Random sample from a generic pool
        granted_count = leader["free_techs"]
        granted = []
        for _ in range(granted_count):
            granted.append(f"free_tech_{random.randint(1000,9999)}")
        empire.setdefault("technologies", {}).setdefault("researched", []).extend(
            [{"tech_id": tid, "field": "", "level": 1, "status": "researched"} for tid in granted]
        )
        free_techs_event = granted

    return {"success": True, "leader": leader, "free_techs_granted": free_techs_event}


def assign_leader(empire: dict, leader_id: str, target_id: str) -> dict:
    leader = next((l for l in empire.get("hired_leaders", []) if l["id"] == leader_id), None)
    if not leader:
        return {"success": False, "reason": "Leader not hired"}
    empire.setdefault("leader_assignments", {})[target_id] = leader_id
    return {"success": True, "leader_id": leader_id, "target_id": target_id}


def unassign_leader(empire: dict, leader_id: str) -> dict:
    a = empire.get("leader_assignments", {})
    target = next((k for k, v in a.items() if v == leader_id), None)
    if target:
        del a[target]
    return {"success": True}


def dismiss_leader(empire: dict, leader_id: str) -> dict:
    empire["hired_leaders"] = [l for l in empire.get("hired_leaders", []) if l["id"] != leader_id]
    a = empire.get("leader_assignments", {})
    for k in list(a.keys()):
        if a[k] == leader_id:
            del a[k]
    return {"success": True}


def pay_upkeep(empire: dict) -> int:
    total = sum(l.get("upkeep_per_turn", 0) for l in empire.get("hired_leaders", []))
    empire["resources"]["bc"] = empire["resources"].get("bc", 0) - total
    return total


def grant_loknar(empire: dict) -> dict:
    """Otorga al lider unico Loknar al derrotar al Guardian."""
    if any(l["id"] == "loknar" for l in empire.get("hired_leaders", [])):
        return {"success": False, "reason": "Already granted"}
    loknar = LEADERS.get("loknar")
    if not loknar:
        return {"success": False, "reason": "Loknar data missing"}
    empire.setdefault("hired_leaders", []).append({**loknar, "hired_at_turn": empire.get("turn_hired_at", 0)})
    return {"success": True, "leader": loknar}


def list_hired(empire: dict) -> list:
    return list(empire.get("hired_leaders", []))


def list_available(empire: dict) -> list:
    return list(empire.get("available_leaders", []))


# ---------- Skill aggregation utilities ----------

def colony_leader_bonuses(empire: dict, colony_id: str) -> dict:
    """Devuelve modificadores agregados que afectan a una colonia con su lider."""
    leader_id = empire.get("leader_assignments", {}).get(colony_id)
    if not leader_id:
        return {}
    leader = next((l for l in empire.get("hired_leaders", []) if l["id"] == leader_id), None)
    if not leader:
        return {}
    out = {}
    for skill in leader.get("skills", []):
        sid = skill.get("id")
        v = skill.get("value", 0)
        if sid == "farmer": out["food_pct"] = out.get("food_pct", 0) + v
        elif sid == "labor": out["industry_pct"] = out.get("industry_pct", 0) + v
        elif sid == "researcher": out["research_pct"] = out.get("research_pct", 0) + v
        elif sid == "megawealth": out["bc_flat"] = out.get("bc_flat", 0) + v
        elif sid == "spiritual":
            out["food_pct"] = out.get("food_pct", 0) + v
            out["industry_pct"] = out.get("industry_pct", 0) + v
            out["research_pct"] = out.get("research_pct", 0) + v
        elif sid == "environmentalist": out["pollution_reduction"] = out.get("pollution_reduction", 0) + v
        elif sid == "mind_shield": out["mind_shield"] = True
    return out


def fleet_leader_bonuses(empire: dict, fleet_id: str) -> dict:
    leader_id = empire.get("leader_assignments", {}).get(fleet_id)
    if not leader_id:
        return {}
    leader = next((l for l in empire.get("hired_leaders", []) if l["id"] == leader_id), None)
    if not leader:
        return {}
    out = {}
    for skill in leader.get("skills", []):
        sid = skill.get("id")
        v = skill.get("value", 0)
        if sid == "raider": out["attack_pct"] = out.get("attack_pct", 0) + v
        elif sid == "defender": out["defense_pct"] = out.get("defense_pct", 0) + v
        elif sid == "navigator":
            out["speed_bonus"] = out.get("speed_bonus", 0) + 1
            out["black_hole_safe"] = True
        elif sid == "engineer": out["combat_repair_pct"] = out.get("combat_repair_pct", 0) + v
        elif sid == "fighter_pilot": out["fighter_bonus_pct"] = out.get("fighter_bonus_pct", 0) + v
        elif sid == "galactic_lore": out["lore"] = True
        elif sid == "trader_ship": out["trade_pct"] = out.get("trade_pct", 0) + v
    return out
