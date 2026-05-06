from flask import Blueprint, request, jsonify, g
from app.auth.middleware import token_required
from app.models.game import GameModel, HallOfFameModel

combat_bp = Blueprint('combat', __name__)

def _get_game_state(game_id):
    entry = GameModel.get_game(g.user_id, game_id)
    if not entry or entry == "forbidden":
        return None
    return entry['game_state']

@combat_bp.route('/auto', methods=['POST'])
@token_required
def auto_resolve(game_id):
    # Logic for auto-resolve
    return jsonify({"message": "Combat resolved"}), 200

@combat_bp.route('/log', methods=['GET'])
@token_required
def get_combat_logs(game_id):
    game_state = _get_game_state(game_id)
    if not game_state:
        return jsonify({"error": "Game not found"}), 404
        
    logs = game_state.get('combat_logs', [])
    return jsonify(logs), 200

@combat_bp.route('/attack-antares', methods=['POST'])
@token_required
def attack_antares(game_id):
    game_state = _get_game_state(game_id)
    if not game_state:
        return jsonify({"error": "Game not found"}), 404
        
    if game_state.get('antares_defeated'):
        return jsonify({"error": "Antares already defeated"}), 400
        
    # Logic to attack Antares
    # On win:
    # game_state['status'] = 'victory'
    # game_state['victory_type'] = 'antares'
    # compute score...
    # HallOfFameModel.add_entry(...)
    
    return jsonify({"message": "Assault on Antares launched"}), 200

@combat_bp.route('/hall-of-fame', methods=['GET'])
def get_hof():
    entries = HallOfFameModel.get_top_entries()
    return jsonify(entries), 200
