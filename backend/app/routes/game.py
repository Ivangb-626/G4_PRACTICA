from flask import Blueprint, request, jsonify, g
from app.auth.middleware import token_required
from app.models.game import GameModel
from app.services.game_service import generate_game_state, end_turn

game_bp = Blueprint('game', __name__)

def _game_entry_or_error(game_id):
    entry = GameModel.get_game(g.user_id, game_id)
    if entry == "forbidden":
        return None, (jsonify({"error": "This game does not belong to you"}), 403)
    if not entry:
        return None, (jsonify({"error": "Game not found"}), 404)
    return entry, None

@game_bp.route('/new', methods=['POST'])
@token_required
def create_new_game():
    data = request.get_json()
    name = data.get('name', 'New Game')
    scenario_id = data.get('scenario_id', 'default')
    
    # Logic to generate initial state based on race, galaxy size, etc.
    game_state = generate_game_state(data)
    
    game_id = GameModel.create_game(g.user_id, name, scenario_id, game_state)
    return jsonify({"game_id": game_id, "message": "Game created"}), 201

@game_bp.route('/<game_id>', methods=['GET'])
@token_required
def get_game_state(game_id):
    entry, error = _game_entry_or_error(game_id)
    if error: return error
    
    # Filter state for player (fog of war etc. if needed)
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
    result = end_turn(game_id, game_state)
    
    # Save updated state
    GameModel.save_game(g.user_id, game_id, game_state)
    
    return jsonify(result), 200
