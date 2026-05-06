from flask import Blueprint, request, jsonify, g
from app.auth.middleware import token_required
from app.models.game import GameModel

espionage_bp = Blueprint('espionage', __name__)

def _get_game_state(game_id):
    entry = GameModel.get_game(g.user_id, game_id)
    if not entry or entry == "forbidden":
        return None
    return entry['game_state']

@espionage_bp.route('/', methods=['GET'])
@espionage_bp.route('', methods=['GET'])
@token_required
def list_spies(game_id):
    game_state = _get_game_state(game_id)
    if not game_state:
        return jsonify({"error": "Game not found"}), 404
        
    spies = game_state.get('player', {}).get('spies', [])
    return jsonify(spies), 200

@espionage_bp.route('/recruit', methods=['POST'])
@token_required
def recruit_spy(game_id):
    # Logic to recruit spy
    return jsonify({"message": "Spy recruited"}), 200

@espionage_bp.route('/mission', methods=['POST'])
@token_required
def assign_mission(game_id):
    # Logic to assign mission
    return jsonify({"message": "Mission assigned"}), 200
