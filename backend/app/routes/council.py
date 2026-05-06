from flask import Blueprint, request, jsonify, g
from app.auth.middleware import token_required
from app.models.game import GameModel
from app.services.council_service import convene_council, player_vote, estimate_council_votes

council_bp = Blueprint('council', __name__)


def _entry(game_id):
    entry = GameModel.get_game(g.user_id, game_id)
    if not entry or entry == "forbidden":
        return None
    return entry


@council_bp.route('/votes', methods=['GET'])
@token_required
def votes(game_id):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    return jsonify(estimate_council_votes(entry['game_state'])), 200


@council_bp.route('/convene', methods=['POST'])
@token_required
def convene(game_id):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    res = convene_council(entry['game_state'])
    GameModel.save_game(g.user_id, game_id, entry['game_state'])
    return jsonify(res), 200


@council_bp.route('/vote', methods=['POST'])
@token_required
def vote(game_id):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    data = request.get_json() or {}
    res = player_vote(entry['game_state'], data.get('candidate'))
    GameModel.save_game(g.user_id, game_id, entry['game_state'])
    return jsonify(res), 200
