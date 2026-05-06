from flask import Blueprint, request, jsonify, g
from app.auth.middleware import token_required
from app.models.game import GameModel

ship_design_bp = Blueprint('ship_design', __name__)

def _get_game_state(game_id):
    entry = GameModel.get_game(g.user_id, game_id)
    if not entry or entry == "forbidden":
        return None
    return entry['game_state']

@ship_design_bp.route('/', methods=['GET'])
@ship_design_bp.route('', methods=['GET'])
@token_required
def list_designs(game_id):
    game_state = _get_game_state(game_id)
    if not game_state:
        return jsonify({"error": "Game not found"}), 404
        
    designs = game_state.get('player', {}).get('ship_designs', [])
    return jsonify(designs), 200

@ship_design_bp.route('/', methods=['POST'])
@ship_design_bp.route('', methods=['POST'])
@token_required
def create_design(game_id):
    game_state = _get_game_state(game_id)
    if not game_state:
        return jsonify({"error": "Game not found"}), 404
        
    data = request.get_json()
    # Logic to validate hull, weapons, specials
    # Add to player.ship_designs
    return jsonify({"message": "Design created"}), 201
