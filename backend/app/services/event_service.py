"""
event_service.py — Eventos aleatorios de imperio/galaxia.

Llamado al final de cada turno por turn_engine. Los eventos solo se disparan si
game_state["random_events_enabled"] es true (default true).
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


EVENTS = [
    "plague",
    "bountiful_harvest",
    "industrial_accident",
    "supernova",
    "archaeological_dig",
    "pirate_raid",
    "scientific_breakthrough",
    "leader_offer",
    "trade_boom",
]


def generate_random_events(game_state: dict) -> list:
    if not game_state.get("random_events_enabled", True):
        return []

    severity = _difficulty_record(game_state.get("difficulty")).get("events_severity_mult", 1.0)
    events = []

    if random.random() > 0.10 * severity:
        return events

    kind = random.choice(EVENTS)

    # Choose a random empire (often the player so it's noticed)
    pool = []
    for emp in [game_state.get("player"), *game_state.get("ai_players", [])]:
        if emp:
            pool.append(emp)
    if not pool:
        return events
    target_emp = random.choice(pool)

    if kind == "plague" and target_emp.get("colonies"):
        c = random.choice(target_emp["colonies"])
        if isinstance(c.get("population"), dict):
            c["population"]["total"] = max(1, c["population"]["total"] - 2)
        events.append({"type": "event_plague", "owner": target_emp.get("id", "player"), "colony_id": c.get("id")})

    elif kind == "bountiful_harvest" and target_emp.get("colonies"):
        c = random.choice(target_emp["colonies"])
        if isinstance(c.get("population"), dict):
            c["population"]["total"] = min(c["population"].get("max", c["population"]["total"] + 2), c["population"]["total"] + 2)
        events.append({"type": "event_bountiful_harvest", "owner": target_emp.get("id", "player"), "colony_id": c.get("id")})

    elif kind == "industrial_accident" and target_emp.get("colonies"):
        c = random.choice(target_emp["colonies"])
        if c.get("buildings"):
            removed = c["buildings"].pop(random.randrange(len(c["buildings"])))
            events.append({"type": "event_industrial_accident", "owner": target_emp.get("id", "player"), "colony_id": c.get("id"), "building": removed})

    elif kind == "supernova":
        systems = game_state["galaxy"].get("star_systems", [])
        # Avoid Orion/protected systems
        candidates = [s for s in systems if s.get("name") != "Orion"]
        if candidates:
            s = random.choice(candidates)
            for emp in [game_state.get("player"), *game_state.get("ai_players", [])]:
                if not emp:
                    continue
                emp["colonies"] = [c for c in emp.get("colonies", []) if c.get("star_system_id") != s["id"]]
            s["destroyed_by_supernova"] = True
            events.append({"type": "event_supernova", "system_id": s["id"]})

    elif kind == "archaeological_dig":
        target_emp.setdefault("technologies", {}).setdefault("researched", []).append(
            {"tech_id": f"artifact_{random.randint(1000,9999)}", "field": "", "level": 1, "status": "researched"}
        )
        events.append({"type": "event_archaeological_dig", "owner": target_emp.get("id", "player")})

    elif kind == "pirate_raid":
        loss = min(target_emp.get("resources", {}).get("bc", 0), random.randint(20, 80))
        target_emp["resources"]["bc"] = target_emp.get("resources", {}).get("bc", 0) - loss
        events.append({"type": "event_pirate_raid", "owner": target_emp.get("id", "player"), "bc_lost": loss})

    elif kind == "scientific_breakthrough":
        cur = target_emp.get("technologies", {}).get("current_research")
        if cur:
            cur["progress"] = cur.get("total_cost", 0)
        events.append({"type": "event_scientific_breakthrough", "owner": target_emp.get("id", "player")})

    elif kind == "leader_offer":
        try:
            from app.services.leader_service import roll_available_leaders
            res = roll_available_leaders(game_state, target_emp)
            if res.get("new_leader"):
                events.append({"type": "event_leader_offer", "owner": target_emp.get("id", "player"), "leader_id": res["new_leader"]["id"]})
        except Exception:
            pass

    elif kind == "trade_boom":
        bonus = random.randint(50, 150)
        target_emp["resources"]["bc"] = target_emp.get("resources", {}).get("bc", 0) + bonus
        events.append({"type": "event_trade_boom", "owner": target_emp.get("id", "player"), "bc_gained": bonus})

    return events
