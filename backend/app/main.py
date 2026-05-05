import asyncio
import random

from flask import Flask, g, jsonify, request
from flask_cors import CORS

from app.auth.jwt_handler import create_token
from app.auth.middleware import token_required
from app.auth.password import hash_password, verify_password
from app.db.game_repo import create_game, delete_game, get_game, list_games, save_game, get_top_hall_of_fame, add_to_hall_of_fame
from app.db.user_repo import create_user, get_by_email, get_by_id, get_by_username, update_last_login
from app.errors import ValidationError
from app.services.ai_service import AIService
from app.services.colony_service import (

    BUILDINGS,
    add_to_build_queue,
    calculate_colony_production,
    cancel_build_queue_item,
    get_available_ships,
    has_technology,
    reorder_build_queue as reorder_queue,
)
from app.services.diplomacy_service import (
    declare_war,
    get_intelligence,
    initialize_diplomacy,
    list_relations,
    make_demand,
    make_gift,
    open_dialogue,
    propose_treaty,
    trade_tech,
)
from app.services.game_service import (
    SHIP_TYPES,
    apply_cheat,
    attack_antaran_homeworld,
    build_dimensional_portal,
    colonize_planet,
    defeat_orion_guardian,
    end_turn,
    find_fleet,
    generate_game_state,
    get_colony_detail,
    get_galaxy_view,
    get_tech_tree,
    list_scenarios,
    move_fleet,
    set_research,
)
from app.services.combat_service import (
    SPACE_MONSTERS,
    mind_control_colony,
    resolve_combat_against_monster,
)
from app.services.espionage_service import (
    SPY_LEVELS,
    MISSION_TYPES,
    assign_defense,
    assign_mission,
    list_spies,
    recruit_spy,
)
from app.services.leader_service import (
    get_hired_leaders, get_available_leaders, hire_leader, assign_leader, unassign_leader
)
from app.validation import (

    validate_difficulty,
    validate_email,
    validate_game_name,
    validate_number_range,
    validate_password,
    validate_username,
)


app = Flask(__name__)
CORS(app)


def _game_entry_or_error(game_id):
    entry = get_game(g.user_id, game_id)
    if entry == "forbidden":
        return None, (jsonify({"error": "This game does not belong to you"}), 403)
    if not entry:
        return None, (jsonify({"error": "Game not found"}), 404)
    return entry, None


def _player_colony(game_state, colony_id):
    return next((colony for colony in game_state["player"].get("colonies", []) if colony["id"] == colony_id), None)


def _player_fleet(game_state, fleet_id):
    return find_fleet(game_state, "player", fleet_id)




def _build_basic_ai_actions(game_state, ai_player):
    available_actions = {
        "can_colonize": [],
        "can_research": [],
        "available_buildings": {},
        "available_ships": {},
        "can_move": [],
    }

    for fleet in ai_player.get("fleets", []):
        if fleet.get("destination") is not None:
            continue
        colony_ship = next(
            (ship for ship in fleet.get("ships", []) if ship["type"] == "colony_ship" and ship.get("count", 0) > 0),
            None,
        )
        if colony_ship:
            available_actions["can_colonize"].append(
                {"fleetId": fleet["id"], "planetIndex": 0, "systemId": fleet["star_system_id"]}
            )

    if ai_player.get("technologies", {}).get("current_research") is None:
        available_actions["can_research"] = [
            {"id": "construction_1", "field": "construction", "level": 1}
        ]

    for colony in ai_player.get("colonies", []):
        available_actions["available_ships"][colony["id"]] = get_available_ships(game_state, colony)

    return available_actions


@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    try:
        username = validate_username(data.get("username", ""))
        email = validate_email(data.get("email", ""))
        password = validate_password(data.get("password", ""))
    except ValidationError as err:
        return jsonify({"error": err.message}), 400

    if get_by_username(username):
        return jsonify({"error": "Username already exists"}), 400
    if get_by_email(email):
        return jsonify({"error": "Email already registered"}), 400

    password_hash = hash_password(password)
    user = create_user(username, email, password_hash)
    token = create_token(str(user["_id"]))
    return jsonify({"user_id": str(user["_id"]), "username": username, "token": token}), 201


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username", "")
    password = data.get("password", "")

    user = get_by_username(username)
    if not user or not verify_password(password, user["password_hash"]):
        return jsonify({"error": "Invalid credentials"}), 401

    update_last_login(str(user["_id"]))
    token = create_token(str(user["_id"]))
    return jsonify({"user_id": str(user["_id"]), "username": user["username"], "token": token})


@app.route("/api/auth/profile", methods=["GET"])
@token_required
def profile():
    user = get_by_id(g.user_id)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    return jsonify(
        {
            "user_id": str(user["_id"]),
            "username": user["username"],
            "email": user["email"],
            "created_at": user["created_at"],
            "games_played": user.get("games_played", 0),
            "games_won": user.get("games_won", 0),
        }
    )


@app.route("/api/games", methods=["GET"])
@app.route("/api/game", methods=["GET"])
@token_required
def games_list():
    return jsonify({"games": list_games(g.user_id)})


