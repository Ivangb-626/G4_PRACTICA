import json
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parents[1] / "data"

with (DATA_DIR / "buildings.json").open("r", encoding="utf-8") as f:
    BUILDINGS = {building["id"]: building for building in json.load(f)}

with (DATA_DIR / "ships.json").open("r", encoding="utf-8") as f:
    SHIPS = {ship["type"]: ship for ship in json.load(f)}


def get_empire(game_state, owner_id):
    if owner_id == "player":
        return game_state["player"]
    return next((ai for ai in game_state.get("ai_players", []) if ai["id"] == owner_id), None)


def has_technology(player_technologies, tech_id):
    return any(
        tech["tech_id"] == tech_id and tech.get("status") != "discarded"
        for tech in player_technologies.get("researched", [])
    )


def get_available_buildings(game_state, colony):
    owner_id = colony.get("owner", "player")
    empire = get_empire(game_state, owner_id)
    if not empire:
        return []

    available = []
    built_ids = {building["id"] for building in colony.get("buildings", [])}
    queued_ids = {
        item["id"]
        for item in colony.get("build_queue", [])
        if item.get("type") == "building"
    }

    for building_id, building in BUILDINGS.items():
        if building_id in built_ids or building_id in queued_ids:
            continue

        tech_reqs = building.get("prerequisites", {}).get("tech", [])
        if tech_reqs and not all(has_technology(empire["technologies"], tech) for tech in tech_reqs):
            continue

        building_reqs = building.get("prerequisites", {}).get("buildings", [])
        if building_reqs and not all(req in built_ids for req in building_reqs):
            continue

        available.append(
            {
                "id": building_id,
                "name": building["name"],
                "cost": building["cost"],
                "maintenance": building["maintenance"],
                "description": building.get("description", ""),
                "effects": building.get("effects", {}),
            }
        )

    return available


def get_available_ships(game_state, colony):
    has_shipyard = any(
        building["id"] in ["spaceport", "star_base"] for building in colony.get("buildings", [])
    )
    available = []

    for ship_type, ship in SHIPS.items():
        if not has_shipyard and ship_type not in ["colony_ship", "transport", "frigate"]:
            continue

        available.append(
            {
                "type": ship_type,
                "name": ship.get("name", ship_type),
                "cost": ship.get("cost", 50),
                "command_points": ship.get("command_points", 1),
                "description": (
                    f"Speed: {ship.get('speed', 2)}, "
                    f"Attack: {ship.get('attack', 0)}, "
                    f"Defense: {ship.get('defense', 0)}"
                ),
            }
        )

    return available


def add_to_build_queue(colony, item_type, item_id, cost):
    if len(colony.get("build_queue", [])) >= 7:
        raise ValueError("Build queue is full (max 7 items)")

    queue_item = {
        "type": item_type,
        "id": item_id,
        "progress": 0,
        "cost": cost,
    }
    colony.setdefault("build_queue", []).append(queue_item)
    return queue_item


def cancel_build_queue_item(colony, index):
    if index < 0 or index >= len(colony.get("build_queue", [])):
        raise ValueError("Invalid queue index")
    colony["build_queue"].pop(index)


def reorder_build_queue(colony, from_index, to_index):
    queue = colony.get("build_queue", [])
    if from_index < 0 or from_index >= len(queue) or to_index < 0 or to_index >= len(queue):
        raise ValueError("Invalid queue index")

    item = queue.pop(from_index)
    queue.insert(to_index, item)


def _get_shipyard_bonus(colony):
    bonus = 0
    for building in colony.get("buildings", []):
        bonus += BUILDINGS.get(building["id"], {}).get("effects", {}).get("ship_production_bonus", 0)
    return bonus


def _get_or_create_fleet(game_state, colony):
    owner_id = colony.get("owner", "player")
    empire = get_empire(game_state, owner_id)
    if not empire:
        return None

    fleet = next(
        (
            item
            for item in empire.get("fleets", [])
            if item.get("star_system_id") == colony["star_system_id"] and item.get("destination") is None
        ),
        None,
    )
    if fleet:
        return fleet

    fleet = {
        "id": f"fleet_{owner_id}_{colony['star_system_id']}_{len(empire.get('fleets', []))}",
        "name": f"Defense Fleet {colony['name']}",
        "owner": owner_id,
        "star_system_id": colony["star_system_id"],
        "ships": [],
        "destination": None,
        "eta_turns": None,
        "command_points_used": 0,
    }
    empire.setdefault("fleets", []).append(fleet)
    return fleet


