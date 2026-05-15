"""
ground_combat.py — Invasiones, Mind Control, asimilacion y rebeliones.

Reusa resolve_ground_combat() de combat_service.py y anade:
- prepare_invasion / bombard / mind_control
- per-turn assimilation tick + rebellion roll
"""
from __future__ import annotations

import random


def _find_empire(game_state: dict, owner_id: str):
    if owner_id == "player":
        return game_state.get("player")
    return next((ai for ai in game_state.get("ai_players", []) if ai["id"] == owner_id), None)


def _empire_for_colony(game_state: dict, colony_id: str):
    for emp in [game_state.get("player"), *game_state.get("ai_players", [])]:
        if not emp:
            continue
        for c in emp.get("colonies", []):
            if c.get("id") == colony_id:
                return emp, c
    return None, None


def bombard(game_state: dict, fleet, colony, intensity: int = 1) -> dict:
    """Reduce marines, poblacion y edificios. Las razas Telepaticas pueden saltar esto."""
    pop_loss = max(0, intensity)
    ground_loss = max(0, intensity * 5)
    bld_chance = min(0.6, 0.15 * intensity)

    pop = colony.get("population", {})
    if isinstance(pop, dict):
        pop["total"] = max(1, pop.get("total", 1) - pop_loss)
    colony["ground_defense"] = max(0, colony.get("ground_defense", 0) - ground_loss)
    if colony.get("buildings") and random.random() < bld_chance:
        idx = random.randrange(len(colony["buildings"]))
        removed = colony["buildings"].pop(idx)
        return {"type": "bombard", "pop_lost": pop_loss, "removed_building": removed}
    return {"type": "bombard", "pop_lost": pop_loss}


def mind_control(game_state: dict, attacker_id: str, colony_id: str) -> dict:
    """Telepatic mind control. Cambia el owner sin combate si tiene exito."""
    attacker = _find_empire(game_state, attacker_id)
    if not attacker:
        return {"success": False, "reason": "Attacker not found"}
    flags = attacker.get("race", {}).get("traits", {}).get("flags", {})
    if not flags.get("telepathic"):
        return {"success": False, "reason": "Race is not telepathic"}

    target_emp, colony = _empire_for_colony(game_state, colony_id)
    if not target_emp or not colony:
        return {"success": False, "reason": "Colony not found"}

    # Mind shield protection
    leader_id = target_emp.get("leader_assignments", {}).get(colony_id)
    if leader_id:
        leader = next((l for l in target_emp.get("hired_leaders", []) if l["id"] == leader_id), None)
        if leader and any(s.get("id") == "mind_shield" for s in leader.get("skills", [])):
            return {"success": False, "reason": "Colony shielded by Mind Shield leader"}

    pop_total = colony.get("population", {}).get("total", 1) if isinstance(colony.get("population"), dict) else 1
    chance = max(10, 80 - pop_total * 3)
    if random.randint(1, 100) > chance:
        colony["morale"] = -25
        return {"success": False, "reason": "Mind control resisted"}

    # Transfer
    target_emp["colonies"] = [c for c in target_emp.get("colonies", []) if c.get("id") != colony_id]
    colony["owner"] = attacker_id
    colony["morale"] = -25
    colony["assimilation_progress"] = 0
    colony["original_owner"] = target_emp.get("id")
    attacker.setdefault("colonies", []).append(colony)
    return {"success": True, "colony_id": colony_id}


def post_conquest_setup(colony: dict, new_owner: str, original_owner: str) -> None:
    colony["owner"] = new_owner
    colony["morale"] = -50
    colony["assimilation_progress"] = 0
    colony["original_owner"] = original_owner


def process_assimilation(game_state: dict) -> list:
    """Tick por turno: avanza asimilacion y comprueba rebeliones."""
    events = []
    for emp in [game_state.get("player"), *game_state.get("ai_players", [])]:
        if not emp:
            continue
        amc_buildings = []  # set of colony_ids that have alien_management_center
        for c in emp.get("colonies", []):
            if "alien_management_center" in [b if isinstance(b, str) else b.get("id") for b in c.get("buildings", [])]:
                amc_buildings.append(c.get("id"))
        for c in emp.get("colonies", []):
            if c.get("assimilation_progress") is None:
                continue
            if c["assimilation_progress"] >= 100:
                continue
            inc = 10 if c.get("id") in amc_buildings else 5
            c["assimilation_progress"] = min(100, c["assimilation_progress"] + inc)
            # Slowly recover morale
            try:
                if isinstance(c.get("morale"), (int, float)):
                    c["morale"] = min(0, c["morale"] + 5)
            except Exception:
                pass
            # Rebellion check
            rebel_chance = max(0, 100 - c["assimilation_progress"]) * 0.005
            if random.random() < rebel_chance:
                original = c.get("original_owner")
                if original and original != emp.get("id"):
                    target_emp = _find_empire(game_state, original)
                    if target_emp:
                        emp["colonies"] = [k for k in emp["colonies"] if k.get("id") != c.get("id")]
                        c["owner"] = original
                        c["assimilation_progress"] = 100
                        c["morale"] = "stable"
                        target_emp.setdefault("colonies", []).append(c)
                        events.append({"type": "colony_rebelled", "colony_id": c.get("id"), "to": original, "from": emp.get("id")})
    return events