@app.route("/api/games", methods=["POST"])
@app.route("/api/game", methods=["POST"])
@token_required
def create_game_route():
    data = request.get_json() or {}
    scenario_config = data.get("scenario_config", {})

    try:
        name = validate_game_name(data.get("name", "New Game"))
        galaxy_size = scenario_config.get("galaxy_size")
        if galaxy_size not in ["small", "medium", "large"]:
            raise ValidationError("Galaxy size must be one of: small, medium, large")
        num_opponents = validate_number_range(scenario_config.get("num_opponents", 1), 1, 3, "num_opponents")
        difficulty = validate_difficulty(scenario_config.get("difficulty"))
    except ValidationError as err:
        return jsonify({"error": err.message}), 400

    player_race = scenario_config.get("player_race")
    if not player_race or not isinstance(player_race, str):
        return jsonify({"error": "Player race required"}), 400

    scenario_config["galaxy_size"] = galaxy_size
    scenario_config["num_opponents"] = num_opponents
    scenario_config["difficulty"] = difficulty
    scenario_config["player_race"] = player_race

    game_state = generate_game_state(name, scenario_config)
    game_id = create_game(g.user_id, name, scenario_config.get("scenario_id", "default"), game_state)
    game_state["game_id"] = game_id
    save_game(g.user_id, game_id, game_state)
    return jsonify({"game_id": game_id, "game_state": game_state}), 201


@app.route("/api/games/<game_id>", methods=["GET"])
@app.route("/api/game/<game_id>", methods=["GET"])
@token_required
def load_game(game_id):
    entry, error = _game_entry_or_error(game_id)
    if error:
        return error

    game_state = entry["game_state"]
    game_state["game_id"] = game_id
    return jsonify({"game_id": game_id, "game_state": game_state})


@app.route("/api/games/<game_id>/save", methods=["POST"])
@token_required
def save_game_route(game_id):
    entry, error = _game_entry_or_error(game_id)
    if error:
        return error

    data = request.get_json() or {}
    name = data.get("name")
    if name is not None:
        try:
            name = validate_game_name(name)
        except ValidationError as err:
            return jsonify({"error": err.message}), 400

    success = save_game(g.user_id, game_id, entry["game_state"], name=name)
    if not success:
        return jsonify({"error": "Failed to save game"}), 500
    return jsonify({"success": True, "last_saved": entry["game_state"].get("last_saved")})


@app.route("/api/games/<game_id>", methods=["DELETE"])
@app.route("/api/game/<game_id>", methods=["DELETE"])
@token_required
def delete_game_route(game_id):
    return jsonify({"success": delete_game(g.user_id, game_id)})


@app.route("/api/games/<game_id>/colony/<colony_id>/manage", methods=["POST"])
@token_required
def manage_colony(game_id, colony_id):
    entry, error = _game_entry_or_error(game_id)
    if error:
        return error

    game_state = entry["game_state"]
    colony = _player_colony(game_state, colony_id)
    if not colony:
        return jsonify({"error": "Colony not found"}), 404

    data = request.get_json() or {}
    warnings = []
    population = data.get("population", {})
    if population:
        try:
            farmers = int(population.get("farmers", colony["population"]["farmers"]))
            workers = int(population.get("workers", colony["population"]["workers"]))
            scientists = int(population.get("scientists", colony["population"]["scientists"]))
        except (TypeError, ValueError):
            return jsonify({"error": "Population values must be integers"}), 400

        total = colony["population"]["total"]
        if farmers < 0 or workers < 0 or scientists < 0:
            return jsonify({"error": "Population values cannot be negative"}), 400
        if farmers + workers + scientists != total:
            return jsonify({"error": "Population assignment does not match total"}), 400

        colony["population"]["farmers"] = farmers
        colony["population"]["workers"] = workers
        colony["population"]["scientists"] = scientists

    calculate_colony_production(game_state, colony)
    if colony.get("food_surplus", 0) < 0:
        warnings.append("Food deficit: population will decrease next turn")
    if colony.get("food_surplus", 0) < 2:
        warnings.append("Low food reserves: maintain surplus above 2")
    if colony.get("industry_output", 0) == 0 and not colony.get("build_queue"):
        warnings.append("No construction in progress: production goes to trade goods")

    save_game(g.user_id, game_id, game_state)
    return jsonify({"colony": colony, "validation_warnings": warnings})


@app.route("/api/games/<game_id>/research", methods=["POST"])
@token_required
def research_route(game_id):
    entry, error = _game_entry_or_error(game_id)
    if error:
        return error

    data = request.get_json() or {}
    try:
        field = data.get("field")
        level = int(data.get("level"))
        tech_id = data.get("tech_id")
        result = set_research(entry["game_state"], field, level, tech_id)
        save_game(g.user_id, game_id, entry["game_state"])
        return jsonify(result)
    except (TypeError, ValueError) as err:
        return jsonify({"error": str(err)}), 400


