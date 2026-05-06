"""
espionage_service.py — Reclutamiento de espias, operaciones y contrainteligencia.
"""
from __future__ import annotations

import json
import random
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

with (DATA_DIR / "governments.json").open("r", encoding="utf-8") as f:
    GOVERNMENTS = {item["id"]: item for item in json.load(f)}


SPY_BASE_COST = 75
SPY_BASE_UPKEEP = 2
MISSIONS = ("steal_tech", "sabotage", "incite_rebellion", "frame")


def _find_empire(game_state: dict, owner_id: str):
    if owner_id == "player":
        return game_state.get("player")
    return next((ai for ai in game_state.get("ai_players", []) if ai["id"] == owner_id), None)


def _empire_counter_intel(empire: dict) -> int:
    if not empire:
        return 0
    base = 0
    gov_id = empire.get("government") or empire.get("race", {}).get("government", "dictatorship")
    gov = GOVERNMENTS.get(gov_id) or {}
    base += gov.get("modifiers", {}).get("counter_espionage", 0)
    flags = empire.get("race", {}).get("traits", {}).get("flags", {})
    if flags.get("repulsive"):
        base += 5
    if flags.get("telepathic"):
        base += 10
    base += empire.get("race", {}).get("traits", {}).get("spy_bonus", 0) // 2
    spies = empire.get("spies", [])
    base += sum(5 + s.get("experience", 0) for s in spies if s.get("assignment") == "defense")
    for c in empire.get("colonies", []):
        for b in c.get("buildings", []):
            bid = b if isinstance(b, str) else b.get("id")
            if bid == "cyber_security_link":
                base += 10
    for l in empire.get("hired_leaders", []):
        for skill in l.get("skills", []):
            if skill.get("id") == "counter_spy":
                base += skill.get("value", 0)
    return base


def _empire_offensive_bonus(empire: dict) -> int:
    if not empire:
        return 0
    bonus = empire.get("race", {}).get("traits", {}).get("spy_bonus", 0)
    for l in empire.get("hired_leaders", []):
        for skill in l.get("skills", []):
            if skill.get("id") == "spy":
                bonus += skill.get("value", 0)
    return bonus


def recruit_spy(empire: dict) -> dict:
    spies = empire.setdefault("spies", [])
    cost = SPY_BASE_COST + len(spies) * 25
    if empire.get("resources", {}).get("bc", 0) < cost:
        return {"success": False, "reason": f"Need {cost} BC"}
    empire["resources"]["bc"] -= cost
    spy = {
        "id": f"spy_{random.randint(1000, 9999)}_{len(spies)}",
        "owner": empire.get("id", "player"),
        "assignment": "defense",
        "mission": None,
        "experience": 0,
        "cost_per_turn": SPY_BASE_UPKEEP,
    }
    spies.append(spy)
    return {"success": True, "spy": spy, "cost": cost}


def assign_spy(empire: dict, spy_id: str, target: str, mission: str) -> dict:
    spy = next((s for s in empire.get("spies", []) if s["id"] == spy_id), None)
    if not spy:
        return {"success": False, "reason": "Spy not found"}
    if mission != "defense" and mission not in MISSIONS:
        return {"success": False, "reason": f"Invalid mission. Use one of {MISSIONS} or 'defense'"}
    if mission == "defense":
        spy["assignment"] = "defense"
        spy["mission"] = None
    else:
        spy["assignment"] = target
        spy["mission"] = mission
    return {"success": True, "spy": spy}


def list_spies(empire: dict) -> list:
    return list(empire.get("spies", []))


