from flask import Blueprint, request, jsonify, g
from app.auth.middleware import token_required
from app.models.game import GameModel
from app.services.colony_service import calculate_colony_production, add_to_build_queue

colony_bp = Blueprint('colony', __name__)

def _get_game_state(game_id):
    entry = GameModel.get_game(g.user_id, game_id)
    if not entry or entry == "forbidden":
        return None
    return entry['game_state']

@colony_bp.route('/', methods=['GET'])
@colony_bp.route('', methods=['GET'])
@token_required
def list_colonies(game_id):
    game_state = _get_game_state(game_id)
    if not game_state:
        return jsonify({"error": "Game not found"}), 404
        
    colonies = game_state.get('player', {}).get('colonies', [])
    return jsonify(colonies), 200

@colony_bp.route('/<colony_id>', methods=['GET'])
@token_required
def get_colony(game_id, colony_id):
    game_state = _get_game_state(game_id)
    if not game_state:
        return jsonify({"error": "Game not found"}), 404
        
    colony = next((c for c in game_state['player'].get('colonies', []) if c['id'] == colony_id), None)
    if not colony:
        return jsonify({"error": "Colony not found"}), 404
        
    # Enrich with production details
    prod = calculate_colony_production(colony, game_state['player'], game_state)
    colony['production_details'] = prod
    
    return jsonify(colony), 200

@colony_bp.route('/<colony_id>/assign', methods=['POST'])
@token_required
def assign_population(game_id, colony_id):
    game_state = _get_game_state(game_id)
    if not game_state:
        return jsonify({"error": "Game not found"}), 404
        
    colony = next((c for c in game_state['player'].get('colonies', []) if c['id'] == colony_id), None)
    if not colony:
        return jsonify({"error": "Colony not found"}), 404
        
    data = request.get_json()
    farmers = data.get('farmers', colony.get('farmers', 0))
    workers = data.get('workers', colony.get('workers', 0))
    scientists = data.get('scientists', colony.get('scientists', 0))
    
    total_pop = colony.get('population', 0)
    if farmers + workers + scientists > total_pop:
        return jsonify({"error": "Total assignment exceeds population"}), 400
        
    colony['farmers'] = farmers
    colony['workers'] = workers
    colony['scientists'] = scientists
    
    GameModel.save_game(g.user_id, game_id, game_state)
    return jsonify({"message": "Population assigned", "colony": colony}), 200

@colony_bp.route('/<colony_id>/build-queue', methods=['POST'])
@token_required
def update_build_queue(game_id, colony_id):
    game_state = _get_game_state(game_id)
    if not game_state:
        return jsonify({"error": "Game not found"}), 404
        
    colony = next((c for c in game_state['player'].get('colonies', []) if c['id'] == colony_id), None)
    if not colony:
        return jsonify({"error": "Colony not found"}), 404
        
    data = request.get_json()
    item_id = data.get('item_id')
    item_type = data.get('item_type') # 'building' or 'ship'
    
    success, error = add_to_build_queue(colony, item_id, item_type, game_state)
    if not success:
        return jsonify({"error": error}), 400
        
    GameModel.save_game(g.user_id, game_id, game_state)
    return jsonify({"message": "Build queue updated", "queue": colony.get('build_queue', [])}), 200