@app.route("/api/games/<game_id>/fleet/<fleet_id>/move", methods=["POST"])
@token_required
def fleet_move_route(game_id, fleet_id):
    entry, error = _game_entry_or_error(game_id)
    if error:
        return error

    data = request.get_json() or {}
    destination = data.get("destination")
    try:
        result = move_fleet(entry["game_state"], "player", fleet_id, destination)
        save_game(g.user_id, game_id, entry["game_state"])
        return jsonify(result)
    except ValueError as err:
        return jsonify({"error": str(err)}), 400


@app.route("/api/games/<game_id>/fleet/<fleet_id>/split", methods=["POST"])
@token_required
def fleet_split_route(game_id, fleet_id):
    entry, error = _game_entry_or_error(game_id)
    if error:
        return error

    data = request.get_json() or {}
    ships_to_split = data.get("ships", [])
    game_state = entry["game_state"]
    fleet = _player_fleet(game_state, fleet_id)
    if not fleet:
        return jsonify({"error": "Fleet not found"}), 404
    if fleet.get("destination") is not None:
        return jsonify({"error": "Cannot split fleet while in transit"}), 400
    if not isinstance(ships_to_split, list) or not ships_to_split:
        return jsonify({"error": "Ships payload is required"}), 400

    try:
        new_fleet = {
            "id": f"{fleet_id}_split_{random.randint(1000, 9999)}",
            "name": f"{fleet['name']} (Split)",
            "owner": "player",
            "star_system_id": fleet["star_system_id"],
            "ships": [],
            "destination": None,
            "eta_turns": None,
            "command_points_used": 0,
        }

        for split_ship in ships_to_split:
            ship_type = split_ship.get("type")
            count = int(split_ship.get("count", 1))
            if not ship_type or count <= 0:
                raise ValueError("Invalid ship split request")
            existing = next((item for item in fleet["ships"] if item["type"] == ship_type), None)
            if not existing or existing["count"] < count:
                raise ValueError(f"Not enough {ship_type} ships to split")

        for split_ship in ships_to_split:
            ship_type = split_ship["type"]
            count = int(split_ship.get("count", 1))
            existing = next((item for item in fleet["ships"] if item["type"] == ship_type), None)
            existing["count"] -= count
            new_fleet["ships"].append({"type": ship_type, "count": count})

        fleet["ships"] = [item for item in fleet["ships"] if item["count"] > 0]
        fleet["command_points_used"] = sum(
            SHIP_TYPES.get(item["type"], {}).get("command_points", 0) * item.get("count", 0)
            for item in fleet["ships"]
        )
        new_fleet["command_points_used"] = sum(
            SHIP_TYPES.get(item["type"], {}).get("command_points", 0) * item.get("count", 0)
            for item in new_fleet["ships"]
        )

        game_state["player"]["fleets"].append(new_fleet)
        save_game(g.user_id, game_id, game_state)
        return jsonify({"original_fleet": fleet, "new_fleet": new_fleet})
    except (TypeError, ValueError) as err:
        return jsonify({"error": str(err)}), 400


@app.route("/api/games/<game_id>/colonize", methods=["POST"])
@token_required
def colonize_route(game_id):
    entry, error = _game_entry_or_error(game_id)
    if error:
        return error

    data = request.get_json() or {}
    try:
        planet_index = int(data.get("planet_index"))
        result = colonize_planet(entry["game_state"], "player", data.get("fleet_id"), planet_index)
        save_game(g.user_id, game_id, entry["game_state"])
        return jsonify(result)
    except (TypeError, ValueError) as err:
        return jsonify({"error": str(err)}), 400


@app.route("/api/games/<game_id>/endTurn", methods=["POST"])
@app.route("/api/game/<game_id>/endTurn", methods=["POST"])
@token_required
def end_turn_route(game_id):
    entry, error = _game_entry_or_error(game_id)
    if error:
        return error

    result = end_turn(entry["game_state"])
    save_game(g.user_id, game_id, result["game_state"], autosave=True)
    return jsonify(result)


@app.route("/api/games/<game_id>/ai-turn", methods=["POST"])
@token_required
def ai_turn_route(game_id):
    entry, error = _game_entry_or_error(game_id)
    if error:
        return error

    data = request.get_json() or {}
    ai_id = data.get("ai_id", "ai_0")
    game_state = entry["game_state"]
    ai_player = next((item for item in game_state.get("ai_players", []) if item.get("id") == ai_id), None)
    if not ai_player:
        return jsonify({"error": "AI player not found"}), 404

    ai_service = AIService()
    request_payload = {
        "game_state": {"turn": game_state.get("turn"), "ai_player": ai_player},
        "personality": ai_player.get("personality", "balanced"),
        "difficulty": game_state.get("difficulty", "normal"),
        "available_actions": _build_basic_ai_actions(game_state, ai_player),
    }
    return jsonify(asyncio.run(ai_service.get_ai_turn(request_payload)))


@app.route("/api/games/<game_id>/cheat", methods=["POST"])
@token_required
def cheat_route(game_id):
    entry, error = _game_entry_or_error(game_id)
    if error:
        return error

    data = request.get_json() or {}
    try:
        result = apply_cheat(entry["game_state"], data.get("cheat_code"), data.get("target"))
        save_game(g.user_id, game_id, entry["game_state"])
        return jsonify({"success": True, "message": result["message"], "game_state": result["game_state"]})
    except ValueError as err:
        return jsonify({"error": str(err)}), 400


