from flask import Blueprint, request, jsonify, g
from app.auth.middleware import token_required
from app.models.game import GameModel
from app.services.game_service import apply_cheat

cheat_bp = Blueprint('cheat', __name__)

def _get_game_state(game_id):
    entry = GameModel.get_game(g.user_id, game_id)
    if not entry or entry == "forbidden":
        return None
    return entry['game_state']

@cheat_bp.route('/', methods=['POST'])
@cheat_bp.route('', methods=['POST'])
@token_required
def apply_cheat_route(game_id):
    game_state = _get_game_state(game_id)
    if not game_state:
        return jsonify({"error": "Game not found"}), 404
        
    data = request.get_json()
    code = data.get('code')
    
    # original 11 + RUSHBUY + CRUNCH = 13
    # MOLA, GALAXY, RESEARCH, ...
    
    success, message = apply_cheat(game_state, code)
    if not success:
        return jsonify({"error": message}), 400
        
    GameModel.save_game(g.user_id, game_id, game_state)
    return jsonify({"message": message}), 200

@cheat_bp.route('/codes', methods=['GET'])
@token_required
def list_cheat_codes(game_id):
    codes = ["MOLA", "GALAXY", "RESEARCH", "MONEY", "POP", "SCORE", "SHIP", "TECH", "COLONY", "FLEET", "ANTARAS", "RUSHBUY", "CRUNCH"]
    return jsonify(codes), 200
