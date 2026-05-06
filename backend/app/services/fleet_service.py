"""
fleet_service.py — Helpers de flota (split, merge, disband).

Mantiene compatibilidad con game_service que ya gestiona move/colonize.
"""
from __future__ import annotations


def split_fleet(empire: dict, fleet_id: str, ships_to_split: list) -> dict:
    """Mueve ships_to_split a una nueva flota en el mismo sistema."""
    fleet = next((f for f in empire.get("fleets", []) if f["id"] == fleet_id), None)
    if not fleet:
        return {"success": False, "reason": "Fleet not found"}
    new_ships = []
    for sp in ships_to_split:
        sid, count = sp.get("type"), sp.get("count", 0)
        existing = next((s for s in fleet["ships"] if s["type"] == sid), None)
        if not existing or existing.get("count", 0) < count:
            return {"success": False, "reason": f"Not enough {sid}"}
        existing["count"] -= count
        new_ships.append({"type": sid, "count": count})
    fleet["ships"] = [s for s in fleet["ships"] if s.get("count", 0) > 0]

    new_fleet = {
        "id": f"{fleet_id}_split_{len(empire['fleets'])}",
        "name": f"{fleet.get('name', 'Fleet')} (split)",
        "owner": fleet["owner"],
        "star_system_id": fleet["star_system_id"],
        "ships": new_ships,
        "destination": None,
        "eta_turns": None,
        "command_points_used": 0,
    }
    empire["fleets"].append(new_fleet)
    return {"success": True, "fleet": new_fleet}


def merge_fleets(empire: dict, fleet_a_id: str, fleet_b_id: str) -> dict:
    a = next((f for f in empire.get("fleets", []) if f["id"] == fleet_a_id), None)
    b = next((f for f in empire.get("fleets", []) if f["id"] == fleet_b_id), None)
    if not a or not b:
        return {"success": False, "reason": "Fleet not found"}
    if a["star_system_id"] != b["star_system_id"]:
        return {"success": False, "reason": "Fleets must be in the same system"}
    for ship in b["ships"]:
        existing = next((s for s in a["ships"] if s["type"] == ship["type"]), None)
        if existing:
            existing["count"] += ship["count"]
        else:
            a["ships"].append(ship)
    empire["fleets"] = [f for f in empire["fleets"] if f["id"] != fleet_b_id]
    return {"success": True, "fleet": a}


def disband_fleet(empire: dict, fleet_id: str) -> dict:
    before = len(empire.get("fleets", []))
    empire["fleets"] = [f for f in empire.get("fleets", []) if f["id"] != fleet_id]
    return {"success": before > len(empire["fleets"])}
