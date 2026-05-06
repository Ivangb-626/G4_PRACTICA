import asyncio
import json
import math
import random
from datetime import datetime
from pathlib import Path

from app.services.ai_service import AIService
from app.services.colony_service import (
    BUILDINGS,
    SHIPS,
    add_to_build_queue,
    calculate_colony_production,
    get_available_buildings,
    get_available_ships,
    has_technology,
    process_colony_construction,
)
from app.services.combat_service import resolve_combat, resolve_ground_combat
from app.services.diplomacy_service import check_galactic_council, get_relation_key, initialize_diplomacy


DATA_DIR = Path(__file__).resolve().parents[1] / "data"

with (DATA_DIR / "races.json").open("r", encoding="utf-8") as f:
    RACES = {item["id"]: item for item in json.load(f)}

with (DATA_DIR / "ships.json").open("r", encoding="utf-8") as f:
    SHIP_TYPES = {item["type"]: item for item in json.load(f)}

with (DATA_DIR / "technologies.json").open("r", encoding="utf-8") as f:
    TECHS = {item["id"]: item for item in json.load(f)}


PLANET_TYPES = {
    "toxic": {"habitable": False, "food_mod": -3},
    "barren": {"habitable": False, "food_mod": -2},
    "desert": {"habitable": True, "food_mod": -1},
    "tundra": {"habitable": True, "food_mod": -1},
    "arid": {"habitable": True, "food_mod": 0},
    "swamp": {"habitable": True, "food_mod": 0},
    "ocean": {"habitable": True, "food_mod": 1},
    "terran": {"habitable": True, "food_mod": 1},
    "gaia": {"habitable": True, "food_mod": 2},
}

PLANET_SIZES = {
    "tiny": {"max_pop": 8, "build_slots": 3},
    "small": {"max_pop": 12, "build_slots": 4},
    "medium": {"max_pop": 16, "build_slots": 5},
    "large": {"max_pop": 22, "build_slots": 7},
    "huge": {"max_pop": 28, "build_slots": 8},
}

MINERAL_MOD = {
    "ultra_poor": 0.33,
    "poor": 0.66,
    "abundant": 1.0,
    "rich": 1.5,
    "ultra_rich": 2.0,
}

STAR_TYPES = {
    "red": {"max_planets": 3, "bias": ["toxic", "barren", "tundra"]},
    "orange": {"max_planets": 4, "bias": ["desert", "tundra", "arid"]},
    "yellow": {"max_planets": 5, "bias": list(PLANET_TYPES.keys())},
    "white": {"max_planets": 4, "bias": ["barren", "desert", "terran"]},
    "blue": {"max_planets": 3, "bias": ["toxic", "barren", "gaia"]},
    "black_hole": {"max_planets": 0, "bias": []},
}

GALAXY_SIZE_COUNTS = {"small": 20, "medium": 30, "large": 40, "huge": 55}

DIFFICULTY_LEVELS = ["gardener", "officer", "commander", "lord", "impossible"]

SCENARIOS = [
    {
        "id": "default",
        "name": "Estandar",
        "description": "Partida de practica",
        "galaxy_sizes": ["small", "medium", "large", "huge"],
        "galaxy_ages": ["early", "average", "late"],
        "max_opponents": 7,
        "difficulty_options": DIFFICULTY_LEVELS,
        "starting_tech_levels": ["pre_warp", "average", "advanced"],
    }
]


def random_star_type(galaxy_age="average"):
    """Black holes are rare. Galaxy age biases star color distribution."""
    rolls = ["red", "orange", "yellow", "white", "blue"]
    weights = {
        "early": [12, 16, 35, 18, 19],
        "average": [18, 22, 30, 18, 12],
        "late": [28, 24, 22, 14, 12],
    }.get(galaxy_age, [18, 22, 30, 18, 12])
    base = random.choices(rolls, weights=weights, k=1)[0]
    if random.random() < 0.05:
        return "black_hole"
    return base


def random_planet(star_type, galaxy_age="average"):
    """Galaxy age skews planet types: early -> more Gaia/Terran, late -> more toxic/barren."""
    if star_type == "black_hole":
        return None
    size = random.choice(list(PLANET_SIZES.keys()))
    bias = STAR_TYPES[star_type]["bias"]
    if galaxy_age == "early" and random.random() < 0.30:
        ptype = random.choice(["terran", "gaia", "ocean"])
    elif galaxy_age == "late" and random.random() < 0.30:
        ptype = random.choice(["toxic", "barren", "radiated", "desert"])
    else:
        ptype = random.choice(bias) if bias else "barren"
    minerals = random.choice(list(MINERAL_MOD.keys()))
    if galaxy_age == "early" and random.random() < 0.20:
        minerals = random.choice(["rich", "ultra_rich"])
    return {
        "index": 0,
        "name": f"{ptype.title()}-{random.randint(100, 999)}",
        "type": ptype,
        "size": size,
        "minerals": minerals,
        "gravity": random.choice(["low", "normal", "high"]),
        "max_population": PLANET_SIZES[size]["max_pop"],
        "colonized_by": None,
        "special": None,
    }


def _fleet_command_points(fleet):
    return sum(
        SHIP_TYPES.get(ship["type"], {}).get("command_points", 0) * ship.get("count", 0)
        for ship in fleet.get("ships", [])
    )


def _normalize_population(colony):
    total = max(1, int(round(colony["population"].get("total", 1))))
    max_pop = max(1, int(round(colony["population"].get("max", total))))
    total = min(total, max_pop)

    farmers = max(0, int(round(colony["population"].get("farmers", 0))))
    workers = max(0, int(round(colony["population"].get("workers", 0))))
    scientists = max(0, int(round(colony["population"].get("scientists", 0))))

    values = {"farmers": farmers, "workers": workers, "scientists": scientists}
    assigned = sum(values.values())
    if assigned > total:
        overflow = assigned - total
        for key in ["scientists", "workers", "farmers"]:
            take = min(values[key], overflow)
            values[key] -= take
            overflow -= take
            if overflow <= 0:
                break
    elif assigned < total:
        values["farmers"] += total - assigned

    colony["population"]["total"] = total
    colony["population"]["max"] = max_pop
    colony["population"]["farmers"] = values["farmers"]
    colony["population"]["workers"] = values["workers"]
    colony["population"]["scientists"] = values["scientists"]


GREEK_LETTERS = [
    "Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta", "Eta", "Theta",
    "Iota", "Kappa", "Lambda", "Sigma", "Omega", "Tau", "Omicron", "Rho",
    "Phi", "Chi", "Psi", "Pi", "Mu", "Nu", "Xi",
]

CLASSICAL_STARS = [
    "Centauri", "Eridani", "Cygni", "Draconis", "Lyrae", "Ursae", "Cassiopeiae",
    "Andromedae", "Persei", "Aurigae", "Pegasi", "Orionis", "Tauri", "Aquilae",
    "Carinae", "Velorum", "Hydrae", "Leonis", "Virginis", "Bootis",
]

PROPER_STARS = [
    "Rigel", "Sirius", "Vega", "Altair", "Antares", "Polaris", "Arcturus",
    "Betelgeuse", "Aldebaran", "Spica", "Pollux", "Deneb", "Capella", "Procyon",
    "Mintaka", "Alnilam", "Bellatrix", "Mizar", "Alcor", "Fomalhaut", "Achernar",
    "Canopus", "Regulus", "Hadar", "Alphard", "Atria", "Mira", "Kepler", "Tycho",
]

