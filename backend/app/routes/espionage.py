from flask import Blueprint, request, jsonify, g
from app.auth.middleware import token_required
from app.models.game import GameModel
from app.services.espionage_service import recruit_spy as svc_recruit, assign_spy as svc_assign, list_spies as svc_list

espionage_bp = Blueprint('espionage', __name__)


def _entry(game_id):
    entry = GameModel.get_game(g.user_id, game_id)
    if not entry or entry == "forbidden":
        return None
    return entry


@espionage_bp.route('/', methods=['GET'])
@espionage_bp.route('', methods=['GET'])
@token_required
def list_spies(game_id):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    return jsonify(svc_list(entry['game_state'].get('player', {}))), 200


@espionage_bp.route('/recruit', methods=['POST'])
@token_required
def recruit(game_id):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    res = svc_recruit(entry['game_state']['player'])
    if res.get('success'):
        GameModel.save_game(g.user_id, game_id, entry['game_state'])
    return jsonify(res), 200 if res.get('success') else 400


@espionage_bp.route('/mission', methods=['POST'])
@token_required
def assign_mission(game_id):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    data = request.get_json() or {}
    spy_id = data.get('spy_id')
    target = data.get('target')
    mission = data.get('mission', 'defense')
    if not spy_id:
        return jsonify({"error": "spy_id required"}), 400
    res = svc_assign(entry['game_state']['player'], spy_id, target, mission)
    if res.get('success'):
        GameModel.save_game(g.user_id, game_id, entry['game_state'])
    return jsonify(res), 200 if res.get('success') else 400
