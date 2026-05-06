from flask import Blueprint, request, jsonify, g
from app.auth.middleware import token_required
from app.models.game import GameModel
from app.services.leader_service import (
    list_hired,
    list_available,
    hire_leader as svc_hire_leader,
    assign_leader as svc_assign_leader,
    unassign_leader as svc_unassign_leader,
    dismiss_leader as svc_dismiss_leader,
)

leaders_bp = Blueprint('leaders', __name__)


def _entry(game_id):
    entry = GameModel.get_game(g.user_id, game_id)
    if not entry or entry == "forbidden":
        return None
    return entry


def _save(game_id, game_state):
    GameModel.save_game(g.user_id, game_id, game_state)


@leaders_bp.route('/', methods=['GET'])
@leaders_bp.route('', methods=['GET'])
@token_required
def get_hired(game_id):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    return jsonify(list_hired(entry['game_state'].get('player', {}))), 200


@leaders_bp.route('/available', methods=['GET'])
@token_required
def get_available(game_id):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    return jsonify(list_available(entry['game_state'].get('player', {}))), 200


@leaders_bp.route('/hire', methods=['POST'])
@token_required
def hire(game_id):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    data = request.get_json() or {}
    leader_id = data.get('leader_id')
    if not leader_id:
        return jsonify({"error": "leader_id required"}), 400
    res = svc_hire_leader(entry['game_state']['player'], leader_id)
    if res.get('success'):
        _save(game_id, entry['game_state'])
    return jsonify(res), 200 if res.get('success') else 400


@leaders_bp.route('/assign', methods=['POST'])
@token_required
def assign(game_id):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    data = request.get_json() or {}
    leader_id = data.get('leader_id')
    target_id = data.get('target_id')
    if not leader_id or not target_id:
        return jsonify({"error": "leader_id and target_id required"}), 400
    res = svc_assign_leader(entry['game_state']['player'], leader_id, target_id)
    if res.get('success'):
        _save(game_id, entry['game_state'])
    return jsonify(res), 200 if res.get('success') else 400


@leaders_bp.route('/unassign', methods=['POST'])
@token_required
def unassign(game_id):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    data = request.get_json() or {}
    leader_id = data.get('leader_id')
    res = svc_unassign_leader(entry['game_state']['player'], leader_id)
    _save(game_id, entry['game_state'])
    return jsonify(res), 200


@leaders_bp.route('/dismiss', methods=['POST'])
@token_required
def dismiss(game_id):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    data = request.get_json() or {}
    leader_id = data.get('leader_id')
    res = svc_dismiss_leader(entry['game_state']['player'], leader_id)
    _save(game_id, entry['game_state'])
    return jsonify(res), 200