CATALOG_PREFIXES = ["HD", "NGC", "HIP", "PSR", "GJ", "WR", "K", "M", "IC", "Wolf"]

ADJECTIVES = [
    "Crimson", "Azure", "Silent", "Hollow", "Ember", "Frozen", "Drifting",
    "Forgotten", "Eternal", "Veiled", "Serene", "Wandering", "Burning",
    "Shattered", "Lone", "Twilight", "Shrouded", "Blazing", "Iron", "Obsidian",
]

NOUNS = [
    "Helix", "Veil", "Spire", "Beacon", "Cradle", "Reach", "Expanse", "Forge",
    "Maw", "Gate", "Drift", "Halo", "Crown", "Abyss", "Mantle", "Echo", "Shroud",
    "Vault", "Pulse", "Throne",
]

SUFFIXES = [
    "Prime", "Proxima", "Major", "Minor", "Borealis", "Australis", "Magna",
    "Nova", "Ultima",
]


def generate_random_system_name():
    """Procedural sci-fi star-system name. Avoids trailing roman numerals so
    planets can append I/II/III without colliding."""
    pattern = random.choices(
        ["greek_classical", "greek_proper", "proper", "catalog", "adj_noun", "noun_suffix"],
        weights=[28, 18, 14, 18, 14, 8],
        k=1,
    )[0]

    if pattern == "greek_classical":
        return f"{random.choice(GREEK_LETTERS)} {random.choice(CLASSICAL_STARS)}"
    if pattern == "greek_proper":
        return f"{random.choice(GREEK_LETTERS)} {random.choice(PROPER_STARS)}"
    if pattern == "proper":
        base = random.choice(PROPER_STARS)
        if random.random() < 0.35:
            return f"{base} {random.choice(SUFFIXES)}"
        return base
    if pattern == "catalog":
        prefix = random.choice(CATALOG_PREFIXES)
        number = random.randint(101, 9999)
        return f"{prefix}-{number}"
    if pattern == "adj_noun":
        return f"{random.choice(ADJECTIVES)} {random.choice(NOUNS)}"
    return f"{random.choice(NOUNS)} {random.choice(SUFFIXES)}"

