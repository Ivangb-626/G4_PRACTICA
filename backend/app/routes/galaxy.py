from flask import Blueprint, jsonify, g
from app.auth.middleware import token_required
from app.models.game import GameModel
from app.services.game_service import get_galaxy_view, find_system

galaxy_bp = Blueprint('galaxy', __name__)


def _entry(game_id):
    entry = GameModel.get_game(g.user_id, game_id)
    if not entry or entry == "forbidden":
        return None
    return entry


@galaxy_bp.route('/', methods=['GET'])
@galaxy_bp.route('', methods=['GET'])
@token_required
def get_galaxy(game_id):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    return jsonify(get_galaxy_view(entry['game_state'])), 200


@galaxy_bp.route('/system/<system_id>', methods=['GET'])
@token_required
def get_system(game_id, system_id):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    visible = set(entry['game_state'].get('galaxy', {}).get('fog_of_war', {}).get('player', []))
    if system_id not in visible:
        return jsonify({"error": "System not explored"}), 403
    sys = find_system(entry['game_state'], system_id)
    if not sys:
        return jsonify({"error": "System not found"}), 404
    return jsonify(sys), 200
