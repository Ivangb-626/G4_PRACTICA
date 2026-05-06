from flask import Blueprint, request, jsonify, g
from app.auth.middleware import token_required
from app.models.game import GameModel

research_bp = Blueprint('research', __name__)

def _get_game_state(game_id):
    entry = GameModel.get_game(g.user_id, game_id)
    if not entry or entry == "forbidden":
        return None
    return entry['game_state']

@research_bp.route('/', methods=['GET'])
@research_bp.route('', methods=['GET'])
@token_required
def get_research_state(game_id):
    game_state = _get_game_state(game_id)
    if not game_state:
        return jsonify({"error": "Game not found"}), 404
        
    player = game_state.get('player', {})
    tech_state = {
        "current_research": player.get("current_research"),
        "research_accumulated": player.get("research_accumulated", 0),
        "technologies": player.get("technologies", []),
        "available_techs": [] # This logic usually resides in research_service
    }
    
    return jsonify(tech_state), 200

@research_bp.route('/select', methods=['POST'])
@token_required
def select_research(game_id):
    game_state = _get_game_state(game_id)
    if not game_state:
        return jsonify({"error": "Game not found"}), 404
        
    data = request.get_json()
    tech_id = data.get('tech_id')
    
    if not tech_id:
        return jsonify({"error": "No tech_id provided"}), 400
        
    game_state['player']['current_research'] = tech_id
    GameModel.save_game(g.user_id, game_id, game_state)
    
    return jsonify({"message": f"Research set to {tech_id}"}), 200