@app.route("/api/games/<game_id>/galaxy", methods=["GET"])
@app.route("/api/game/<game_id>/galaxy", methods=["GET"])
@token_required
def galaxy_route(game_id):
    entry, error = _game_entry_or_error(game_id)
    if error:
        return error
    return jsonify(get_galaxy_view(entry["game_state"]))


@app.route("/api/games/<game_id>/tech-tree", methods=["GET"])
@app.route("/api/game/<game_id>/tech-tree", methods=["GET"])
@token_required
def tech_tree_route(game_id):
    entry, error = _game_entry_or_error(game_id)
    if error:
        return error
    return jsonify(get_tech_tree(entry["game_state"]))


@app.route("/api/games/<game_id>/colony/<colony_id>", methods=["GET"])
@app.route("/api/game/<game_id>/colony/<colony_id>", methods=["GET"])
@token_required
def colony_detail_route(game_id, colony_id):
    entry, error = _game_entry_or_error(game_id)
    if error:
        return error

    try:
        return jsonify(get_colony_detail(entry["game_state"], colony_id))
    except ValueError as err:
        return jsonify({"error": str(err)}), 404


@app.route("/api/games/<game_id>/colony/<colony_id>/build-queue/add", methods=["POST"])
@app.route("/api/game/<game_id>/colony/<colony_id>/build-queue/add", methods=["POST"])
@token_required
def add_build_queue_item(game_id, colony_id):
    entry, error = _game_entry_or_error(game_id)
    if error:
        return error

    game_state = entry["game_state"]
    colony = _player_colony(game_state, colony_id)
    if not colony:
        return jsonify({"error": "Colony not found"}), 404

    data = request.get_json() or {}
    item_type = data.get("type")
    item_id = data.get("id")
    if not item_type or not item_id:
        return jsonify({"error": "Missing type or id"}), 400

    try:
        if len(colony.get("build_queue", [])) >= 7:
            raise ValueError("Build queue is full (max 7 items)")

        if item_type == "building":
            if item_id not in BUILDINGS:
                raise ValueError("Unknown building")
            if any(building["id"] == item_id for building in colony.get("buildings", [])):
                raise ValueError(f"Building '{BUILDINGS[item_id]['name']}' already built in this colony.")
            if any(item["id"] == item_id and item["type"] == "building" for item in colony.get("build_queue", [])):
                raise ValueError(f"Building '{BUILDINGS[item_id]['name']}' already in build queue.")

            tech_reqs = BUILDINGS[item_id].get("prerequisites", {}).get("tech", [])
            if tech_reqs and not all(has_technology(game_state["player"]["technologies"], tech) for tech in tech_reqs):
                raise ValueError(f"Technological prerequisites not met for '{BUILDINGS[item_id]['name']}'.")

            building_reqs = BUILDINGS[item_id].get("prerequisites", {}).get("buildings", [])
            built_ids = {building["id"] for building in colony.get("buildings", [])}
            if building_reqs and not all(req in built_ids for req in building_reqs):
                raise ValueError(f"Building prerequisites not met for '{BUILDINGS[item_id]['name']}'.")

            cost = BUILDINGS[item_id]["cost"]
        elif item_type == "ship":
            available_ships = get_available_ships(game_state, colony)
            ship = next((item for item in available_ships if item["type"] == item_id), None)
            if not ship:
                raise ValueError("Unknown ship or not available based on current technology/buildings.")
            cost = ship["cost"]
        else:
            raise ValueError("Invalid item type")

        queue_item = add_to_build_queue(colony, item_type, item_id, cost)
        save_game(g.user_id, game_id, game_state)
        return jsonify({"queue_item": queue_item, "queue": colony["build_queue"]})
    except ValueError as err:
        return jsonify({"error": str(err)}), 400


@app.route("/api/games/<game_id>/colony/<colony_id>/build-queue/remove", methods=["POST"])
@app.route("/api/game/<game_id>/colony/<colony_id>/build-queue/remove", methods=["POST"])
@token_required
def remove_build_queue_item(game_id, colony_id):
    entry, error = _game_entry_or_error(game_id)
    if error:
        return error

    game_state = entry["game_state"]
    colony = _player_colony(game_state, colony_id)
    if not colony:
        return jsonify({"error": "Colony not found"}), 404

    data = request.get_json() or {}
    try:
        index = int(data.get("index"))
        cancel_build_queue_item(colony, index)
        save_game(g.user_id, game_id, game_state)
        return jsonify({"queue": colony["build_queue"]})
    except (TypeError, ValueError) as err:
        return jsonify({"error": str(err)}), 400


