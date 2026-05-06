"""
colony_service.py — Calculo de produccion, gestion de cola de construccion y disponibilidad
de edificios/naves. Aplica:
- modificadores de gobierno (governments.json)
- flags de raza (cybernetic, aquatic, lithovore, tolerant, telepathic, subterranean, ...)
- riqueza mineral del planeta
- moral
- edificios con efectos especiales (robotic_factory, soil_enrichment, autolab, etc.)
- bonus de lider asignado a la colonia
"""
import json
import math
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

with (DATA_DIR / "buildings.json").open("r", encoding="utf-8") as f:
    BUILDINGS = {item["id"]: item for item in json.load(f)}

with (DATA_DIR / "ships.json").open("r", encoding="utf-8") as f:
    SHIPS = {item["type"]: item for item in json.load(f)}

with (DATA_DIR / "governments.json").open("r", encoding="utf-8") as f:
    GOVERNMENTS = {item["id"]: item for item in json.load(f)}


# Mineral richness modifiers for industrial output (multiplier for base PP / robotic factory)
RICHNESS_MOD = {
    "ultra_poor": 0.33,
    "poor": 0.66,
    "abundant": 1.0,
    "rich": 1.5,
    "ultra_rich": 2.0,
}

# Robotic factory PP bonus by richness
ROBOTIC_PP_BY_RICHNESS = {
    "ultra_poor": 5,
    "poor": 8,
    "abundant": 10,
    "rich": 15,
    "ultra_rich": 20,
}

# Climate maximum population multipliers
CLIMATE_MAX_POP_MULT = {
    "toxic": 0.25,
    "barren": 0.40,
    "radiated": 0.30,
    "desert": 0.60,
    "tundra": 0.65,
    "arid": 0.75,
    "swamp": 0.85,
    "ocean": 0.95,
    "terran": 1.00,
    "gaia": 1.20,
}


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


def _find_planet(game_state, colony):
    if not game_state:
        return None
    sys_id = colony.get("star_system_id")
    sys = next((s for s in game_state.get("galaxy", {}).get("star_systems", []) if s.get("id") == sys_id), None)
    if not sys:
        return None
    idx = colony.get("planet_index", 0)
    if 0 <= idx < len(sys.get("planets", [])):
        return sys["planets"][idx]
    return None


def _empire_for_colony(game_state, colony):
    """Localiza el imperio dueno de la colonia dentro del game_state."""
    if not game_state:
        return None
    owner = colony.get("owner") or "player"
    if owner == "player":
        return game_state.get("player")
    return next((ai for ai in game_state.get("ai_players", []) if ai.get("id") == owner), None)


def _race_flags(empire):
    if not empire:
        return {}
    return empire.get("race", {}).get("traits", {}).get("flags", {}) or {}


def _race_traits(empire):
    if not empire:
        return {}
    return empire.get("race", {}).get("traits", {}) or {}


def _government(empire):
    if not empire:
        return GOVERNMENTS.get("dictatorship", {})
    gov_id = empire.get("government") or empire.get("race", {}).get("government", "dictatorship")
    return GOVERNMENTS.get(gov_id, GOVERNMENTS.get("dictatorship", {}))


def _building_ids(colony):
    out = []
    for b in colony.get("buildings", []):
        out.append(b if isinstance(b, str) else b.get("id"))
    return out


