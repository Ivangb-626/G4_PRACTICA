from flask import Blueprint, request, jsonify, g
from app.auth.middleware import token_required
from app.models.game import GameModel

leaders_bp = Blueprint('leaders', __name__)

def _get_game_state(game_id):
    entry = GameModel.get_game(g.user_id, game_id)
    if not entry or entry == "forbidden":
        return None
    return entry['game_state']

@leaders_bp.route('/', methods=['GET'])
@leaders_bp.route('', methods=['GET'])
@token_required
def list_hired_leaders(game_id):
    game_state = _get_game_state(game_id)
    if not game_state:
        return jsonify({"error": "Game not found"}), 404
        
    leaders = game_state.get('player', {}).get('leaders', [])
    return jsonify(leaders), 200

@leaders_bp.route('/available', methods=['GET'])
@token_required
def list_available_leaders(game_id):
    # Logic to show available leaders to hire
    return jsonify([]), 200

@leaders_bp.route('/hire', methods=['POST'])
@token_required
def hire_leader(game_id):
    # Logic to hire leader
    return jsonify({"message": "Leader hired"}), 200