@app.route("/api/games/<game_id>/colony/<colony_id>/build-queue/reorder", methods=["POST"])
@app.route("/api/game/<game_id>/colony/<colony_id>/build-queue/reorder", methods=["POST"])
@token_required
def reorder_build_queue(game_id, colony_id):
    entry, error = _game_entry_or_error(game_id)
    if error:
        return error

    game_state = entry["game_state"]
    colony = _player_colony(game_state, colony_id)
    if not colony:
        return jsonify({"error": "Colony not found"}), 404

    data = request.get_json() or {}
    try:
        from_index = int(data.get("from"))
        to_index = int(data.get("to"))
        reorder_queue(colony, from_index, to_index)
        save_game(g.user_id, game_id, game_state)
        return jsonify({"queue": colony["build_queue"]})
    except (TypeError, ValueError) as err:
        return jsonify({"error": str(err)}), 400


@app.route("/api/games/<game_id>/diplomacy", methods=["GET"])
@app.route("/api/game/<game_id>/diplomacy", methods=["GET"])
@token_required
def diplomacy_status_route(game_id):
    entry, error = _game_entry_or_error(game_id)
    if error:
        return error
    initialize_diplomacy(entry["game_state"])
    return jsonify(entry["game_state"]["diplomacy"])


@app.route("/api/games/<game_id>/diplomacy/propose", methods=["POST"])
@app.route("/api/game/<game_id>/diplomacy/propose", methods=["POST"])
@token_required
def propose_treaty_route(game_id):
    entry, error = _game_entry_or_error(game_id)
    if error:
        return error

    data = request.get_json() or {}
    target = data.get("target")
    treaty_type = data.get("treaty_type")
    if not target or not isinstance(target, str):
        return jsonify({"error": "Missing required field 'target'"}), 400
    if not treaty_type or not isinstance(treaty_type, str):
        return jsonify({"error": "Missing required field 'treaty_type'"}), 400

    try:
        result = propose_treaty(entry["game_state"], "player", target, treaty_type)
        save_game(g.user_id, game_id, entry["game_state"])
        return jsonify(result)
    except ValueError as err:
        return jsonify({"error": str(err)}), 400


@app.route("/api/games/<game_id>/diplomacy/war", methods=["POST"])
@app.route("/api/game/<game_id>/diplomacy/war", methods=["POST"])
@token_required
def declare_war_route(game_id):
    entry, error = _game_entry_or_error(game_id)
    if error:
        return error

    data = request.get_json() or {}
    target = data.get("target")
    if not target or not isinstance(target, str):
        return jsonify({"error": "Missing required field 'target'"}), 400

    try:
        result = declare_war(entry["game_state"], "player", target)
        save_game(g.user_id, game_id, entry["game_state"])
        return jsonify(result)
    except ValueError as err:
        return jsonify({"error": str(err)}), 400


# ─── Diplomacy: Tech trade (DIPLOMACY sec 3) ─────────────────────────
@app.route("/api/games/<game_id>/diplomacy/trade-tech", methods=["POST"])
@app.route("/api/game/<game_id>/diplomacy/trade-tech", methods=["POST"])
@token_required
def trade_tech_route(game_id):
    entry, error = _game_entry_or_error(game_id)
    if error:
        return error
    data = request.get_json() or {}
    target = data.get("target")
    offered = data.get("offered_tech")
    requested = data.get("requested_tech")
    if not all([target, offered, requested]):
        return jsonify({"error": "Missing target, offered_tech or requested_tech"}), 400
    result = trade_tech(entry["game_state"], "player", target, offered, requested)
    save_game(g.user_id, game_id, entry["game_state"])
    return jsonify(result)


# ─── Diplomacy: Gifts (DIPLOMACY sec 8) ──────────────────────────────
@app.route("/api/games/<game_id>/diplomacy/gift", methods=["POST"])
@app.route("/api/game/<game_id>/diplomacy/gift", methods=["POST"])
@token_required
def gift_route(game_id):
    entry, error = _game_entry_or_error(game_id)
    if error:
        return error
    data = request.get_json() or {}
    target = data.get("target")
    gift_type = data.get("gift_type")
    if not target or not gift_type:
        return jsonify({"error": "Missing target or gift_type"}), 400
    result = make_gift(
        entry["game_state"], "player", target, gift_type,
        amount=data.get("amount"), tech_id=data.get("tech_id"),
    )
    save_game(g.user_id, game_id, entry["game_state"])
    return jsonify(result)


# ─── Diplomacy: Demands (DIPLOMACY sec 7 & 12) ────────────────────────
@app.route("/api/games/<game_id>/diplomacy/demand", methods=["POST"])
@app.route("/api/game/<game_id>/diplomacy/demand", methods=["POST"])
@token_required
def demand_route(game_id):
    entry, error = _game_entry_or_error(game_id)
    if error:
        return error
    data = request.get_json() or {}
    target = data.get("target")
    demand_type = data.get("demand_type")
    if not target or not demand_type:
        return jsonify({"error": "Missing target or demand_type"}), 400
    result = make_demand(
        entry["game_state"], "player", target, demand_type,
        payload=data.get("payload"),
    )
    save_game(g.user_id, game_id, entry["game_state"])
    return jsonify(result)


