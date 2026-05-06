from flask import Blueprint, request, jsonify, g
from app.auth.middleware import token_required
from app.models.game import GameModel
from app.services.ground_combat import assault_colony, mind_control, bombard

ground_bp = Blueprint('ground', __name__)


def _entry(game_id):
    entry = GameModel.get_game(g.user_id, game_id)
    if not entry or entry == "forbidden":
        return None
    return entry


@ground_bp.route('/assault', methods=['POST'])
@token_required
def assault(game_id):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    data = request.get_json() or {}
    res = assault_colony(entry['game_state'], 'player', data.get('fleet_id'), data.get('colony_id'), bool(data.get('exterminate', False)))
    GameModel.save_game(g.user_id, game_id, entry['game_state'])
    return jsonify(res), 200


@ground_bp.route('/mind-control', methods=['POST'])
@token_required
def mind_control_route(game_id):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    data = request.get_json() or {}
    res = mind_control(entry['game_state'], 'player', data.get('colony_id'))
    GameModel.save_game(g.user_id, game_id, entry['game_state'])
    return jsonify(res), 200


@ground_bp.route('/bombard', methods=['POST'])
@token_required
def bombard_route(game_id):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    data = request.get_json() or {}
    fleet_id = data.get('fleet_id')
    colony_id = data.get('colony_id')
    intensity = int(data.get('intensity', 1))

    fleet = next((f for f in entry['game_state'].get('player', {}).get('fleets', []) if f.get('id') == fleet_id), None)
    target_colony = None
    for emp in [entry['game_state'].get('player'), *entry['game_state'].get('ai_players', [])]:
        if not emp:
            continue
        for c in emp.get('colonies', []):
            if c.get('id') == colony_id:
                target_colony = c
                break
        if target_colony:
            break
    if not fleet or not target_colony:
        return jsonify({"error": "Fleet or colony not found"}), 400
    res = bombard(entry['game_state'], fleet, target_colony, intensity)
    GameModel.save_game(g.user_id, game_id, entry['game_state'])
    return jsonify(res), 200