def _execute_mission(game_state: dict, attacker_emp: dict, spy: dict) -> dict:
    target_id = spy.get("assignment")
    mission = spy.get("mission")
    target_emp = _find_empire(game_state, target_id)
    if not target_emp:
        return {"type": "spy_idle", "spy_id": spy["id"]}

    base = 30 + spy.get("experience", 0) * 5 + _empire_offensive_bonus(attacker_emp)
    counter = _empire_counter_intel(target_emp)
    chance = max(5, min(90, base - counter))

    if random.randint(1, 100) > chance:
        if random.random() < 0.4:
            attacker_emp["spies"] = [s for s in attacker_emp.get("spies", []) if s["id"] != spy["id"]]
            try:
                from app.services.diplomacy_service import _adjust_relation
                _adjust_relation(game_state, attacker_emp.get("id", "player"), target_id, -25)
            except Exception:
                pass
            return {"type": "spy_caught", "spy_id": spy["id"], "target": target_id, "owner": attacker_emp.get("id", "player")}
        return {"type": "spy_failed", "spy_id": spy["id"], "target": target_id}

    spy["experience"] = min(10, spy.get("experience", 0) + 1)

    if mission == "steal_tech":
        target_techs = [t.get("tech_id") for t in target_emp.get("technologies", {}).get("researched", []) if t.get("status") != "discarded"]
        attacker_techs = {t.get("tech_id") for t in attacker_emp.get("technologies", {}).get("researched", []) if t.get("status") != "discarded"}
        candidates = [t for t in target_techs if t and t not in attacker_techs]
        if not candidates:
            return {"type": "spy_no_tech", "spy_id": spy["id"]}
        stolen = random.choice(candidates)
        attacker_emp.setdefault("technologies", {}).setdefault("researched", []).append(
            {"tech_id": stolen, "field": "", "level": 1, "status": "researched"}
        )
        return {"type": "tech_stolen", "spy_id": spy["id"], "tech_id": stolen, "from": target_id}

    if mission == "sabotage":
        candidates = [c for c in target_emp.get("colonies", []) if any(b for b in c.get("buildings", []))]
        if not candidates:
            return {"type": "spy_no_target", "spy_id": spy["id"]}
        colony = random.choice(candidates)
        building = random.choice(colony["buildings"])
        colony["buildings"] = [b for b in colony["buildings"] if b != building]
        return {"type": "sabotage", "spy_id": spy["id"], "colony_id": colony.get("id"), "removed": building}

    if mission == "incite_rebellion":
        candidates = [c for c in target_emp.get("colonies", []) if c.get("assimilation_progress") is not None and c["assimilation_progress"] < 100]
        if not candidates:
            return {"type": "spy_no_target", "spy_id": spy["id"]}
        colony = random.choice(candidates)
        original = colony.get("original_owner") or attacker_emp.get("id", "player")
        target_emp["colonies"] = [c for c in target_emp["colonies"] if c.get("id") != colony.get("id")]
        original_emp = _find_empire(game_state, original) or attacker_emp
        colony["owner"] = original
        colony["morale"] = "stable"
        colony["assimilation_progress"] = 100
        original_emp.setdefault("colonies", []).append(colony)
        return {"type": "rebellion_incited", "spy_id": spy["id"], "colony_id": colony.get("id"), "to": original}

    if mission == "frame":
        third = next((ai["id"] for ai in game_state.get("ai_players", []) if ai["id"] != target_id and ai["id"] != attacker_emp.get("id")), None)
        if not third:
            return {"type": "spy_no_target", "spy_id": spy["id"]}
        try:
            from app.services.diplomacy_service import _adjust_relation
            _adjust_relation(game_state, target_id, third, -25)
        except Exception:
            pass
        return {"type": "frame_success", "spy_id": spy["id"], "target": target_id, "framed_against": third}

    return {"type": "spy_idle", "spy_id": spy["id"]}


def process_turn_espionage(game_state: dict) -> list:
    events = []
    factions = ["player", *(ai["id"] for ai in game_state.get("ai_players", []))]
    for owner_id in factions:
        emp = _find_empire(game_state, owner_id)
        if not emp:
            continue
        spies = emp.get("spies", [])
        for spy in list(spies):
            upkeep = spy.get("cost_per_turn", SPY_BASE_UPKEEP)
            emp["resources"]["bc"] = emp["resources"].get("bc", 0) - upkeep
            if spy.get("assignment") in (None, "defense"):
                continue
            if emp["resources"]["bc"] < 0:
                emp["spies"] = [s for s in emp["spies"] if s["id"] != spy["id"]]
                events.append({"type": "spy_disbanded", "spy_id": spy["id"], "owner": owner_id})
                continue
            ev = _execute_mission(game_state, emp, spy)
            if ev:
                events.append(ev)
    return events
