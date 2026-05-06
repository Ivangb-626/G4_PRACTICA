from flask import Blueprint, request, jsonify, g
from app.auth.middleware import token_required
from app.models.game import GameModel
from app.services.diplomacy_service import (
    propose_treaty,
    accept_treaty,
    reject_treaty,
    declare_war,
    offer_surrender,
    gift,
    demand,
    propose_tech_trade,
    blackmail,
    initialize_diplomacy,
)
from app.services.ai_service import AIService

diplomacy_bp = Blueprint('diplomacy', __name__)


def _entry(game_id):
    entry = GameModel.get_game(g.user_id, game_id)
    if not entry or entry == "forbidden":
        return None
    return entry


def _save(game_id, gs):
    GameModel.save_game(g.user_id, game_id, gs)


@diplomacy_bp.route('/', methods=['GET'])
@diplomacy_bp.route('', methods=['GET'])
@token_required
def list_relations(game_id):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    initialize_diplomacy(entry['game_state'])
    return jsonify(entry['game_state'].get('diplomacy', {})), 200


@diplomacy_bp.route('/propose', methods=['POST'])
@token_required
def propose(game_id):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    data = request.get_json() or {}
    target = data.get('target')
    treaty_type = data.get('type', 'trade_treaty')
    terms = data.get('terms', {})
    res = propose_treaty(entry['game_state'], 'player', target, treaty_type, terms)
    _save(game_id, entry['game_state'])
    return jsonify(res), 200


@diplomacy_bp.route('/accept', methods=['POST'])
@token_required
def accept(game_id):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    data = request.get_json() or {}
    res = accept_treaty(entry['game_state'], data.get('treaty_id'))
    _save(game_id, entry['game_state'])
    return jsonify(res), 200


@diplomacy_bp.route('/reject', methods=['POST'])
@token_required
def reject(game_id):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    data = request.get_json() or {}
    res = reject_treaty(entry['game_state'], data.get('treaty_id'))
    _save(game_id, entry['game_state'])
    return jsonify(res), 200


@diplomacy_bp.route('/war', methods=['POST'])
@token_required
def war(game_id):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    data = request.get_json() or {}
    res = declare_war(entry['game_state'], 'player', data.get('target'))
    _save(game_id, entry['game_state'])
    return jsonify(res), 200


@diplomacy_bp.route('/surrender', methods=['POST'])
@token_required
def surrender(game_id):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    data = request.get_json() or {}
    res = offer_surrender(entry['game_state'], 'player', data.get('target'))
    _save(game_id, entry['game_state'])
    return jsonify(res), 200


@diplomacy_bp.route('/gift', methods=['POST'])
@token_required
def make_gift(game_id):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    data = request.get_json() or {}
    res = gift(entry['game_state'], 'player', data.get('target'), data.get('payload', {}))
    _save(game_id, entry['game_state'])
    return jsonify(res), 200


@diplomacy_bp.route('/demand', methods=['POST'])
@token_required
def make_demand(game_id):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    data = request.get_json() or {}
    res = demand(entry['game_state'], 'player', data.get('target'), data.get('payload', {}))
    _save(game_id, entry['game_state'])
    return jsonify(res), 200


@diplomacy_bp.route('/tech-trade', methods=['POST'])
@token_required
def tech_trade(game_id):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    data = request.get_json() or {}
    res = propose_tech_trade(entry['game_state'], 'player', data.get('target'), data.get('offered_tech'), data.get('requested_tech'))
    _save(game_id, entry['game_state'])
    return jsonify(res), 200


@diplomacy_bp.route('/blackmail', methods=['POST'])
@token_required
def make_blackmail(game_id):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    data = request.get_json() or {}
    res = blackmail(entry['game_state'], 'player', data.get('target'), data.get('leverage', {}))
    _save(game_id, entry['game_state'])
    return jsonify(res), 200


@diplomacy_bp.route('/ai-evaluate', methods=['POST'])
@token_required
def ai_evaluate(game_id):
    """Endpoint que consulta al ai-service la valoracion de una propuesta sin ejecutar nada."""
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    data = request.get_json() or {}
    target = data.get('target')
    proposal = data.get('proposal', {})
    ai_player = next((ai for ai in entry['game_state'].get('ai_players', []) if ai['id'] == target), None)
    if not ai_player:
        return jsonify({"accept": False, "reason": "Not an AI empire"}), 200
    initialize_diplomacy(entry['game_state'])
    relation_value = 30
    relations = entry['game_state'].get('diplomacy', {}).get('relations', {})
    pair = sorted(['player', target])
    key = f"{pair[0]}|{pair[1]}"
    if key in relations:
        relation_value = relations[key].get('value', 30)
    result = AIService().evaluate_diplomacy(ai_player, proposal, relation_value)
    return jsonify(result), 200
