import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

with (DATA_DIR / "buildings.json").open("r", encoding="utf-8") as f:
    BUILDINGS = {item["id"]: item for item in json.load(f)}

with (DATA_DIR / "ships.json").open("r", encoding="utf-8") as f:
    SHIPS = {item["type"]: item for item in json.load(f)}


def _normalize_build_args(a, b, d):
    if a in ("building", "ship"):
        item_type, item_id = a, b
    else:
        item_id, item_type = a, b
    if isinstance(d, dict):
        catalog = BUILDINGS if item_type == "building" else SHIPS
        cost = catalog.get(item_id, {}).get("cost", 0)
    else:
        cost = d or 0
    return item_type, item_id, cost


def add_to_build_queue(colony, arg_a, arg_b, arg_c):
    item_type, item_id, cost = _normalize_build_args(arg_a, arg_b, arg_c)
    catalog = BUILDINGS if item_type == "building" else SHIPS
    if item_id not in catalog:
        return False, f"Unknown {item_type}: {item_id}"
    queue = colony.setdefault("build_queue", [])
    queue.append({
        "item_type": item_type,
        "item_id": item_id,
        "name": catalog[item_id].get("name", item_id),
        "cost": cost,
        "progress": 0,
    })
    return True, None


def _resolve_colony_player(arg_a, arg_b, arg_c=None):
    # Some callers pass (colony, player, game_state); others (game_state, colony).
    if isinstance(arg_a, dict) and ("buildings" in arg_a or "population" in arg_a):
        return arg_a, arg_b, arg_c
    return arg_b, None, arg_a


def calculate_colony_production(arg_a, arg_b, arg_c=None):
    colony, _player, _game_state = _resolve_colony_player(arg_a, arg_b, arg_c)
    if colony is None:
        return {"food": 0, "industry": 0, "research": 0, "bc": 0, "production": 0}

    workers = colony.get("workers", 0)
    farmers = colony.get("farmers", 0)
    scientists = colony.get("scientists", 0)

    food = farmers * 2
    industry = workers * 1
    research = scientists * 1
    bc = workers // 2

    bonuses = {"production_bonus": 0, "research_bonus": 0, "food_bonus": 0, "bc_bonus": 0}
    for built in colony.get("buildings", []):
        record = BUILDINGS.get(built) if isinstance(built, str) else BUILDINGS.get(built.get("id"))
        if not record:
            continue
        for k in bonuses:
            bonuses[k] += record.get("effects", {}).get(k, 0)

    industry += bonuses["production_bonus"]
    research += bonuses["research_bonus"]
    food += bonuses["food_bonus"]
    bc += bonuses["bc_bonus"]

    colony["food_output"] = food
    colony["industry_output"] = industry
    colony["research_output"] = research
    colony["bc_output"] = bc
    colony["food_surplus"] = food - colony.get("population", 0)

    return {"food": food, "industry": industry, "research": research, "bc": bc, "production": industry}


def process_colony_construction(arg_a, arg_b, arg_c=None, arg_d=None):
    colony, _player, _game_state = _resolve_colony_player(arg_a, arg_b, arg_c)
    if colony is None:
        return []

    production = arg_d if arg_d is not None else colony.get("industry_output", 0)
    queue = colony.get("build_queue", [])
    events = []

    if not queue:
        return events

    head = queue[0]
    head["progress"] = head.get("progress", 0) + production
    if head["progress"] >= head.get("cost", 0):
        completed = queue.pop(0)
        if completed["item_type"] == "building":
            colony.setdefault("buildings", []).append(completed["item_id"])
        events.append({"type": "construction_complete", "colony_id": colony.get("id"), "item": completed})

    return events


def get_available_buildings(game_state, colony):
    built = set()
    for entry in colony.get("buildings", []):
        built.add(entry if isinstance(entry, str) else entry.get("id"))
    player_techs = set(game_state.get("player", {}).get("technologies", []))

    out = []
    for building in BUILDINGS.values():
        if building["id"] in built:
            continue
        prereqs = building.get("prerequisites", {})
        if any(t not in player_techs for t in prereqs.get("tech", [])):
            continue
        if any(b not in built for b in prereqs.get("buildings", [])):
            continue
        out.append(building)
    return out


def get_available_ships(game_state, colony):
    return list(SHIPS.values())


def has_technology(player, tech_id):
    return tech_id in player.get("technologies", [])
