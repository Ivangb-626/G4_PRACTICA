import asyncio
from flask import Blueprint, request, jsonify, g
from app.auth.middleware import token_required
from app.models.game import GameModel, HallOfFameModel
from app.services.game_service import (
    DIFFICULTY_LEVELS,
    GALAXY_SIZE_COUNTS,
    RACES,
    SCENARIOS,
    generate_game_state,
    list_scenarios,
    _normalize_difficulty,
    end_turn,
    validate_end_turn,
)
from app.services.score_service import calculate_final_score

game_bp = Blueprint('game', __name__)


def _payload_bool(data, key, default):
    value = data.get(key, default)
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "on"}:
            return True
        if normalized in {"false", "0", "no", "off"}:
            return False
    return bool(value)


def _scenario_definition(scenario_id):
    return next((item for item in SCENARIOS if item.get("id") == scenario_id), None)


def _validated_new_game_payload(data):
    if not isinstance(data, dict):
        return None, "Request body must be a JSON object"

    scenario_id = str(data.get("scenario_id") or "default").strip()
    scenario_def = _scenario_definition(scenario_id)
    if not scenario_def:
        return None, f"Unknown scenario: {scenario_id}"

    name = str(data.get("name") or "New Game").strip()
    if not name:
        return None, "Game name is required"
    if len(name) > 100:
        return None, "Game name must be 100 characters or fewer"

    galaxy_size = str(data.get("galaxy_size") or "medium").strip()
    allowed_sizes = scenario_def.get("galaxy_sizes") or list(GALAXY_SIZE_COUNTS.keys())
    if galaxy_size not in allowed_sizes:
        return None, f"Galaxy size must be one of: {', '.join(allowed_sizes)}"

    galaxy_age = str(data.get("galaxy_age") or "average").strip()
    allowed_ages = scenario_def.get("galaxy_ages") or ["early", "average", "late"]
    if galaxy_age not in allowed_ages:
        return None, f"Galaxy age must be one of: {', '.join(allowed_ages)}"

    try:
        num_opponents = int(data.get("num_opponents", 3))
    except (TypeError, ValueError):
        return None, "Number of opponents must be an integer"
    max_opponents = int(scenario_def.get("max_opponents", 7))
    if num_opponents < 1 or num_opponents > max_opponents:
        return None, f"Number of opponents must be between 1 and {max_opponents}"

    player_race = str(data.get("player_race") or "alkari").strip()
    if player_race not in RACES:
        return None, f"Unknown player race: {player_race}"

    difficulty = _normalize_difficulty(str(data.get("difficulty") or "officer"))
    allowed_difficulties = scenario_def.get("difficulty_options") or DIFFICULTY_LEVELS
    if difficulty not in allowed_difficulties:
        return None, f"Difficulty must be one of: {', '.join(allowed_difficulties)}"

    starting_tech_level = str(data.get("starting_tech_level") or "average").strip()
    allowed_tech_levels = scenario_def.get("starting_tech_levels") or ["pre_warp", "average", "advanced"]
    if starting_tech_level not in allowed_tech_levels:
        return None, f"Starting tech level must be one of: {', '.join(allowed_tech_levels)}"

    home_system_name = data.get("home_system_name")
    if home_system_name is not None:
        home_system_name = str(home_system_name).strip() or None
        if home_system_name and len(home_system_name) > 20:
            return None, "Home system name must be 20 characters or fewer"

    return {
        "name": name,
        "scenario": {
            "scenario_id": scenario_id,
            "galaxy_size": galaxy_size,
            "galaxy_age": galaxy_age,
            "num_opponents": num_opponents,
            "player_race": player_race,
            "difficulty": difficulty,
            "starting_tech_level": starting_tech_level,
            "antaran_attacks_enabled": _payload_bool(data, "antaran_attacks_enabled", True),
            "orion_guardian_enabled": _payload_bool(data, "orion_guardian_enabled", True),
            "random_events_enabled": _payload_bool(data, "random_events_enabled", True),
            "home_system_name": home_system_name,
        },
    }, None


def _game_entry_or_error(game_id):
    entry = GameModel.get_game(g.user_id, game_id)
    if entry == "forbidden":
        return None, (jsonify({"error": "This game does not belong to you"}), 403)
    if not entry:
        return None, (jsonify({"error": "Game not found"}), 404)
    return entry, None


@game_bp.route('/scenarios', methods=['GET'])
def get_scenarios():
    return jsonify(list_scenarios()), 200


@game_bp.route('/new', methods=['POST'])
@token_required
def create_new_game():
    data = request.get_json(silent=True) or {}
    payload, error = _validated_new_game_payload(data)
    if error:
        return jsonify({"error": error}), 400

    name = payload["name"]
    scenario = payload["scenario"]
    try:
        game_state = generate_game_state(name, scenario)
        game_id = GameModel.create_game(g.user_id, name, scenario["scenario_id"], game_state)
    except Exception as exc:
        return jsonify({"error": f"No se pudo crear la partida: {exc}"}), 500
    return jsonify({"game_id": game_id, "message": "Game created"}), 201


@game_bp.route('/<game_id>', methods=['GET'])
@token_required
def get_game_state(game_id):
    entry, error = _game_entry_or_error(game_id)
    if error: return error
    return jsonify(entry['game_state']), 200


@game_bp.route('/list', methods=['GET'])
@token_required
def list_user_games():
    games = GameModel.list_games(g.user_id)
    return jsonify(games), 200


@game_bp.route('/<game_id>', methods=['DELETE'])
@token_required
def delete_user_game(game_id):
    success = GameModel.delete_game(g.user_id, game_id)
    if not success:
        return jsonify({"error": "Game not found or delete failed"}), 404
    return jsonify({"message": "Game deleted"}), 200


@game_bp.route('/<game_id>/end-turn', methods=['POST'])
@token_required
def process_end_turn(game_id):
    entry, error = _game_entry_or_error(game_id)
    if error: return error
    game_state = entry['game_state']
    status = validate_end_turn(game_state)
    if not status.get("can_end_turn"):
        first = status.get("blockers", ["No se puede pasar el turno."])[0]
        return jsonify({"error": f"No se puede pasar el turno: {first}", "turn_status": status}), 400
    try:
        result = asyncio.run(end_turn(game_state))
    except Exception as exc:
        return jsonify({
            "error": f"No se pudo resolver el turno. Revisa el estado de economia, flotas y eventos: {exc}",
            "turn_status": validate_end_turn(game_state),
        }), 500
    GameModel.save_game(g.user_id, game_id, game_state)
    return jsonify(result), 200


@game_bp.route('/<game_id>/turn-status', methods=['GET'])
@token_required
def get_turn_status(game_id):
    entry, error = _game_entry_or_error(game_id)
    if error: return error
    return jsonify(validate_end_turn(entry['game_state'])), 200


@game_bp.route('/<game_id>/score', methods=['GET'])
@token_required
def get_score(game_id):
    entry, error = _game_entry_or_error(game_id)
    if error: return error
    score = calculate_final_score(entry['game_state'], 'player')
    return jsonify(score), 200


@game_bp.route('/hall-of-fame', methods=['GET'])
def get_hall_of_fame():
    entries = HallOfFameModel.get_top_entries()
    return jsonify(entries), 200