def calculate_colony_production(arg_a, arg_b, arg_c=None):
    """
    Devuelve y persiste en colony los outputs de food/industry/research/bc.
    Acepta (colony, player, game_state) o (game_state, colony).
    """
    colony, _player, game_state = _resolve_colony_player(arg_a, arg_b, arg_c)
    if colony is None:
        return {"food": 0, "industry": 0, "research": 0, "bc": 0, "production": 0}

    pop = colony.get("population", {})
    if isinstance(pop, dict):
        farmers = pop.get("farmers", 0)
        workers = pop.get("workers", 0)
        scientists = pop.get("scientists", 0)
        total_pop = pop.get("total", farmers + workers + scientists)
    else:
        farmers = colony.get("farmers", 0)
        workers = colony.get("workers", 0)
        scientists = colony.get("scientists", 0)
        total_pop = farmers + workers + scientists

    empire = _empire_for_colony(game_state, colony)
    flags = _race_flags(empire)
    traits = _race_traits(empire)
    gov_mods = _government(empire).get("modifiers", {})

    planet = _find_planet(game_state, colony)
    climate = (planet or {}).get("type", "terran")
    richness = (planet or {}).get("minerals", "abundant")
    rich_mult = RICHNESS_MOD.get(richness, 1.0)

    # Base outputs
    food_per_farmer = 2 + traits.get("food_bonus", 0)
    industry_per_worker = 1 + traits.get("industry_bonus", 0) + traits.get("production_per_worker_extra", 0)
    research_per_scientist = 1 + traits.get("research_per_scientist_extra", 0)
    bc_per_pop = traits.get("bc_per_capita", 0)

    # Climate penalty for food
    climate_food_pen = {
        "toxic": -3, "barren": -2, "radiated": -3, "desert": -1, "tundra": -1,
        "arid": 0, "swamp": 0, "ocean": 1, "terran": 1, "gaia": 2,
    }.get(climate, 0)
    if flags.get("tolerant"):
        climate_food_pen = max(0, climate_food_pen)
    if flags.get("aquatic") and climate == "ocean":
        climate_food_pen = max(climate_food_pen, 2)

    food = farmers * food_per_farmer + climate_food_pen
    industry = workers * industry_per_worker * rich_mult
    research = scientists * research_per_scientist
    bc = (workers // 2) + total_pop * bc_per_pop

    # Lithovore: no farmers needed, all citizens count toward food=0 consumption; redirect potential
    if flags.get("lithovore"):
        food = 0  # not needed

    # Building effects
    bonuses = {"production_bonus": 0, "research_bonus": 0, "food_bonus": 0, "bc_bonus": 0,
               "morale_bonus": 0, "ship_production_bonus": 0, "research_per_scientist_bonus": 0,
               "food_per_farmer_bonus": 0, "bc_per_pop_bonus": 0, "trade_treaty_bonus": 0}
    has_robotic = False
    has_imperial_palace = False
    has_autolab = False
    for bid in _building_ids(colony):
        record = BUILDINGS.get(bid)
        if not record:
            continue
        eff = record.get("effects", {})
        for k in list(bonuses.keys()):
            bonuses[k] += eff.get(k, 0)
        if eff.get("production_bonus_by_richness"):
            has_robotic = True
        if bid == "imperial_palace":
            has_imperial_palace = True
        if bid == "autolab":
            has_autolab = True

    # Apply per-farmer/scientist/pop bonuses from buildings
    food += farmers * bonuses["food_per_farmer_bonus"]
    research += scientists * bonuses["research_per_scientist_bonus"]
    bc += total_pop * bonuses["bc_per_pop_bonus"]

    # Apply flat building bonuses
    industry += bonuses["production_bonus"]
    research += bonuses["research_bonus"]
    food += bonuses["food_bonus"]
    bc += bonuses["bc_bonus"]

    # Robotic factory adds richness-scaled PP
    if has_robotic:
        industry += ROBOTIC_PP_BY_RICHNESS.get(richness, 10)

    # Spaceport ship_production_bonus is stored in colony for use during build queue
    colony["ship_production_bonus"] = bonuses["ship_production_bonus"]

    # Government modifiers
    if gov_mods.get("research"):
        research *= 1 + gov_mods["research"] / 100.0
    if gov_mods.get("bc"):
        bc *= 1 + gov_mods["bc"] / 100.0
    if gov_mods.get("production"):
        industry *= 1 + gov_mods["production"] / 100.0

    # Leader bonuses (try import lazily to avoid cycles)
    try:
        from app.services.leader_service import colony_leader_bonuses
        if empire:
            lb = colony_leader_bonuses(empire, colony.get("id"))
            if lb:
                if lb.get("food_pct"): food *= 1 + lb["food_pct"] / 100.0
                if lb.get("industry_pct"): industry *= 1 + lb["industry_pct"] / 100.0
                if lb.get("research_pct"): research *= 1 + lb["research_pct"] / 100.0
                if lb.get("bc_flat"): bc += lb["bc_flat"]
    except Exception:
        pass

    # Morale: integer -100..+100. If 'stable' -> 0.
    morale = colony.get("morale", 0)
    if isinstance(morale, str):
        morale = 0
    morale_bonus = bonuses["morale_bonus"] + (5 if has_imperial_palace else 0)
    morale_bonus += gov_mods.get("morale_bonus", 0)
    if not gov_mods.get("morale_immune") and not flags.get("cybernetic"):
        # Each colony's morale acts as % multiplier
        effective_morale = max(-100, min(100, morale + morale_bonus))
        production_mult = 1 + effective_morale / 100.0
        food *= production_mult
        industry *= production_mult
        research *= production_mult
        bc *= production_mult

    # Cybernetic: cost 1 PP per pop, but no food consumption
    if flags.get("cybernetic"):
        industry -= total_pop * 0.5

    # Persist
    colony["food_output"] = max(0, round(food, 2))
    colony["industry_output"] = max(0, round(industry, 2))
    colony["research_output"] = max(0, round(research, 2))
    colony["bc_output"] = max(0, round(bc, 2))
    consumption = total_pop if not flags.get("lithovore") and not flags.get("cybernetic") else 0
    colony["food_consumption"] = consumption
    colony["food_surplus"] = colony["food_output"] - consumption

    return {
        "food": colony["food_output"],
        "industry": colony["industry_output"],
        "research": colony["research_output"],
        "bc": colony["bc_output"],
        "production": colony["industry_output"],
    }


def process_colony_construction(arg_a, arg_b=None, arg_c=None, arg_d=None):
    """
    Avanza la cola de construccion. Acepta:
    - (game_state, colony)
    - (colony, player, game_state, override_production)
    Devuelve lista de eventos.
    """
    colony, _player, _game_state = _resolve_colony_player(arg_a, arg_b, arg_c)
    if colony is None:
        return []

    production = arg_d if arg_d is not None else colony.get("industry_output", 0)
    queue = colony.get("build_queue", [])
    events = []

    if not queue:
        return events

    # Spaceport ship production bonus only for ships
    head = queue[0]
    effective_prod = production
    if head.get("item_type") == "ship":
        spb = colony.get("ship_production_bonus", 0)
        if spb:
            effective_prod = production * (1 + spb / 100.0)

    head["progress"] = head.get("progress", 0) + effective_prod
    if head["progress"] >= head.get("cost", 0):
        completed = queue.pop(0)
        if completed["item_type"] == "building":
            colony.setdefault("buildings", []).append(completed["item_id"])
        events.append({"type": "construction_complete", "colony_id": colony.get("id"), "item": completed})

    return events


def get_available_buildings(game_state, colony):
    built = set(_building_ids(colony))
    empire = _empire_for_colony(game_state, colony)
    techs = set()
    if empire:
        for t in empire.get("technologies", {}).get("researched", []):
            if t.get("status") != "discarded":
                techs.add(t.get("tech_id"))

    out = []
    for building in BUILDINGS.values():
        if building["id"] in built:
            continue
        prereqs = building.get("prerequisites", {})
        if any(t not in techs for t in prereqs.get("tech", [])):
            continue
        if any(b not in built for b in prereqs.get("buildings", [])):
            continue
        # unique_per_empire: skip if any other player colony has it
        if building.get("unique_per_empire") and empire:
            already = any(
                building["id"] in _building_ids(c)
                for c in empire.get("colonies", [])
                if c is not colony
            )
            if already:
                continue
        out.append(building)
    return out


def get_available_ships(game_state, colony):
    """Devuelve naves construibles segun tech del imperio dueno."""
    empire = _empire_for_colony(game_state, colony)
    techs = set()
    if empire:
        for t in empire.get("technologies", {}).get("researched", []):
            if t.get("status") != "discarded":
                techs.add(t.get("tech_id"))

    out = []
    for ship in SHIPS.values():
        if ship.get("category") in ("antaran", "orion"):
            continue
        req = ship.get("tech_required")
        if req and req not in techs:
            continue
        if ship.get("limit_per_empire"):
            owned = sum(
                s.get("count", 0)
                for fl in (empire or {}).get("fleets", [])
                for s in fl.get("ships", [])
                if s.get("type") == ship["type"]
            )
            if owned >= ship["limit_per_empire"]:
                continue
        out.append(ship)
    return out


def has_technology(player, tech_id):
    techs = player.get("technologies", {})
    if isinstance(techs, dict):
        return any(t.get("tech_id") == tech_id for t in techs.get("researched", []) if t.get("status") != "discarded")
    return tech_id in (techs or [])