# ─── Diplomacy: Scouting / Intelligence (DIPLOMACY sec 14) ────────────
@app.route("/api/games/<game_id>/diplomacy/intelligence/<target>", methods=["GET"])
@app.route("/api/game/<game_id>/diplomacy/intelligence/<target>", methods=["GET"])
@token_required
def intelligence_route(game_id, target):
    entry, error = _game_entry_or_error(game_id)
    if error:
        return error
    result = get_intelligence(entry["game_state"], "player", target)
    save_game(g.user_id, game_id, entry["game_state"])
    return jsonify(result)


@app.route("/api/games/<game_id>/diplomacy/dialogue/<target>", methods=["POST"])
@app.route("/api/game/<game_id>/diplomacy/dialogue/<target>", methods=["POST"])
@token_required
def open_dialogue_route(game_id, target):
    entry, error = _game_entry_or_error(game_id)
    if error:
        return error
    result = open_dialogue(entry["game_state"], "player", target)
    save_game(g.user_id, game_id, entry["game_state"])
    return jsonify(result)


@app.route("/api/games/<game_id>/diplomacy/relations", methods=["GET"])
@app.route("/api/game/<game_id>/diplomacy/relations", methods=["GET"])
@token_required
def relations_list_route(game_id):
    entry, error = _game_entry_or_error(game_id)
    if error:
        return error
    return jsonify({"relations": list_relations(entry["game_state"], "player")})


# ─── Combat: Mind Control (PLAN sec 4) ────────────────────────────────
@app.route("/api/games/<game_id>/combat/mind-control", methods=["POST"])
@app.route("/api/game/<game_id>/combat/mind-control", methods=["POST"])
@token_required
def mind_control_route(game_id):
    entry, error = _game_entry_or_error(game_id)
    if error:
        return error
    data = request.get_json() or {}
    colony_id = data.get("colony_id")
    if not colony_id:
        return jsonify({"error": "Missing colony_id"}), 400
    result = mind_control_colony(entry["game_state"], "player", colony_id)
    save_game(g.user_id, game_id, entry["game_state"])
    return jsonify(result)


# ─── Combat: Space Monsters (PLAN sec 18) ─────────────────────────────
@app.route("/api/games/<game_id>/combat/monster", methods=["POST"])
@app.route("/api/game/<game_id>/combat/monster", methods=["POST"])
@token_required
def fight_monster_route(game_id):
    entry, error = _game_entry_or_error(game_id)
    if error:
        return error
    data = request.get_json() or {}
    fleet_id = data.get("fleet_id")
    system_id = data.get("system_id")
    if not fleet_id or not system_id:
        return jsonify({"error": "Missing fleet_id or system_id"}), 400

    state = entry["game_state"]
    fleet = _player_fleet(state, fleet_id)
    if not fleet:
        return jsonify({"error": "Fleet not found"}), 404

    system = next((s for s in state["galaxy"]["star_systems"] if s["id"] == system_id), None)
    if not system or not system.get("space_monster") or system["space_monster"].get("defeated"):
        return jsonify({"error": "No space monster at that system"}), 400

    monster = system["space_monster"]
    result = resolve_combat_against_monster(fleet, monster["type"], monster.get("is_travelling", False), SHIP_TYPES)
    if result.get("winner") == "attacker":
        monster["defeated"] = True
    save_game(g.user_id, game_id, entry["game_state"])
    return jsonify(result)


@app.route("/api/games/<game_id>/space-monsters", methods=["GET"])
@app.route("/api/game/<game_id>/space-monsters", methods=["GET"])
@token_required
def list_monsters_route(game_id):
    entry, error = _game_entry_or_error(game_id)
    if error:
        return error
    state = entry["game_state"]
    monsters = []
    for system in state["galaxy"]["star_systems"]:
        m = system.get("space_monster")
        if m and not m.get("defeated"):
            monsters.append({
                "system_id": system["id"],
                "system_name": system.get("name"),
                "monster_type": m["type"],
                "is_travelling": m.get("is_travelling", False),
                "tactic_hint": SPACE_MONSTERS[m["type"]]["tactic_hint"],
            })
    return jsonify({"monsters": monsters, "catalog": SPACE_MONSTERS})


# ─── Antarans & Orion (PLAN sec 19 & 20) ──────────────────────────────
@app.route("/api/games/<game_id>/orion/defeat-guardian", methods=["POST"])
@app.route("/api/game/<game_id>/orion/defeat-guardian", methods=["POST"])
@token_required
def defeat_guardian_route(game_id):
    entry, error = _game_entry_or_error(game_id)
    if error:
        return error
    result = defeat_orion_guardian(entry["game_state"], "player")
    save_game(g.user_id, game_id, entry["game_state"])
    return jsonify(result)


@app.route("/api/games/<game_id>/antaran/build-portal", methods=["POST"])
@app.route("/api/game/<game_id>/antaran/build-portal", methods=["POST"])
@token_required
def build_portal_route(game_id):
    entry, error = _game_entry_or_error(game_id)
    if error:
        return error
    data = request.get_json() or {}
    result = build_dimensional_portal(entry["game_state"], "player", colony_id=data.get("colony_id"))
    save_game(g.user_id, game_id, entry["game_state"])
    return jsonify(result)


