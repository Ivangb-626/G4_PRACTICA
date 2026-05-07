from flask import Blueprint, request, jsonify, g
from app.auth.middleware import token_required
from app.models.game import GameModel
from app.services.colony_service import calculate_colony_production, add_to_build_queue
from app.services.game_service import get_colony_detail

colony_bp = Blueprint('colony', __name__)


def _entry(game_id):
    entry = GameModel.get_game(g.user_id, game_id)
    if not entry or entry == "forbidden":
        return None
    return entry


@colony_bp.route('/', methods=['GET'])
@colony_bp.route('', methods=['GET'])
@token_required
def list_colonies(game_id):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    return jsonify(entry['game_state'].get('player', {}).get('colonies', [])), 200


@colony_bp.route('/<colony_id>', methods=['GET'])
@token_required
def get_colony(game_id, colony_id):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    try:
        return jsonify(get_colony_detail(entry['game_state'], colony_id)), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


@colony_bp.route('/<colony_id>/assign', methods=['POST'])
@token_required
def assign_population(game_id, colony_id):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    colony = next((c for c in entry['game_state']['player'].get('colonies', []) if c['id'] == colony_id), None)
    if not colony:
        return jsonify({"error": "Colony not found"}), 404
    data = request.get_json() or {}
    pop = colony.setdefault('population', {"total": 1, "max": 1, "farmers": 0, "workers": 0, "scientists": 0})
    farmers = int(data.get('farmers', pop.get('farmers', 0)))
    workers = int(data.get('workers', pop.get('workers', 0)))
    scientists = int(data.get('scientists', pop.get('scientists', 0)))
    total = pop.get('total', farmers + workers + scientists)
    if farmers + workers + scientists > total:
        return jsonify({"error": "Total assignment exceeds population"}), 400
    pop['farmers'] = farmers
    pop['workers'] = workers
    pop['scientists'] = scientists
    calculate_colony_production(entry['game_state'], colony)
    GameModel.save_game(g.user_id, game_id, entry['game_state'])
    return jsonify({"colony": colony}), 200


@colony_bp.route('/<colony_id>/build-queue', methods=['POST'])
@token_required
def update_build_queue(game_id, colony_id):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    colony = next((c for c in entry['game_state']['player'].get('colonies', []) if c['id'] == colony_id), None)
    if not colony:
        return jsonify({"error": "Colony not found"}), 404
    data = request.get_json() or {}
    item_id = data.get('item_id')
    item_type = data.get('item_type', 'building')
    success, error = add_to_build_queue(colony, item_type, item_id, entry['game_state'])
    if not success:
        return jsonify({"error": error}), 400
    GameModel.save_game(g.user_id, game_id, entry['game_state'])
    return jsonify({"queue": colony.get('build_queue', [])}), 200


@colony_bp.route('/<colony_id>/build-queue/<int:idx>', methods=['DELETE'])
@token_required
def remove_build_queue_item(game_id, colony_id, idx):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    colony = next((c for c in entry['game_state']['player'].get('colonies', []) if c['id'] == colony_id), None)
    if not colony:
        return jsonify({"error": "Colony not found"}), 404
    queue = colony.get('build_queue', [])
    if idx < 0 or idx >= len(queue):
        return jsonify({"error": "Index out of range"}), 400
    queue.pop(idx)
    colony['build_queue'] = queue
    GameModel.save_game(g.user_id, game_id, entry['game_state'])
    return jsonify({"queue": queue}), 200