def _add_ship_to_fleet(game_state, colony, ship_type):
    fleet = _get_or_create_fleet(game_state, colony)
    if not fleet:
        return None

    ship_group = next((ship for ship in fleet["ships"] if ship["type"] == ship_type), None)
    if ship_group:
        ship_group["count"] += 1
    else:
        fleet["ships"].append({"type": ship_type, "count": 1})

    fleet["command_points_used"] = sum(
        SHIPS.get(ship["type"], {}).get("command_points", 0) * ship.get("count", 0)
        for ship in fleet["ships"]
    )
    return fleet


def process_colony_construction(game_state, colony):
    events = []
    queue = colony.get("build_queue", [])
    if not queue:
        return events

    current_item = queue[0]
    industry = colony.get("industry_output", 0)
    if current_item["type"] == "ship":
        industry *= 1 + (_get_shipyard_bonus(colony) / 100)

    current_item["progress"] += industry

    while queue and queue[0]["progress"] >= queue[0]["cost"]:
        current_item = queue[0]
        overflow = current_item["progress"] - current_item["cost"]

        if current_item["type"] == "building":
            building = BUILDINGS.get(current_item["id"])
            if building:
                colony.setdefault("buildings", []).append(
                    {
                        "id": current_item["id"],
                        "name": building["name"],
                        "completed": True,
                    }
                )
                events.append(
                    {
                        "type": "building_complete",
                        "colony_id": colony["id"],
                        "building_id": current_item["id"],
                        "building_name": building["name"],
                    }
                )
        elif current_item["type"] == "ship":
            fleet = _add_ship_to_fleet(game_state, colony, current_item["id"])
            events.append(
                {
                    "type": "ship_complete",
                    "colony_id": colony["id"],
                    "ship_type": current_item["id"],
                    "fleet_id": fleet["id"] if fleet else None,
                }
            )

        queue.pop(0)
        if queue:
            queue[0]["progress"] += max(0, overflow)

    return events


def calculate_colony_production(game_state, colony):
    from app.services.game_service import MINERAL_MOD, PLANET_TYPES, find_system

    system = find_system(game_state, colony["star_system_id"])
    if not system:
        return

    planet = system["planets"][colony["planet_index"]]
    owner_id = colony.get("owner", "player")
    empire = get_empire(game_state, owner_id)
    if not empire:
        return

    race = empire["race"]
    food_mod = PLANET_TYPES.get(planet["type"], {}).get("food_mod", 0)
    mineral_mod = MINERAL_MOD.get(planet["minerals"], 1.0)

    farmers = int(colony["population"].get("farmers", 1))
    workers = int(colony["population"].get("workers", 0))
    scientists = int(colony["population"].get("scientists", 0))
    total = int(colony["population"].get("total", 1))

    building_food_bonus = sum(
        BUILDINGS.get(building["id"], {}).get("effects", {}).get("food_bonus", 0)
        for building in colony.get("buildings", [])
    )
    building_prod_bonus = sum(
        BUILDINGS.get(building["id"], {}).get("effects", {}).get("production_bonus", 0)
        for building in colony.get("buildings", [])
    )
    building_research_bonus = sum(
        BUILDINGS.get(building["id"], {}).get("effects", {}).get("research_bonus", 0)
        for building in colony.get("buildings", [])
    )
    building_bc_bonus = sum(
        BUILDINGS.get(building["id"], {}).get("effects", {}).get("bc_bonus", 0)
        for building in colony.get("buildings", [])
    )
    building_ground_defense = sum(
        BUILDINGS.get(building["id"], {}).get("effects", {}).get("ground_defense", 0)
        for building in colony.get("buildings", [])
    )
    building_orbital_defense = sum(
        BUILDINGS.get(building["id"], {}).get("effects", {}).get("orbital_defense", 0)
        for building in colony.get("buildings", [])
    )

    food_output = max(0, farmers * (1 + food_mod + race["traits"].get("food_bonus", 0)) + building_food_bonus)
    food_consumption = total
    food_surplus = food_output - food_consumption

    industry_output = max(
        0,
        (workers * 2 + race["traits"].get("industry_bonus", 0) * workers + building_prod_bonus) * mineral_mod,
    )
    research_output = max(
        0,
        scientists * 2 + race["traits"].get("research_bonus", 0) + building_research_bonus,
    )
    bc_output = max(
        0,
        race["traits"].get("trade_bonus", 0) * total + building_bc_bonus,
    )
    if not colony.get("build_queue"):
        bc_output += round(industry_output * 0.5, 2)

    colony["food_output"] = food_output
    colony["food_consumption"] = food_consumption
    colony["food_surplus"] = food_surplus
    colony["industry_output"] = round(industry_output, 2)
    colony["research_output"] = round(research_output, 2)
    colony["bc_output"] = round(bc_output, 2)
    colony["ground_defense"] = building_ground_defense
    colony["orbital_defense"] = building_orbital_defense