@app.route("/api/games/<game_id>/antaran/assault", methods=["POST"])
@app.route("/api/game/<game_id>/antaran/assault", methods=["POST"])
@token_required
def antaran_assault_route(game_id):
    entry, error = _game_entry_or_error(game_id)
    if error:
        return error
    data = request.get_json() or {}
    fleet_id = data.get("fleet_id")
    if not fleet_id:
        return jsonify({"error": "Missing fleet_id"}), 400
    result = attack_antaran_homeworld(entry["game_state"], "player", fleet_id)
    save_game(g.user_id, game_id, entry["game_state"])
    return jsonify(result)


# ─── Espionage: Spy levels & defense (DIPLOMACY sec 9) ────────────────
@app.route("/api/games/<game_id>/espionage/levels", methods=["GET"])
@app.route("/api/game/<game_id>/espionage/levels", methods=["GET"])
@token_required
def espionage_levels_route(game_id):
    return jsonify({"levels": SPY_LEVELS, "missions": MISSION_TYPES})


@app.route("/api/games/<game_id>/espionage/defense", methods=["POST"])
@app.route("/api/game/<game_id>/espionage/defense", methods=["POST"])
@token_required
def espionage_defense_route(game_id):
    entry, error = _game_entry_or_error(game_id)
    if error:
        return error
    data = request.get_json() or {}
    spy_id = data.get("spy_id")
    if not spy_id:
        return jsonify({"error": "Missing spy_id"}), 400
    result, code = assign_defense(entry["game_state"], "player", spy_id)
    save_game(g.user_id, game_id, entry["game_state"])
    return jsonify(result), code


@app.route("/api/scenarios", methods=["GET"])
def scenarios_route():
    return jsonify({"scenarios": list_scenarios()})


@app.route("/api/games/<game_id>/status", methods=["GET"])
@app.route("/api/game/<game_id>/status", methods=["GET"])
@token_required
def game_status_route(game_id):
    entry, error = _game_entry_or_error(game_id)
    if error:
        return error

    game_state = entry["game_state"]
    player = game_state["player"]
    return jsonify(
        {
            "turn": game_state["turn"],
            "player_race": player["race"]["id"],
            "victory_condition": game_state.get("victory_condition"),
            "resources": player["resources"],
            "colonies_count": len(player.get("colonies", [])),
            "fleets_count": len(player.get("fleets", [])),
            "total_population": sum(colony["population"]["total"] for colony in player.get("colonies", [])),
            "technologies_researched": len(
                [tech for tech in player["technologies"].get("researched", []) if tech.get("status") != "discarded"]
            ),
            "current_research": player["technologies"].get("current_research"),
            "ai_players": [
                {
                    "id": ai["id"],
                    "race": ai["race"]["id"],
                    "personality": ai.get("personality", "balanced"),
                    "colonies_count": len(ai.get("colonies", [])),
                    "fleets_count": len(ai.get("fleets", [])),
                }
                for ai in game_state.get("ai_players", [])
            ],
        }
    )


@app.route("/api/games/<game_id>/fleets", methods=["GET"])
@app.route("/api/game/<game_id>/fleets", methods=["GET"])
@token_required
def list_fleets_route(game_id):
    entry, error = _game_entry_or_error(game_id)
    if error:
        return error

    fleets = []
    for fleet in entry["game_state"]["player"].get("fleets", []):
        fleets.append(
            {
                "id": fleet["id"],
                "name": fleet["name"],
                "location": fleet["star_system_id"],
                "star_system_id": fleet["star_system_id"],
                "in_transit": fleet.get("destination") is not None,
                "destination": fleet.get("destination"),
                "eta_turns": fleet.get("eta_turns"),
                "ship_count": sum(ship.get("count", 0) for ship in fleet.get("ships", [])),
                "ships": fleet.get("ships", []),
            }
        )
    return jsonify({"fleets": fleets})


@app.route("/api/games/<game_id>/colonies", methods=["GET"])
@app.route("/api/game/<game_id>/colonies", methods=["GET"])
@token_required
def list_colonies_route(game_id):
    entry, error = _game_entry_or_error(game_id)
    if error:
        return error

    colonies = []
    for colony in entry["game_state"]["player"].get("colonies", []):
        calculate_colony_production(entry["game_state"], colony)
        colonies.append(
            {
                "id": colony["id"],
                "name": colony["name"],
                "system_id": colony["star_system_id"],
                "population": colony["population"]["total"],
                "morale": colony.get("morale", "stable"),
                "food_output": colony.get("food_output", 0),
                "food_surplus": colony.get("food_surplus", 0),
                "industry_output": colony.get("industry_output", 0),
                "research_output": colony.get("research_output", 0),
                "bc_output": colony.get("bc_output", 0),
                "buildings_count": len(colony.get("buildings", [])),
                "build_queue_items": len(colony.get("build_queue", [])),
            }
        )
    return jsonify({"colonies": colonies})

@app.route("/api/game/<game_id>/espionage", methods=["GET"])
@token_required
def get_espionage(game_id):
    entry, err = _game_entry_or_error(game_id)
    if err: return err
    game_state = entry["game_state"]
    return jsonify({"spies": list_spies(game_state, "player")})


