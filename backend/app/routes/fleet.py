from flask import Blueprint, request, jsonify, g
from app.auth.middleware import token_required
from app.models.game import GameModel
from app.services.game_service import (
    move_fleet,
    colonize_planet,
    empire_max_jumps,
    empire_has_unlimited_range,
    reachable_systems,
    find_fleet,
    get_empire,
    transfer_ships,
)
from app.services.fleet_service import split_fleet, merge_fleets, disband_fleet

fleet_bp = Blueprint('fleet', __name__)


def _entry(game_id):
    entry = GameModel.get_game(g.user_id, game_id)
    if not entry or entry == "forbidden":
        return None
    return entry


@fleet_bp.route('/', methods=['GET'])
@fleet_bp.route('', methods=['GET'])
@token_required
def list_fleets(game_id):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    fleets = entry['game_state'].get('player', {}).get('fleets', [])
    return jsonify(fleets), 200


@fleet_bp.route('/range', methods=['GET'])
@token_required
def get_range(game_id):
    """Numero maximo de saltos del jugador en este momento."""
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    empire = get_empire(entry['game_state'], 'player')
    return jsonify({
        "max_jumps": empire_max_jumps(empire),
        "unlimited": empire_has_unlimited_range(empire),
    }), 200


@fleet_bp.route('/<fleet_id>/reachable', methods=['GET'])
@token_required
def fleet_reachable(game_id, fleet_id):
    """IDs de sistemas accesibles para esa flota desde su posicion actual."""
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    fleet = find_fleet(entry['game_state'], 'player', fleet_id)
    if not fleet:
        return jsonify({"error": "Fleet not found"}), 404
    empire = get_empire(entry['game_state'], 'player')
    unlimited = empire_has_unlimited_range(empire)
    if unlimited:
        all_ids = [
            s["id"]
            for s in entry['game_state'].get('galaxy', {}).get('star_systems', [])
            if s.get("id") != fleet['star_system_id']
        ]
        return jsonify({
            "max_jumps": -1,
            "unlimited": True,
            "origin": fleet['star_system_id'],
            "reachable": all_ids,
        }), 200
    max_jumps = empire_max_jumps(empire)
    targets = reachable_systems(entry['game_state'], fleet['star_system_id'], max_jumps)
    return jsonify({
        "max_jumps": max_jumps,
        "unlimited": False,
        "origin": fleet['star_system_id'],
        "reachable": list(targets),
    }), 200


@fleet_bp.route('/<fleet_id>/move', methods=['POST'])
@token_required
def move(game_id, fleet_id):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    data = request.get_json() or {}
    destination = data.get('destination') or data.get('star_id')
    try:
        result = move_fleet(entry['game_state'], 'player', fleet_id, destination)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    GameModel.save_game(g.user_id, game_id, entry['game_state'])
    return jsonify(result), 200


@fleet_bp.route('/<fleet_id>/colonize', methods=['POST'])
@token_required
def colonize(game_id, fleet_id):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    data = request.get_json() or {}
    planet_index = int(data.get('planet_index', data.get('planet_idx', 0)))
    try:
        result = colonize_planet(entry['game_state'], 'player', fleet_id, planet_index)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    GameModel.save_game(g.user_id, game_id, entry['game_state'])
    return jsonify(result), 200


@fleet_bp.route('/<fleet_id>/split', methods=['POST'])
@token_required
def split(game_id, fleet_id):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    data = request.get_json() or {}
    ships = data.get('ships', [])
    res = split_fleet(entry['game_state']['player'], fleet_id, ships)
    if res.get('success'):
        GameModel.save_game(g.user_id, game_id, entry['game_state'])
    return jsonify(res), 200 if res.get('success') else 400


@fleet_bp.route('/merge', methods=['POST'])
@token_required
def merge(game_id):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    data = request.get_json() or {}
    res = merge_fleets(entry['game_state']['player'], data.get('fleet_a'), data.get('fleet_b'))
    if res.get('success'):
        GameModel.save_game(g.user_id, game_id, entry['game_state'])
    return jsonify(res), 200 if res.get('success') else 400


@fleet_bp.route('/transfer', methods=['POST'])
@token_required
def transfer(game_id):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    data = request.get_json() or {}
    from_fleet = data.get('from_fleet')
    to_fleet = data.get('to_fleet')
    ships = data.get('ships', [])
    try:
        result = transfer_ships(entry['game_state'], 'player', from_fleet, to_fleet, ships)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    GameModel.save_game(g.user_id, game_id, entry['game_state'])
    return jsonify(result), 200


@fleet_bp.route('/<fleet_id>', methods=['DELETE'])
@token_required
def disband(game_id, fleet_id):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    res = disband_fleet(entry['game_state']['player'], fleet_id)
    GameModel.save_game(g.user_id, game_id, entry['game_state'])
    return jsonify(res), 200
