from flask import Blueprint, request, jsonify, g
from app.auth.middleware import token_required
from app.models.game import GameModel
from app.services.game_service import move_fleet, colonize_planet # Assuming these are in game_service or fleet_service

fleet_bp = Blueprint('fleet', __name__)

def _get_game_state(game_id):
    entry = GameModel.get_game(g.user_id, game_id)
    if not entry or entry == "forbidden":
        return None
    return entry['game_state']

@fleet_bp.route('/', methods=['GET'])
@fleet_bp.route('', methods=['GET'])
@token_required
def list_fleets(game_id):
    game_state = _get_game_state(game_id)
    if not game_state:
        return jsonify({"error": "Game not found"}), 404
        
    fleets = game_state.get('player', {}).get('fleets', [])
    return jsonify(fleets), 200

@fleet_bp.route('/<fleet_id>/move', methods=['POST'])
@token_required
def move_fleet_route(game_id, fleet_id):
    game_state = _get_game_state(game_id)
    if not game_state:
        return jsonify({"error": "Game not found"}), 404
        
    data = request.get_json()
    star_idx = data.get('star_idx')
    
    success, error = move_fleet(game_state, "player", fleet_id, star_idx)
    if not success:
        return jsonify({"error": error}), 400
        
    GameModel.save_game(g.user_id, game_id, game_state)
    return jsonify({"message": "Fleet movement orders issued"}), 200

@fleet_bp.route('/range', methods=['GET'])
@token_required
def get_fleet_range(game_id):
    game_state = _get_game_state(game_id)
    if not game_state:
        return jsonify({"error": "Game not found"}), 404
        
    # Logic to calculate fleet range based on tech and starbases
    # This is often derived from the game_state player object
    fuel_range = game_state['player'].get('fuel_range', 4)
    return jsonify({"range": fuel_range}), 200

@fleet_bp.route('/<fleet_id>/split', methods=['POST'])
@token_required
def split_fleet_route(game_id, fleet_id):
    game_state = _get_game_state(game_id)
    if not game_state:
        return jsonify({"error": "Game not found"}), 404
        
    data = request.get_json()
    ships_to_move = data.get('ships', []) # List of ship indices or IDs
    
    # Logic to split fleet
    # success, error = split_fleet(game_state, "player", fleet_id, ships_to_move)
    # For now, placeholder error
    return jsonify({"error": "Split fleet not fully implemented in service layer"}), 501

@fleet_bp.route('/<fleet_id>/colonize', methods=['POST'])
@token_required
def colonize_route(game_id, fleet_id):
    game_state = _get_game_state(game_id)
    if not game_state:
        return jsonify({"error": "Game not found"}), 404
        
    data = request.get_json()
    planet_idx = data.get('planet_idx')
    
    success, error = colonize_planet(game_state, "player", fleet_id, planet_idx)
    if not success:
        return jsonify({"error": error}), 400
        
    # As per rule 10: set star owner and update galaxy
    # The colonize_planet service should handle this, but we'll ensure it here if needed
    
    GameModel.save_game(g.user_id, game_id, game_state)
    return jsonify({"message": "Planet colonized"}), 200
