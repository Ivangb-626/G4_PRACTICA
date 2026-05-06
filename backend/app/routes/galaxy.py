from flask import Blueprint, jsonify, g
from app.auth.middleware import token_required
from app.models.game import GameModel

galaxy_bp = Blueprint('galaxy', __name__)

def _get_game_state(game_id):
    entry = GameModel.get_game(g.user_id, game_id)
    if not entry or entry == "forbidden":
        return None
    return entry['game_state']

@galaxy_bp.route('/', methods=['GET'])
@galaxy_bp.route('', methods=['GET'])
@token_required
def get_galaxy(game_id):
    game_state = _get_game_state(game_id)
    if not game_state:
        return jsonify({"error": "Game not found"}), 404
    
    # Fog of war filtering
    galaxy = game_state.get('galaxy', {})
    stars = galaxy.get('stars', [])
    
    # Simplified filtering: only show stars explored by player
    filtered_stars = []
    for star in stars:
        if "player" in star.get("explored_by", []):
            filtered_stars.append(star)
        else:
            # Show basic info but not planet details
            filtered_stars.append({
                "index": star["index"],
                "name": star["name"],
                "x": star["x"],
                "y": star["y"],
                "type": star["type"],
                "explored": False
            })
            
    return jsonify({"stars": filtered_stars, "size": galaxy.get("size")}), 200

@galaxy_bp.route('/star/<int:star_idx>', methods=['GET'])
@token_required
def get_star_details(game_id, star_idx):
    game_state = _get_game_state(game_id)
    if not game_state:
        return jsonify({"error": "Game not found"}), 404
        
    stars = game_state.get('galaxy', {}).get('stars', [])
    if star_idx < 0 or star_idx >= len(stars):
        return jsonify({"error": "Star not found"}), 404
        
    star = stars[star_idx]
    if "player" not in star.get("explored_by", []):
        return jsonify({"error": "Star not explored"}), 403
        
    return jsonify(star), 200