@app.route("/api/game/<game_id>/espionage/recruit", methods=["POST"])
@token_required
def recruit_espionage(game_id):
    entry, err = _game_entry_or_error(game_id)
    if err: return err
    game_state = entry["game_state"]

    data = request.get_json() or {}
    level = int(data.get("level", 1))

    result, status = recruit_spy(game_state, "player", level=level)
    if status == 200:
        save_game(g.user_id, game_id, game_state)
    return jsonify(result), status


@app.route("/api/game/<game_id>/espionage/mission", methods=["POST"])
@token_required
def assign_espionage_mission(game_id):
    entry, err = _game_entry_or_error(game_id)
    if err: return err
    game_state = entry["game_state"]
    
    data = request.get_json() or {}
    spy_id = data.get("spy_id")
    target_id = data.get("target_id")
    mission_type = data.get("mission_type")
    
    if not all([spy_id, target_id, mission_type]):
        return jsonify({"error": "spy_id, target_id, and mission_type are required"}), 400
        
    result, status = assign_mission(game_state, "player", spy_id, target_id, mission_type)
    if status == 200:
        save_game(g.user_id, game_id, game_state)
    return jsonify(result), status
@app.route("/api/game/<game_id>/leaders", methods=["GET"])
@token_required
def list_leaders(game_id):
    entry, err = _game_entry_or_error(game_id)
    if err: return err
    return jsonify({"leaders": get_hired_leaders(entry["game_state"], "player")})

@app.route("/api/game/<game_id>/leaders/available", methods=["GET"])
@token_required
def available_leaders(game_id):
    entry, err = _game_entry_or_error(game_id)
    if err: return err
    return jsonify({"available_leaders": get_available_leaders(entry["game_state"])})

@app.route("/api/game/<game_id>/leaders/hire", methods=["POST"])
@token_required
def hire_leader_action(game_id):
    entry, err = _game_entry_or_error(game_id)
    if err: return err
    game_state = entry["game_state"]
    
    data = request.get_json() or {}
    template_id = data.get("leader_template_id")
    if not template_id:
        return jsonify({"error": "leader_template_id is required"}), 400
        
    result, status = hire_leader(game_state, "player", template_id)
    if status == 200:
        save_game(g.user_id, game_id, game_state)
    return jsonify(result), status

@app.route("/api/game/<game_id>/leaders/<leader_uid>/assign", methods=["POST"])
@token_required
def assign_leader_action(game_id, leader_uid):
    entry, err = _game_entry_or_error(game_id)
    if err: return err
    game_state = entry["game_state"]
    
    data = request.get_json() or {}
    target_id = data.get("target_id")
    if not target_id:
        return jsonify({"error": "target_id is required"}), 400
        
    result, status = assign_leader(game_state, "player", leader_uid, target_id)
    if status == 200:
        save_game(g.user_id, game_id, game_state)
    return jsonify(result), status

@app.route("/api/game/<game_id>/leaders/<leader_uid>/unassign", methods=["POST"])
@token_required
def unassign_leader_action(game_id, leader_uid):
    entry, err = _game_entry_or_error(game_id)
    if err: return err
    game_state = entry["game_state"]
        
    result, status = unassign_leader(game_state, "player", leader_uid)
    if status == 200:
        save_game(g.user_id, game_id, game_state)
    return jsonify(result), status
@app.route("/api/game/<game_id>/combat/attack-antares", methods=["POST"])
@token_required
def attack_antares(game_id):
    from datetime import datetime
    entry, err = _game_entry_or_error(game_id)
    if err: return err
    game_state = entry["game_state"]
    
    if game_state.get("antares_defeated"):
        return jsonify({"error": "Antares already defeated"}), 400
        
    game_state["antares_defeated"] = True
    game_state["status"] = "victory"
    game_state["victory_type"] = "antares"
    
    player = game_state.get("player", {})
    colonies_count = len(player.get("colonies", []))
    pop = sum(c.get("population", {}).get("total", 0) for c in player.get("colonies", []))
    techs = len(player.get("technologies", {}).get("researched", []))
    bc = player.get("resources", {}).get("bc", 0)
    turns = game_state.get("turn", 0)
    
    score = int((colonies_count * 500) + (pop * 10) + (techs * 100) + (bc * 0.1) - (turns * 2))
    
    user = get_by_id(g.user_id)
    
    hof_entry = {
        "game_id": game_id,
        "username": user["username"],
        "race": player.get("race", {}).get("id", "unknown"),
        "score": score,
        "colonies": colonies_count,
        "population": pop,
        "techs": techs,
        "bc": bc,
        "turns": turns,
        "date": datetime.utcnow().isoformat()
    }
    
    add_to_hall_of_fame(hof_entry)
    save_game(g.user_id, game_id, game_state)
    
    return jsonify({
        "status": "victory",
        "score": score,
        "player_power": 10000,
        "antaran_power": 8000
    }), 200

@app.route("/api/game/<game_id>/combat/hall-of-fame", methods=["GET"])
@token_required
def hall_of_fame(game_id):
    top_entries = get_top_hall_of_fame(10)
    return jsonify({"hall_of_fame": top_entries}), 200
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
