from flask import Blueprint, request, jsonify, g
from app.auth.middleware import token_required
from app.models.game import GameModel, HallOfFameModel
from app.services.game_service import generate_game_state, list_scenarios, _normalize_difficulty
from app.services.turn_engine import TurnEngine
from app.services.score_service import calculate_final_score

game_bp = Blueprint('game', __name__)


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
    data = request.get_json() or {}
    name = data.get('name', 'New Game')
    scenario = {
        "scenario_id": data.get('scenario_id', 'default'),
        "galaxy_size": data.get('galaxy_size', 'medium'),
        "galaxy_age": data.get('galaxy_age', 'average'),
        "num_opponents": int(data.get('num_opponents', 3)),
        "player_race": data.get('player_race', 'alkari'),
        "difficulty": _normalize_difficulty(data.get('difficulty', 'officer')),
        "starting_tech_level": data.get('starting_tech_level', 'average'),
        "antaran_attacks_enabled": bool(data.get('antaran_attacks_enabled', True)),
        "orion_guardian_enabled": bool(data.get('orion_guardian_enabled', True)),
        "random_events_enabled": bool(data.get('random_events_enabled', True)),
        "home_system_name": data.get('home_system_name'),
    }
    game_state = generate_game_state(name, scenario)
    game_id = GameModel.create_game(g.user_id, name, scenario["scenario_id"], game_state)
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
    result = TurnEngine.execute_turn(game_state)
    GameModel.save_game(g.user_id, game_id, game_state)
    return jsonify(result), 200


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
