from flask import Blueprint, request, jsonify, g
from app.auth.middleware import token_required
from app.models.game import GameModel

diplomacy_bp = Blueprint('diplomacy', __name__)

def _get_game_state(game_id):
    entry = GameModel.get_game(g.user_id, game_id)
    if not entry or entry == "forbidden":
        return None
    return entry['game_state']

@diplomacy_bp.route('/', methods=['GET'])
@diplomacy_bp.route('', methods=['GET'])
@token_required
def list_relations(game_id):
    game_state = _get_game_state(game_id)
    if not game_state:
        return jsonify({"error": "Game not found"}), 404
        
    relations = game_state.get('player', {}).get('diplomacy', [])
    return jsonify(relations), 200

@diplomacy_bp.route('/propose', methods=['POST'])
@token_required
def propose_treaty(game_id):
    game_state = _get_game_state(game_id)
    if not game_state:
        return jsonify({"error": "Game not found"}), 404
        
    data = request.get_json()
    # Logic to handle treaty proposal
    return jsonify({"message": "Treaty proposed"}), 200

@diplomacy_bp.route('/accept', methods=['POST'])
@token_required
def accept_treaty(game_id):
    # Logic to accept treaty
    return jsonify({"message": "Treaty accepted"}), 200

@diplomacy_bp.route('/war', methods=['POST'])
@token_required
def declare_war(game_id):
    game_state = _get_game_state(game_id)
    if not game_state:
        return jsonify({"error": "Game not found"}), 404
        
    data = request.get_json()
    target_id = data.get('target_id')
    
    # Logic to declare war
    return jsonify({"message": f"War declared on {target_id}"}), 200
