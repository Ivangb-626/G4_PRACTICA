from flask import Blueprint, request, jsonify, g
from app.auth.middleware import token_required
from app.models.game import GameModel
from app.services.game_service import set_research, get_tech_tree

research_bp = Blueprint('research', __name__)


def _entry(game_id):
    entry = GameModel.get_game(g.user_id, game_id)
    if not entry or entry == "forbidden":
        return None
    return entry


@research_bp.route('/', methods=['GET'])
@research_bp.route('', methods=['GET'])
@token_required
def get_state(game_id):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    return jsonify(get_tech_tree(entry['game_state'])), 200


@research_bp.route('/select', methods=['POST'])
@token_required
def select(game_id):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    data = request.get_json() or {}
    field = data.get('field')
    level = data.get('level')
    tech_id = data.get('tech_id')
    if not all([field, level, tech_id]):
        return jsonify({"error": "field, level and tech_id required"}), 400
    try:
        result = set_research(entry['game_state'], field, int(level), tech_id, owner_id='player')
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    GameModel.save_game(g.user_id, game_id, entry['game_state'])
    return jsonify(result), 200