def generate_galaxy(size, num_opponents, player_race_id, galaxy_age="average", orion_guardian=True):
    counts = GALAXY_SIZE_COUNTS
    systems = []
    
    used_names = set()
    used_positions = []
    min_dist = 5.0  # Minimum distance percentage between stars

    for index in range(counts.get(size, 30)):
        star_type = random_star_type(galaxy_age)

        system_name = generate_random_system_name()
        while system_name in used_names:
            system_name = generate_random_system_name()
        used_names.add(system_name)
        
        # Valid positioning
        x, y = 0, 0
        valid_pos = False
        attempts = 0
        while not valid_pos and attempts < 100:
            x = random.random() * 100
            y = random.random() * 100
            valid_pos = True
            for px, py in used_positions:
                dist = math.sqrt((x - px) ** 2 + (y - py) ** 2)
                if dist < min_dist:
                    valid_pos = False
                    break
            attempts += 1
            
        used_positions.append((x, y))

        planets = []
        max_planets = STAR_TYPES[star_type]["max_planets"]
        if max_planets > 0:
            for planet_index in range(random.randint(1, max_planets)):
                planet = random_planet(star_type, galaxy_age)
                if planet is None:
                    continue
                planet["index"] = planet_index
                numerals = ["I", "II", "III", "IV", "V", "VI", "VII"]
                numeral = numerals[planet_index] if planet_index < len(numerals) else str(planet_index + 1)
                planet["name"] = f"{system_name} {numeral}"
                planets.append(planet)

        systems.append(
            {
                "id": f"sys_{index}",
                "name": system_name if star_type != "black_hole" else f"BH {system_name}",
                "position": {"x": x, "y": y},
                "star_type": star_type,
                "planets": planets,
                "connections": [],
                "explored_by": [],
                "guardian": {"active": False, "fleet": None},
                "is_black_hole": star_type == "black_hole",
            }
        )

    for index in range(1, len(systems)):
        connect_to = random.randint(0, index - 1)
        systems[index]["connections"].append(systems[connect_to]["id"])
        systems[connect_to]["connections"].append(systems[index]["id"])

    for _ in range(len(systems) // 3):
        first, second = random.sample(range(len(systems)), 2)
        if systems[second]["id"] not in systems[first]["connections"]:
            systems[first]["connections"].append(systems[second]["id"])
            systems[second]["connections"].append(systems[first]["id"])

    orion = systems[0]
    orion["name"] = "Orion"
    orion["star_type"] = "yellow"
    orion["is_black_hole"] = False
    orion["planets"] = [
        {
            "index": 0,
            "name": f"{orion['name']} I",
            "type": "gaia",
            "size": "huge",
            "minerals": "ultra_rich",
            "gravity": "normal",
            "max_population": 28,
            "colonized_by": None,
            "special": "gaia",
        }
    ]
    if orion_guardian:
        orion["guardian"] = {
            "active": True,
            "fleet": {
                "id": "antaran_guardian",
                "name": "Guardian of Orion",
                "owner": "antaranos",
                "star_system_id": orion["id"],
                "ships": [{"type": "battleship", "count": 1}, {"type": "cruiser", "count": 2}, {"type": "destroyer", "count": 3}],
                "destination": None,
                "eta_turns": None,
                "command_points_used": 0,
            },
        }
    else:
        orion["guardian"] = {"active": False, "fleet": None}

    # PLAN sec 18 — Space Monsters guard a few non-Orion, non-starting systems
    candidate_indices = list(range(2, len(systems)))
    random.shuffle(candidate_indices)
    monster_count = max(1, len(systems) // 10)
    monster_kinds = ["space_crystal", "space_amoeba", "space_eel"]
    for idx in candidate_indices[:monster_count]:
        sys = systems[idx]
        if sys.get("guardian", {}).get("active"):
            continue
        kind = random.choice(monster_kinds)
        is_travelling = random.random() < 0.25
        sys["space_monster"] = {
            "type": kind,
            "is_travelling": is_travelling,
            "defeated": False,
        }

    return {
        "size": size,
        "num_systems": len(systems),
        "star_systems": systems,
        "fog_of_war": {"player": [], "ai_0": [], "ai_1": [], "ai_2": []},
    }


def make_colony(star_system_id, planet_index, owner, planet=None):
    max_population = 8
    if planet:
        max_population = planet.get("max_population", max_population)
    return {
        "id": f"col_{star_system_id}_{planet_index}",
        "name": f"Colony {star_system_id}-{planet_index}",
        "star_system_id": star_system_id,
        "planet_index": planet_index,
        "owner": owner,
        "population": {"total": 1, "max": max_population, "farmers": 1, "workers": 0, "scientists": 0},
        "buildings": [],
        "build_queue": [],
        "morale": "stable",
        "food_output": 0,
        "food_consumption": 0,
        "food_surplus": 0,
        "industry_output": 0,
        "research_output": 0,
        "bc_output": 0,
        "ground_defense": 0,
        "orbital_defense": 0,
    }


def _initial_empire(owner_id, race_id, system, include_id=False, personality=None):
    colony = make_colony(system["id"], 0, owner_id, system["planets"][0])
    empire = {
        "race": RACES[race_id],
        "resources": {
            "bc": 200,
            "total_food_surplus": 0,
            "total_production": 0,
            "total_research": 0,
            "command_points": 4,
            "command_points_used": 0,
        },
        "colonies": [colony],
        "fleets": [
            {
                "id": f"fleet_{owner_id}",
                "name": "Initial Fleet" if owner_id == "player" else f"AI Fleet {owner_id}",
                "owner": owner_id,
                "star_system_id": system["id"],
                "ships": [{"type": "frigate", "count": 2}, {"type": "colony_ship", "count": 1}],
                "destination": None,
                "eta_turns": None,
                "command_points_used": 2,
            }
        ],
        "technologies": {"researched": [], "current_research": None},
    }
    if include_id:
        empire["id"] = owner_id
        empire["personality"] = personality or "balanced"
        empire["diplomacy_stance"] = "hostile"
    return empire


def _normalize_difficulty(diff: str) -> str:
    diff = (diff or "officer").lower()
    aliases = {"easy": "gardener", "normal": "officer", "hard": "commander"}
    diff = aliases.get(diff, diff)
    if diff not in DIFFICULTY_LEVELS:
        return "officer"
    return diff


def _starting_techs_for_level(level: str) -> list:
    """Returns initial researched tech IDs based on starting tech level."""
    if level == "pre_warp":
        return []
    if level == "advanced":
        return ["construction_1", "computers_1", "biology_1", "chemistry_1", "laser", "force_fields_1", "power_1", "sociology_1", "engineering_1"]
    return ["construction_1", "computers_1", "biology_1"]  # average


def generate_game_state(name, scenario):
    galaxy_size = scenario.get("galaxy_size", "medium")
    galaxy_age = scenario.get("galaxy_age", "average")
    orion_guardian = scenario.get("orion_guardian_enabled", True)
    antaran_attacks_enabled = scenario.get("antaran_attacks_enabled", True)
    starting_tech_level = scenario.get("starting_tech_level", "average")
    random_events_enabled = scenario.get("random_events_enabled", True)

    galaxy = generate_galaxy(galaxy_size, scenario["num_opponents"], scenario["player_race"], galaxy_age, orion_guardian)
    # Player system: pick first non-black-hole index
    player_system = next((s for s in galaxy["star_systems"][1:] if not s.get("is_black_hole")), galaxy["star_systems"][1])
    
    if scenario.get("home_system_name"):
        player_system["name"] = scenario["home_system_name"]
        for i, planet in enumerate(player_system["planets"]):
            numerals = ["Prime", "II", "III", "IV", "V", "VI", "VII"]
            num_str = numerals[i] if i < len(numerals) else str(i + 1)
            planet["name"] = f"{player_system['name']} {num_str}"
        
    player_system["explored_by"].append("player")
    player_system["planets"][0]["colonized_by"] = "player"
    galaxy["fog_of_war"]["player"] = [player_system["id"], *player_system["connections"]]

    ai_players = []
    available_races = [race_id for race_id in RACES if race_id != scenario["player_race"]]
    random.shuffle(available_races)
    # Find suitable AI start systems: skip player's, skip black holes, must have a habitable planet
    candidate_systems = [
        s for s in galaxy["star_systems"]
        if s["id"] != player_system["id"] and not s.get("is_black_hole") and s.get("planets") and any(PLANET_TYPES.get(p.get("type"), {}).get("habitable") for p in s["planets"])
    ]
    random.shuffle(candidate_systems)
    for index in range(scenario["num_opponents"]):
        if index >= len(candidate_systems):
            break
        ai_id = f"ai_{index}"
        ai_system = candidate_systems[index]
        ai_system["explored_by"].append(ai_id)
        habitable_idx = next((i for i, p in enumerate(ai_system["planets"]) if PLANET_TYPES.get(p.get("type"), {}).get("habitable")), 0)
        ai_system["planets"][habitable_idx]["colonized_by"] = ai_id
        galaxy["fog_of_war"][ai_id] = [ai_system["id"], *ai_system["connections"]]
        race_id = available_races[index % len(available_races)] if available_races else scenario["player_race"]
        ai_players.append(
            _initial_empire(
                ai_id,
                race_id,
                ai_system,
                include_id=True,
                personality=RACES[race_id].get("ai_personality") or random.choice(["aggressive", "defensive", "expansionist", "researcher", "balanced"]),
            )
        )

    difficulty = _normalize_difficulty(scenario.get("difficulty"))
    starting_techs = _starting_techs_for_level(starting_tech_level)

    player_empire = _initial_empire("player", scenario["player_race"], player_system)
    # Apply starting techs
    for tech_id in starting_techs:
        tech = TECHS.get(tech_id)
        if tech:
            player_empire["technologies"]["researched"].append({"field": tech["field"], "level": tech["level"], "tech_id": tech_id, "status": "researched"})
    for ai_emp in ai_players:
        for tech_id in starting_techs:
            tech = TECHS.get(tech_id)
            if tech:
                ai_emp["technologies"]["researched"].append({"field": tech["field"], "level": tech["level"], "tech_id": tech_id, "status": "researched"})

    # Apply difficulty AI bonuses
    try:
        with (DATA_DIR / "difficulty.json").open("r", encoding="utf-8") as f:
            diff_data = json.load(f)
        rec = diff_data.get(difficulty, {})
        if "alias_of" in rec:
            rec = diff_data.get(rec["alias_of"], {})
        for ai_emp in ai_players:
            ai_emp["resources"]["bc"] = ai_emp["resources"].get("bc", 0) + int(rec.get("ai_starting_bc", 0))
            extra_techs_count = int(rec.get("ai_starting_techs", 0))
            if extra_techs_count > 0:
                pool_techs = list(TECHS.values())
                random.shuffle(pool_techs)
                for tech in pool_techs[:extra_techs_count]:
                    ai_emp["technologies"]["researched"].append({"field": tech["field"], "level": tech["level"], "tech_id": tech["id"], "status": "researched"})
    except Exception:
        pass

    antaran_next = (50 + random.randint(0, 30)) if antaran_attacks_enabled else None

    game_state = {
        "game_id": None,
        "name": name,
        "scenario_id": scenario.get("scenario_id", "default"),
        "difficulty": difficulty,
        "galaxy_size": galaxy_size,
        "galaxy_age": galaxy_age,
        "starting_tech_level": starting_tech_level,
        "antaran_attacks_enabled": antaran_attacks_enabled,
        "orion_guardian_enabled": orion_guardian,
        "random_events_enabled": random_events_enabled,
        "turn": 1,
        "current_player": "player",
        "created_at": datetime.utcnow().isoformat(),
        "last_saved": datetime.utcnow().isoformat(),
        "is_autosave": False,
        "cheats_used": [],
        "antaran_next_attack_turn": antaran_next,
        "antarans_active": False,
        "antaran_attack_level": 1,
        "dimensional_portal_built": False,
        "antaran_homeworld_conquered": False,
        "orion_guardian_defeated": False,
        "orion_colonized": False,
        "avenger_fleet_id": None,
        "exotic_technologies": [],
        "victory_condition": None,
        "player": player_empire,
        "ai_players": ai_players,
        "galaxy": galaxy,
    }
    initialize_diplomacy(game_state)
    return game_state


def get_empire(game_state, owner_id):
    if owner_id == "player":
        return game_state["player"]
    return next((item for item in game_state.get("ai_players", []) if item["id"] == owner_id), None)


def get_game_safe(game_state, user="player"):
    return game_state


def find_system(game_state, system_id):
    return next((item for item in game_state["galaxy"]["star_systems"] if item["id"] == system_id), None)


def find_fleet(game_state, owner_or_fleet_id, fleet_id=None):
    if fleet_id is None:
        lookup_id = owner_or_fleet_id
        for owner_id in ["player", *[ai["id"] for ai in game_state.get("ai_players", [])]]:
            empire = get_empire(game_state, owner_id)
            fleet = next((item for item in empire.get("fleets", []) if item["id"] == lookup_id), None) if empire else None
            if fleet:
                return fleet
        return None
    empire = get_empire(game_state, owner_or_fleet_id)
    if not empire:
        return None
    return next((item for item in empire.get("fleets", []) if item["id"] == fleet_id), None)


def _reveal_for_owner(game_state, owner_id, system_id):
    visible = game_state["galaxy"]["fog_of_war"].setdefault(owner_id, [])
    if system_id not in visible:
        visible.append(system_id)
    system = find_system(game_state, system_id)
    if system:
        for connection in system.get("connections", []):
            if connection not in visible:
                visible.append(connection)


def move_fleet(game_state, owner_or_fleet_id, fleet_id=None, destination=None):
    if destination is None:
        destination = fleet_id
        fleet_id = owner_or_fleet_id
        owner_id = "player"
    else:
        owner_id = owner_or_fleet_id

    fleet = find_fleet(game_state, owner_id, fleet_id)
    if not fleet:
        raise ValueError("Fleet not found")
    if fleet.get("destination") is not None:
        raise ValueError("Fleet already in transit")
    if not destination or not isinstance(destination, str):
        raise ValueError("Destination is required")

    current = find_system(game_state, fleet["star_system_id"])
    target = find_system(game_state, destination)
    if not current or not target:
        raise ValueError("Destination not found")
    if destination not in current.get("connections", []):
        raise ValueError("Destination not reachable")

    slowest = min(SHIP_TYPES[ship["type"]]["speed"] for ship in fleet["ships"] if ship.get("count", 0) > 0)
    # Trilarian transdimensional: +2 to every ship speed
    empire = get_empire(game_state, owner_id)
    flags = (empire or {}).get("race", {}).get("traits", {}).get("flags", {})
    if flags.get("transdimensional"):
        slowest += 2
    distance = math.dist(
        [current["position"]["x"], current["position"]["y"]],
        [target["position"]["x"], target["position"]["y"]],
    )

    # Black hole hazard: requires Navigator leader, otherwise lose half the ships
    casualties = []
    if target.get("is_black_hole"):
        try:
            from app.services.leader_service import fleet_leader_bonuses
            bonuses = fleet_leader_bonuses(empire, fleet["id"]) if empire else {}
        except Exception:
            bonuses = {}
        if not bonuses.get("black_hole_safe"):
            for ship in fleet.get("ships", []):
                lost = max(0, int(ship.get("count", 0) * 0.5))
                casualties.append({"type": ship["type"], "lost": lost})
                ship["count"] = max(0, ship["count"] - lost)
            fleet["ships"] = [s for s in fleet["ships"] if s.get("count", 0) > 0]
            if not fleet["ships"]:
                # Fleet wiped out
                empire["fleets"] = [f for f in empire.get("fleets", []) if f["id"] != fleet["id"]]
                return {"fleet": None, "path": [current["id"], destination], "black_hole_destroyed": True, "casualties": casualties}

    fleet["destination"] = destination
    fleet["eta_turns"] = max(1, math.ceil(distance / max(slowest * 18, 1)))
    return {"fleet": fleet, "path": [current["id"], destination], "black_hole_casualties": casualties}


def colonize_planet(game_state, owner_or_fleet_id, fleet_id=None, planet_index=None):
    if planet_index is None:
        planet_index = fleet_id
        fleet_id = owner_or_fleet_id
        owner_id = "player"
    else:
        owner_id = owner_or_fleet_id

    fleet = find_fleet(game_state, owner_id, fleet_id)
    if not fleet:
        raise ValueError("Fleet not found")
    colony_ship = next(
        (ship for ship in fleet.get("ships", []) if ship["type"] == "colony_ship" and ship.get("count", 0) > 0),
        None,
    )
    if not colony_ship:
        raise ValueError("No colony ship in fleet")

    system = find_system(game_state, fleet["star_system_id"])
    if not system:
        raise ValueError("System not found")
    if system["id"] not in game_state["galaxy"]["fog_of_war"].get(owner_id, []):
        raise ValueError("System not explored")
    if not isinstance(planet_index, int) or planet_index < 0 or planet_index >= len(system["planets"]):
        raise ValueError("Invalid planet index")

    planet = system["planets"][planet_index]
    if planet["colonized_by"] is not None:
        raise ValueError("Planet already colonized")
    # Tolerant or Silicoid-like: can colonize anything except destroyed
    empire = get_empire(game_state, owner_id)
    flags = (empire or {}).get("race", {}).get("traits", {}).get("flags", {})
    habitable = PLANET_TYPES.get(planet["type"], {}).get("habitable", False)
    if not habitable and not flags.get("tolerant"):
        raise ValueError("Planet not colonizable without Tolerant trait")

    planet["colonized_by"] = owner_id
    colony_ship["count"] -= 1
    fleet["ships"] = [ship for ship in fleet["ships"] if ship.get("count", 0) > 0]
    fleet["command_points_used"] = _fleet_command_points(fleet)

    new_colony = make_colony(system["id"], planet_index, owner_id, planet)
    get_empire(game_state, owner_id)["colonies"].append(new_colony)
    _reveal_for_owner(game_state, owner_id, system["id"])
    return {"new_colony": new_colony, "fleet": fleet}


def set_research(game_state, field, level, tech_id, owner_id="player"):
    tech = TECHS.get(tech_id)
    if not tech or tech["field"] != field or tech["level"] != level:
        raise ValueError("Technology not available")

    technologies = get_empire(game_state, owner_id)["technologies"]
    if any(item["tech_id"] == tech_id and item.get("status") != "discarded" for item in technologies["researched"]):
        raise ValueError("Already researched")
    if level > 1 and not any(
        item["field"] == field and item["level"] == level - 1 and item.get("status") != "discarded"
        for item in technologies["researched"]
    ):
        raise ValueError("Previous level not completed")
    if any(
        item["field"] == field and item["level"] == level and item.get("status") != "discarded"
        for item in technologies["researched"]
    ):
        raise ValueError("Technology already resolved at this level")

    technologies["current_research"] = {
        "field": field,
        "level": level,
        "tech_id": tech_id,
        "progress": 0,
        "total_cost": tech["research_cost"],
    }
    for other_id, other in TECHS.items():
        if other_id != tech_id and other["field"] == field and other["level"] == level:
            technologies["researched"].append(
                {"field": field, "level": level, "tech_id": other_id, "status": "discarded"}
            )
    return {"current_research": technologies["current_research"]}


def _apply_research(game_state, owner_id):
    empire = get_empire(game_state, owner_id)
    current = empire["technologies"].get("current_research")
    if not current:
        return None
    current["progress"] += sum(colony.get("research_output", 0) for colony in empire.get("colonies", []))
    if current["progress"] >= current["total_cost"]:
        empire["technologies"]["researched"].append(
            {
                "field": current["field"],
                "level": current["level"],
                "tech_id": current["tech_id"],
                "status": "researched",
            }
        )
        empire["technologies"]["current_research"] = None
        return {"type": "research_complete", "owner": owner_id, "tech_id": current["tech_id"]}
    return None


def _compute_empire_economy(game_state, owner_id):
    empire = get_empire(game_state, owner_id)
    total_bc = 0
    total_research = 0
    total_production = 0
    total_food = 0

    for colony in empire.get("colonies", []):
        _normalize_population(colony)
        calculate_colony_production(game_state, colony)
        total_bc += colony.get("bc_output", 0)
        total_research += colony.get("research_output", 0)
        total_production += colony.get("industry_output", 0)
        total_food += colony.get("food_surplus", 0)

        if colony.get("food_surplus", 0) < 0:
            colony["population"]["total"] = max(1, colony["population"]["total"] - 1)
        else:
            growth_bonus = empire["race"]["traits"].get("population_growth_bonus", 0) / 100
            growth = 0.5 * (1 + growth_bonus) * (
                1 - colony["population"]["total"] / max(colony["population"]["max"], 1)
            )
            if growth > 0:
                colony["population"]["total"] = min(
                    colony["population"]["max"],
                    colony["population"]["total"] + int(max(1, round(growth))),
                )
        _normalize_population(colony)

    empire["resources"]["total_bc"] = round(total_bc, 2)
    empire["resources"]["total_research"] = round(total_research, 2)
    empire["resources"]["total_production"] = round(total_production, 2)
    empire["resources"]["total_food_surplus"] = round(total_food, 2)
    empire["resources"]["bc"] = round(empire["resources"].get("bc", 0) + total_bc, 2)


def process_fleet_movements(game_state):
    events = []
    for owner_id in ["player", *[ai["id"] for ai in game_state.get("ai_players", [])]]:
        empire = get_empire(game_state, owner_id)
        for fleet in empire.get("fleets", []):
            if fleet.get("eta_turns") is None:
                continue
            fleet["eta_turns"] -= 1
            if fleet["eta_turns"] <= 0:
                fleet["star_system_id"] = fleet["destination"]
                fleet["destination"] = None
                fleet["eta_turns"] = None
                _reveal_for_owner(game_state, owner_id, fleet["star_system_id"])
                events.append({"type": "fleet_arrival", "owner": owner_id, "fleet_id": fleet["id"], "system_id": fleet["star_system_id"]})
    return events


def _factions_hostile(game_state, owner_a, owner_b):
    if owner_a == owner_b:
        return False
    if "antaranos" in [owner_a, owner_b]:
        return True
    initialize_diplomacy(game_state)
    key = get_relation_key(game_state["diplomacy"]["relations"], owner_a, owner_b)
    if not key:
        return False
    return game_state["diplomacy"]["relations"][key].get("value", 50) <= 0


def resolve_space_combats(game_state):
    events = []
    fleets_by_system = {}
    for owner_id in ["player", *[ai["id"] for ai in game_state.get("ai_players", [])]]:
        empire = get_empire(game_state, owner_id)
        for fleet in empire.get("fleets", []):
            if fleet.get("destination") is None:
                fleets_by_system.setdefault(fleet["star_system_id"], []).append((owner_id, fleet))
    for system in game_state["galaxy"]["star_systems"]:
        guardian = system.get("guardian", {})
        if guardian.get("active") and guardian.get("fleet"):
            fleets_by_system.setdefault(system["id"], []).append(("antaranos", guardian["fleet"]))

    for system_id, fleets in fleets_by_system.items():
        pair = None
        for owner_a, _ in fleets:
            for owner_b, _ in fleets:
                if owner_a != owner_b and _factions_hostile(game_state, owner_a, owner_b):
                    pair = (owner_a, owner_b)
                    break
            if pair:
                break
        if not pair:
            continue

        attacker_owner, defender_owner = pair
        attacker_fleets = [fleet for owner, fleet in fleets if owner == attacker_owner]
        defender_fleets = [fleet for owner, fleet in fleets if owner == defender_owner]
        attacker_bundle = {"ships": [ship for fleet in attacker_fleets for ship in fleet.get("ships", [])]}
        defender_bundle = {"ships": [ship for fleet in defender_fleets for ship in fleet.get("ships", [])]}
        result = resolve_combat(attacker_bundle, defender_bundle)

        if attacker_fleets:
            attacker_fleets[0]["ships"] = result["attacker_remaining"]
            attacker_fleets[0]["command_points_used"] = _fleet_command_points(attacker_fleets[0])
            for fleet in attacker_fleets[1:]:
                fleet["ships"] = []
        if defender_fleets:
            defender_fleets[0]["ships"] = result["defender_remaining"]
            defender_fleets[0]["command_points_used"] = _fleet_command_points(defender_fleets[0])
            for fleet in defender_fleets[1:]:
                fleet["ships"] = []

        events.append(
            {
                "type": "combat_resolved",
                "system_id": system_id,
                "winner": result["winner"],
                "attacker": attacker_owner,
                "defender": defender_owner,
            }
        )

    for owner_id in ["player", *[ai["id"] for ai in game_state.get("ai_players", [])]]:
        empire = get_empire(game_state, owner_id)
        empire["fleets"] = [fleet for fleet in empire.get("fleets", []) if fleet.get("ships")]
    return events


def _available_research(technologies):
    options = []
    researched = {item["tech_id"] for item in technologies.get("researched", []) if item.get("status") != "discarded"}
    discarded = {item["tech_id"] for item in technologies.get("researched", []) if item.get("status") == "discarded"}
    for tech in TECHS.values():
        if tech["id"] in researched or tech["id"] in discarded:
            continue
        if tech["level"] > 1 and not any(
            item["field"] == tech["field"] and item["level"] == tech["level"] - 1 and item.get("status") != "discarded"
            for item in technologies.get("researched", [])
        ):
            continue
        if any(
            item["field"] == tech["field"] and item["level"] == tech["level"] and item.get("status") != "discarded"
            for item in technologies.get("researched", [])
        ):
            continue
        options.append(tech)
    options.sort(key=lambda item: (item["level"], item["field"], item["research_cost"]))
    return options


def _ai_actions(game_state, ai_player):
    actions = {"can_colonize": [], "can_research": [], "available_buildings": {}, "available_ships": {}, "can_move": []}
    if ai_player["technologies"].get("current_research") is None:
        actions["can_research"] = _available_research(ai_player["technologies"])

    for colony in ai_player.get("colonies", []):
        actions["available_buildings"][colony["id"]] = get_available_buildings(game_state, colony)
        actions["available_ships"][colony["id"]] = get_available_ships(game_state, colony)

    for fleet in ai_player.get("fleets", []):
        if fleet.get("destination") is not None:
            continue
        system = find_system(game_state, fleet["star_system_id"])
        if not system:
            continue
        if any(ship["type"] == "colony_ship" and ship.get("count", 0) > 0 for ship in fleet.get("ships", [])):
            for planet in system.get("planets", []):
                if planet.get("colonized_by") is None and PLANET_TYPES.get(planet["type"], {}).get("habitable", False):
                    actions["can_colonize"].append({"fleetId": fleet["id"], "planetIndex": planet["index"], "systemId": system["id"]})
                    break
        for connection in system.get("connections", []):
            priority = 0 if connection not in game_state["galaxy"]["fog_of_war"].get(ai_player["id"], []) else 1
            actions["can_move"].append({"fleetId": fleet["id"], "destination": connection, "priority": priority})
    actions["can_move"].sort(key=lambda item: item["priority"])
    return actions


def _apply_ai_action(game_state, ai_player, action):
    action_type = action.get("type")
    details = action.get("details", {})
    if action_type == "selectResearch":
        tech_id = details.get("techId")
        tech = TECHS.get(tech_id)
        if not tech:
            return None
        set_research(game_state, tech["field"], tech["level"], tech_id, owner_id=ai_player["id"])
        return {"type": "ai_research_selected", "owner": ai_player["id"], "tech_id": tech_id}
    if action_type == "colonizePlanet":
        result = colonize_planet(game_state, ai_player["id"], details.get("fleetId"), details.get("planetIndex"))
        return {"type": "ai_colonized", "owner": ai_player["id"], "colony_id": result["new_colony"]["id"]}
    if action_type == "moveFleet":
        move_fleet(game_state, ai_player["id"], details.get("fleetId"), details.get("destination"))
        return {"type": "ai_fleet_moved", "owner": ai_player["id"], "fleet_id": details.get("fleetId")}
    if action_type == "addBuildQueue":
        colony = next((item for item in ai_player.get("colonies", []) if item["id"] == details.get("colonyId")), None)
        if not colony:
            return None
        if details.get("itemType") == "building" and details.get("itemId") in BUILDINGS:
            add_to_build_queue(colony, "building", details["itemId"], BUILDINGS[details["itemId"]]["cost"])
            return {"type": "ai_build_order", "owner": ai_player["id"], "item_id": details["itemId"]}
        if details.get("itemType") == "ship" and details.get("itemId") in SHIP_TYPES:
            add_to_build_queue(colony, "ship", details["itemId"], SHIP_TYPES[details["itemId"]]["cost"])
            return {"type": "ai_build_order", "owner": ai_player["id"], "item_id": details["itemId"]}
    return None


def check_victory(game_state):
    player_colonies = len(game_state["player"].get("colonies", []))
    player_fleets = len([fleet for fleet in game_state["player"].get("fleets", []) if fleet.get("ships")])
    ai_colonies = sum(len(ai.get("colonies", [])) for ai in game_state.get("ai_players", []))
    ai_fleets = sum(len([fleet for fleet in ai.get("fleets", []) if fleet.get("ships")]) for ai in game_state.get("ai_players", []))

    # PLAN sec 20 — Antaran homeworld conquest victory
    if game_state.get("antaran_homeworld_conquered"):
        game_state["victory_condition"] = "Antaran"
        return "victory"

    # Diplomatic victory (set by check_galactic_council)
    if game_state.get("victory_condition") == "Diplomatic":
        return "victory"

    if ai_colonies == 0 and ai_fleets == 0:
        game_state["victory_condition"] = "Conquest"
        return "victory"
    if player_colonies == 0 and player_fleets == 0:
        game_state["victory_condition"] = "Defeat"
        return "defeat"
    return None


# PLAN sec 19 — Reward for defeating the Guardian
EXOTIC_TECHS = [
    "phasing_cloak",
    "stellar_converter",
    "death_ray",
    "doom_star_hull",
    "antaran_xeno_psychology",
]


def defeat_orion_guardian(game_state, owner_id="player"):
    """PLAN sec 19 — Apply rewards when the Orion Guardian is defeated."""
    if game_state.get("orion_guardian_defeated"):
        return {"success": False, "reason": "Guardian already defeated"}

    orion = next((s for s in game_state["galaxy"]["star_systems"] if s.get("name", "").lower() == "orion"), None)
    if not orion:
        return {"success": False, "reason": "Orion system not found"}

    game_state["orion_guardian_defeated"] = True
    orion["guardian"]["active"] = False
    orion["guardian"]["fleet"] = None

    # Grant exotic techs
    granted = random.sample(EXOTIC_TECHS, k=min(3, len(EXOTIC_TECHS)))
    game_state["exotic_technologies"] = granted

    empire = get_empire(game_state, owner_id)
    if empire:
        empire["technologies"] = list(set(empire.get("technologies", []) + granted))
        # Avenger fleet — gift the last Orion's powerful battleship
        avenger_id = f"avenger_{owner_id}"
        avenger_fleet = {
            "id": avenger_id,
            "name": "Avenger",
            "owner": owner_id,
            "star_system_id": orion["id"],
            "ships": [{"type": "battleship", "count": 1}],
            "destination": None,
            "eta_turns": None,
            "is_avenger": True,
        }
        empire.setdefault("fleets", []).append(avenger_fleet)
        game_state["avenger_fleet_id"] = avenger_id

    return {"success": True, "exotic_techs": granted, "avenger_fleet_id": game_state.get("avenger_fleet_id")}


def build_dimensional_portal(game_state, owner_id="player", colony_id=None):
    """PLAN sec 20 — Build the Dimensional Portal needed to assault Antares."""
    cost = 1000
    empire = get_empire(game_state, owner_id)
    if not empire:
        return {"success": False, "reason": "Empire not found"}
    if game_state.get("dimensional_portal_built"):
        return {"success": False, "reason": "Portal already built"}
    if empire["resources"].get("bc", 0) < cost:
        return {"success": False, "reason": f"Not enough BC ({cost} required)"}
    # Require certain tech as gate
    techs = empire.get("technologies", [])
    if "physics_lvl3" not in techs and "antaran_xeno_psychology" not in techs:
        return {"success": False, "reason": "Requires advanced physics or exotic Antaran tech"}

    empire["resources"]["bc"] -= cost
    game_state["dimensional_portal_built"] = True
    return {"success": True, "message": "Dimensional Portal constructed. You may now assault the Antaran homeworld."}


def attack_antaran_homeworld(game_state, owner_id="player", fleet_id=None):
    """PLAN sec 20 — Final assault. Conquering the homeworld triggers Antaran victory."""
    if not game_state.get("dimensional_portal_built"):
        return {"success": False, "reason": "Dimensional Portal not built"}
    empire = get_empire(game_state, owner_id)
    if not empire:
        return {"success": False, "reason": "Empire not found"}
    fleet = next((f for f in empire.get("fleets", []) if f["id"] == fleet_id), None) if fleet_id else None
    if not fleet:
        return {"success": False, "reason": "Fleet required for the assault"}

    # Resolve combat against an Antaran homeworld defense (very strong)
    antaran_defense = {
        "ships": [
            {"type": "battleship", "count": 3},
            {"type": "cruiser", "count": 5},
        ],
    }
    result = resolve_combat(fleet, antaran_defense, defender_orbital_defense=200, ship_types_data=SHIP_TYPES)
    if result["winner"] == "attacker":
        game_state["antaran_homeworld_conquered"] = True
        game_state["victory_condition"] = "Antaran"
        return {"success": True, "result": result, "victory": "Antaran"}
    return {"success": False, "result": result}


def end_turn(game_state):
    events = []

    # 1) Empire economy
    for owner_id in ["player", *[ai["id"] for ai in game_state.get("ai_players", [])]]:
        _compute_empire_economy(game_state, owner_id)

    # 2) Colony construction queue
    for owner_id in ["player", *[ai["id"] for ai in game_state.get("ai_players", [])]]:
        empire = get_empire(game_state, owner_id)
        for colony in empire.get("colonies", []):
            events.extend(process_colony_construction(game_state, colony))

    # 3) Research progression
    for owner_id in ["player", *[ai["id"] for ai in game_state.get("ai_players", [])]]:
        research_event = _apply_research(game_state, owner_id)
        if research_event:
            events.append(research_event)

    # 4) Fleet movement
    events.extend(process_fleet_movements(game_state))

    # 5) Space combat
    events.extend(resolve_space_combats(game_state))

    # 6) Leader pool: roll new + expire old + pay upkeep
    try:
        from app.services.leader_service import roll_available_leaders, expire_leaders, pay_upkeep
        for owner_id in ["player", *[ai["id"] for ai in game_state.get("ai_players", [])]]:
            empire = get_empire(game_state, owner_id)
            if not empire:
                continue
            res = roll_available_leaders(game_state, empire)
            if res.get("new_leader"):
                events.append({"type": "leader_offer", "owner": owner_id, "leader_id": res["new_leader"]["id"]})
            events.extend(expire_leaders(game_state, empire))
            pay_upkeep(empire)
    except Exception as e:
        events.append({"type": "leader_error", "error": str(e)})

    # 7) Per-empire AI decisions through ai-service
    ai_service = AIService()
    ai_reports = []
    for ai_player in game_state.get("ai_players", []):
        try:
            response = asyncio.run(
                ai_service.get_ai_turn(
                    {
                        "game_state": {"turn": game_state.get("turn"), "ai_player": ai_player},
                        "personality": ai_player.get("personality", "balanced"),
                        "difficulty": game_state.get("difficulty", "officer"),
                        "available_actions": _ai_actions(game_state, ai_player),
                    }
                )
            )
        except Exception as e:
            response = {"actions": [{"type": "endTurn"}], "reasoning": f"AI error: {e}"}

        applied_actions = []
        for action in response.get("actions", []):
            if action.get("type") == "endTurn":
                break
            try:
                event = _apply_ai_action(game_state, ai_player, action)
            except ValueError:
                continue
            if event:
                events.append(event)
                applied_actions.append(action)
        ai_reports.append({
            "ai_id": ai_player["id"],
            "personality": ai_player.get("personality", "balanced"),
            "actions": applied_actions,
            "reasoning": response.get("reasoning", ""),
        })

    # 8) Diplomacy maintenance
    from app.services.diplomacy_service import process_turn_diplomacy
    events.extend(process_turn_diplomacy(game_state))

    # 9) Espionage missions
    from app.services.espionage_service import process_turn_espionage
    events.extend(process_turn_espionage(game_state))

    # 10) Galactic Council
    council_event = check_galactic_council(game_state)
    if council_event:
        events.append(council_event)

    # 11) Antaran activation/attacks
    if game_state.get("antaran_attacks_enabled", True):
        if game_state["turn"] >= 50 and not game_state.get("antarans_active"):
            game_state["antarans_active"] = True
            events.append({"type": "antarans_escaped", "message": "The Antarans have escaped their pocket dimension!"})
        try:
            from app.services.antaran_service import maybe_trigger_attack
            events.extend(maybe_trigger_attack(game_state))
        except Exception as e:
            events.append({"type": "antaran_error", "error": str(e)})

    # 12) Ground assimilation tick
    try:
        from app.services.ground_combat import process_assimilation
        events.extend(process_assimilation(game_state))
    except Exception as e:
        events.append({"type": "assimilation_error", "error": str(e)})

    # 13) Space monster wandering
    try:
        from app.services.creature_service import monster_movement
        events.extend(monster_movement(game_state))
    except Exception:
        pass

    # 14) Random events
    if game_state.get("random_events_enabled", True):
        try:
            from app.services.event_service import generate_random_events
            events.extend(generate_random_events(game_state))
        except Exception as e:
            events.append({"type": "event_error", "error": str(e)})

    # 15) Victory
    victory = check_victory(game_state)
    if victory:
        events.append({"type": victory})

    # Advance turn + autosave every 4 turns
    game_state["turn"] += 1
    game_state["last_saved"] = datetime.utcnow().isoformat()
    game_state["is_autosave"] = (game_state["turn"] % 4 == 0)

    return {"game_state": game_state, "events": events, "ai_actions": ai_reports, "turn": game_state["turn"]}


def apply_cheat(game_state, cheat_code, target=None):
    cheat_code = str(cheat_code or "").lower()
    game_state.setdefault("cheats_used", []).append(cheat_code)

    if cheat_code == "recursos_infinitos":
        game_state["player"]["resources"]["bc"] = 99999
        return {"message": "Infinite resources applied", "game_state": game_state}
    if cheat_code == "revelar_galaxia":
        game_state["galaxy"]["fog_of_war"]["player"] = [system["id"] for system in game_state["galaxy"]["star_systems"]]
        return {"message": "Galaxy revealed", "game_state": game_state}
    if cheat_code == "tecnologia_total":
        for tech in TECHS.values():
            if not any(item["tech_id"] == tech["id"] for item in game_state["player"]["technologies"]["researched"]):
                game_state["player"]["technologies"]["researched"].append(
                    {"field": tech["field"], "level": tech["level"], "tech_id": tech["id"], "status": "researched"}
                )
        return {"message": "All technology unlocked", "game_state": game_state}
    if cheat_code == "flota_invencible":
        if not target or target.get("type") != "star_system" or not target.get("id"):
            raise ValueError("Target required")
        game_state["player"]["fleets"].append(
            {
                "id": "cheat_invincible",
                "name": "Invincible Fleet",
                "owner": "player",
                "star_system_id": target["id"],
                "ships": [{"type": "battleship", "count": 10}],
                "destination": None,
                "eta_turns": None,
                "command_points_used": 80,
            }
        )
        return {"message": "Invincible fleet created", "game_state": game_state}
    if cheat_code == "victoria_inmediata":
        game_state["victory_condition"] = "Conquest"
        return {"message": "Immediate victory", "game_state": game_state}
    if cheat_code == "derrota_inmediata":
        game_state["victory_condition"] = "Defeat"
        return {"message": "Immediate defeat", "game_state": game_state}
    if cheat_code == "colonizar_todo":
        if not target or target.get("type") != "star_system" or not target.get("id"):
            raise ValueError("Target required")
        system = find_system(game_state, target["id"])
        if not system:
            raise ValueError("Star system not found")
        for planet in system.get("planets", []):
            if planet.get("colonized_by") is None and PLANET_TYPES.get(planet["type"], {}).get("habitable", False):
                planet["colonized_by"] = "player"
                game_state["player"]["colonies"].append(make_colony(system["id"], planet["index"], "player", planet))
        return {"message": "System fully colonized", "game_state": game_state}
    if cheat_code == "poblacion_maxima":
        if not target or target.get("type") != "colony" or not target.get("id"):
            raise ValueError("Target required")
        colony = next((item for item in game_state["player"]["colonies"] if item["id"] == target["id"]), None)
        if not colony:
            raise ValueError("Colony not found")
        colony["population"]["total"] = colony["population"]["max"]
        _normalize_population(colony)
        return {"message": "Population maximized", "game_state": game_state}
    if cheat_code == "naves_gratis":
        game_state["player"]["resources"]["free_ship"] = True
        return {"message": "Free ships enabled", "game_state": game_state}
    if cheat_code == "guardian_eliminado":
        orion = next((system for system in game_state["galaxy"]["star_systems"] if system["name"] == "Orion"), None)
        if orion:
            orion["guardian"]["active"] = False
            orion["guardian"]["fleet"] = None
        return {"message": "Guardian removed", "game_state": game_state}
    if cheat_code == "antaranos_desactivados":
        game_state["antaran_next_attack_turn"] = None
        return {"message": "Antarans disabled", "game_state": game_state}
    if cheat_code == "rushbuy":
        for colony in game_state["player"].get("colonies", []):
            if colony.get("build_queue"):
                colony["build_queue"][0]["progress"] = colony["build_queue"][0]["cost"]
        return {"message": "First queue item completed", "game_state": game_state}
    if cheat_code == "crunch":
        for colony in game_state["player"].get("colonies", []):
            for item in colony.get("build_queue", []):
                item["progress"] = item["cost"]
        return {"message": "All queue items completed", "game_state": game_state}
    raise ValueError("Invalid cheat code")


def list_scenarios():
    return SCENARIOS


def get_galaxy_view(game_state):
    visible = set(game_state["galaxy"]["fog_of_war"].get("player", []))
    player_colonies = {colony["star_system_id"] for colony in game_state["player"].get("colonies", [])}
    player_fleets = {
        fleet["star_system_id"] for fleet in game_state["player"].get("fleets", []) if fleet.get("destination") is None
    }
    return {
        "star_systems": [
            {
                "id": system["id"],
                "name": system["name"] if system["id"] in visible else "Unknown System",
                "position": system["position"],
                "star_type": system["star_type"] if system["id"] in visible else "unknown",
                "explored": system["id"] in visible,
                "planets": system["planets"] if system["id"] in visible else [],
                "connections": [connection for connection in system.get("connections", []) if connection in visible],
                "has_player_colony": system["id"] in player_colonies,
                "has_player_fleet": system["id"] in player_fleets,
                "has_enemy_fleet": system["id"] in visible
                and any(
                    fleet["star_system_id"] == system["id"] and fleet.get("destination") is None
                    for ai in game_state.get("ai_players", [])
                    for fleet in ai.get("fleets", [])
                ),
            }
            for system in game_state["galaxy"]["star_systems"]
        ]
    }


def ground_assault(game_state, owner_id, fleet_id, colony_id):
    fleet = find_fleet(game_state, owner_id, fleet_id)
    if not fleet:
        raise ValueError("Fleet not found")
    target_colony = None
    target_owner = None
    for candidate_owner in ["player", *[ai["id"] for ai in game_state.get("ai_players", [])]]:
        empire = get_empire(game_state, candidate_owner)
        colony = next((item for item in empire.get("colonies", []) if item["id"] == colony_id), None) if empire else None
        if colony:
            target_colony = colony
            target_owner = candidate_owner
            break
    if not target_colony:
        raise ValueError("Colony not found")
    if target_owner == owner_id:
        raise ValueError("Cannot assault your own colony")

    transport = next((ship for ship in fleet.get("ships", []) if ship["type"] == "transport" and ship.get("count", 0) > 0), None)
    if not transport:
        raise ValueError("Fleet has no transports")
    if target_colony["star_system_id"] != fleet["star_system_id"]:
        raise ValueError("Fleet not in colony system")

    attacker_bonus = get_empire(game_state, owner_id)["race"]["traits"].get("ground_combat_bonus", 0)
    defender_bonus = get_empire(game_state, target_owner)["race"]["traits"].get("ground_combat_bonus", 0)
    result = resolve_ground_combat(transport["count"], attacker_bonus, target_colony, defender_bonus)
    if result["winner"] == "attacker":
        get_empire(game_state, target_owner)["colonies"] = [
            item for item in get_empire(game_state, target_owner).get("colonies", []) if item["id"] != target_colony["id"]
        ]
        target_colony["owner"] = owner_id
        target_colony["population"]["total"] = max(1, int(target_colony["population"]["total"] * 0.5))
        target_colony["morale"] = "unrest"
        get_empire(game_state, owner_id)["colonies"].append(target_colony)
        _normalize_population(target_colony)

    transport["count"] = 0
    fleet["ships"] = [ship for ship in fleet["ships"] if ship.get("count", 0) > 0]
    fleet["command_points_used"] = _fleet_command_points(fleet)
    return {"result": result, "colony_captured": result["winner"] == "attacker", "fleet": fleet, "colony": target_colony}


def get_colony_detail(game_state, colony_id):
    colony = next((item for item in game_state["player"].get("colonies", []) if item["id"] == colony_id), None)
    if not colony:
        raise ValueError("Colony not found")
    _normalize_population(colony)
    calculate_colony_production(game_state, colony)
    return {
        "colony": colony,
        "available_buildings": get_available_buildings(game_state, colony),
        "available_ships": get_available_ships(game_state, colony),
    }


def get_tech_tree(game_state):
    technologies = game_state["player"]["technologies"]
    researched = {item["tech_id"] for item in technologies.get("researched", []) if item.get("status") != "discarded"}
    discarded = {item["tech_id"] for item in technologies.get("researched", []) if item.get("status") == "discarded"}
    current = technologies.get("current_research")
    fields = {}
    for tech in TECHS.values():
        fields.setdefault(tech["field"], []).append(tech)

    response = []
    for field_name, techs in fields.items():
        levels = {}
        for tech in sorted(techs, key=lambda item: (item["level"], item["id"])):
            if current and current["tech_id"] == tech["id"]:
                status = "current"
            elif tech["id"] in researched:
                status = "researched"
            elif tech["id"] in discarded:
                status = "discarded"
            elif tech["level"] > 1 and not any(
                item["field"] == tech["field"] and item["level"] == tech["level"] - 1 and item.get("status") != "discarded"
                for item in technologies.get("researched", [])
            ):
                status = "locked"
            elif any(
                item["field"] == tech["field"] and item["level"] == tech["level"] and item.get("status") != "discarded"
                for item in technologies.get("researched", [])
            ):
                status = "locked"
            else:
                status = "available"
            levels.setdefault(tech["level"], []).append(
                {
                    "tech_id": tech["id"],
                    "name": tech["name"],
                    "description": tech.get("description", ""),
                    "research_cost": tech["research_cost"],
                    "status": status,
                    "field": tech["field"],
                    "level": tech["level"],
                    "unlocks": tech.get("unlocks", {}),
                }
            )
        response.append({"field": field_name, "levels": [{"level": level, "options": levels[level]} for level in sorted(levels)]})
    return {"fields": response, "current_research": current}