def assault_colony(game_state: dict, attacker_id: str, fleet_id: str, colony_id: str, exterminate: bool = False) -> dict:
    from app.services.combat_service import resolve_ground_combat
    from app.services.diplomacy_service import _adjust_relation
    attacker = _find_empire(game_state, attacker_id)
    if not attacker:
        return {"success": False, "reason": "Attacker not found"}
    fleet = next((f for f in attacker.get("fleets", []) if f["id"] == fleet_id), None)
    if not fleet:
        return {"success": False, "reason": "Fleet not found"}
    target_emp, colony = _empire_for_colony(game_state, colony_id)
    if not target_emp or not colony:
        return {"success": False, "reason": "Colony not found"}
    if target_emp.get("id") == attacker_id or (attacker_id == "player" and target_emp == attacker):
        return {"success": False, "reason": "Cannot assault own colony"}

    transports = next((s for s in fleet.get("ships", []) if s["type"] == "transport" and s.get("count", 0) > 0), None)
    if not transports:
        return {"success": False, "reason": "Fleet has no transports"}

    attacker_bonus = attacker.get("race", {}).get("traits", {}).get("ground_combat_bonus", 0)
    defender_bonus = target_emp.get("race", {}).get("traits", {}).get("ground_combat_bonus", 0)
    marines = transports["count"] * 6
    result = resolve_ground_combat(marines, attacker_bonus, colony, defender_bonus)

    target_owner_id = target_emp.get("id") or ("player" if target_emp == game_state.get("player") else None)
    diplomacy_delta = 0
    captured_tech = None

    if result["winner"] == "attacker":
        target_emp["colonies"] = [c for c in target_emp.get("colonies", []) if c.get("id") != colony_id]
        if exterminate:
            colony["population"] = {"total": 0, "max": colony.get("population", {}).get("max", 1), "farmers": 0, "workers": 0, "scientists": 0}
        else:
            post_conquest_setup(colony, attacker_id, target_emp.get("id"))
        attacker.setdefault("colonies", []).append(colony)
        # Update the planet's ownership in the galaxy so the system view
        # and any map rendering treats the planet as belonging to the attacker.
        system_id = colony.get("star_system_id")
        planet_index = colony.get("planet_index")
        for system in game_state.get("galaxy", {}).get("star_systems", []):
            if system.get("id") != system_id:
                continue
            planets = system.get("planets", [])
            if isinstance(planet_index, int) and 0 <= planet_index < len(planets):
                planets[planet_index]["colonized_by"] = attacker_id
            # Ensure the attacker has visibility on the newly-captured system.
            fog = game_state.get("galaxy", {}).setdefault("fog_of_war", {})
            explored = fog.setdefault(attacker_id, [])
            if system_id and system_id not in explored:
                explored.append(system_id)
            if attacker_id not in system.setdefault("explored_by", []):
                system["explored_by"].append(attacker_id)
            break
        # Tech capture chance
        if random.random() < 0.30:
            target_techs = [t.get("tech_id") for t in target_emp.get("technologies", {}).get("researched", []) if t.get("status") != "discarded"]
            attacker_techs = {t.get("tech_id") for t in attacker.get("technologies", {}).get("researched", []) if t.get("status") != "discarded"}
            opt = [t for t in target_techs if t not in attacker_techs]
            if opt:
                captured_tech = random.choice(opt)
                attacker["technologies"]["researched"].append({"tech_id": captured_tech, "field": "", "level": 1, "status": "researched"})
        diplomacy_delta = -40 if exterminate else -30
        captured = True
    else:
        diplomacy_delta = -15
        captured = False

    transports["count"] = 0
    fleet["ships"] = [s for s in fleet["ships"] if s.get("count", 0) > 0]

    if target_owner_id and target_owner_id != attacker_id:
        try:
            _adjust_relation(game_state, attacker_id, target_owner_id, diplomacy_delta)
            game_state.setdefault("diplomacy", {}).setdefault("history", []).append({
                "turn": game_state.get("turn", 1),
                "type": "colony_assaulted",
                "by": attacker_id,
                "against": target_owner_id,
                "colony_id": colony_id,
                "captured": captured,
                "delta": diplomacy_delta,
            })
        except Exception:
            pass

    return {
        "success": True,
        "colony_captured": captured,
        "result": result,
        "captured_tech": captured_tech if captured else None,
        "diplomacy_delta": diplomacy_delta,
        "target_owner": target_owner_id,
    }
