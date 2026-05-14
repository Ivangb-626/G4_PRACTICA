from flask import Blueprint, request, jsonify, g
from app.auth.middleware import token_required
from app.models.game import GameModel
from app.services.game_service import (
    resolve_space_combats,
    defeat_orion_guardian,
    find_fleet,
    find_system,
    get_empire,
)
from app.services.antaran_service import build_dimensional_portal as svc_build_portal, attack_antaran_homeworld as svc_attack_antaran
from app.services.creature_service import resolve_monster_combat, defeat_monster
from app.services.tactical_combat import init_combat, auto_resolve, step_action
from app.services.leader_service import grant_loknar
from app.services.bombardment_service import (
    verificar_capacidad_ataque,
    bombardear_planeta,
    conquistar_planeta,
    asaltar_planeta,
    ejecutar_campaña_automatica
)

combat_bp = Blueprint('combat', __name__)


def _entry(game_id):
    entry = GameModel.get_game(g.user_id, game_id)
    if not entry or entry == "forbidden":
        return None
    return entry


@combat_bp.route('/auto', methods=['POST'])
@token_required
def auto(game_id):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    events = resolve_space_combats(entry['game_state'])
    GameModel.save_game(g.user_id, game_id, entry['game_state'])
    return jsonify({"events": events}), 200


@combat_bp.route('/planetary/check', methods=['POST'])
@token_required
def check_attack_capacity(game_id):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    data = request.get_json() or {}
    res = verificar_capacidad_ataque(
        entry['game_state'], 
        data.get('id_planeta'), 
        data.get('id_flota_atacante'), 
        'player'
    )
    return jsonify(res), 200


@combat_bp.route('/planetary/bombard', methods=['POST'])
@token_required
def bombard(game_id):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    data = request.get_json() or {}
    res = bombardear_planeta(
        entry['game_state'], 
        data.get('id_planeta'), 
        data.get('id_flota'), 
        data.get('intensidad', 'moderado')
    )
    GameModel.save_game(g.user_id, game_id, entry['game_state'])
    return jsonify(res), 200


@combat_bp.route('/planetary/assault', methods=['POST'])
@token_required
def assault(game_id):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    data = request.get_json() or {}
    res = asaltar_planeta(
        entry['game_state'], 
        data.get('id_planeta'), 
        'player',
        data.get('id_flota')
    )
    GameModel.save_game(g.user_id, game_id, entry['game_state'])
    return jsonify(res), 200


@combat_bp.route('/planetary/conquer', methods=['POST'])
@token_required
def conquer(game_id):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    data = request.get_json() or {}
    res = conquistar_planeta(
        entry['game_state'], 
        data.get('id_planeta'), 
        'player',
        data.get('id_flota')
    )
    GameModel.save_game(g.user_id, game_id, entry['game_state'])
    return jsonify(res), 200


@combat_bp.route('/planetary/campaign', methods=['POST'])
@token_required
def campaign(game_id):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    data = request.get_json() or {}
    res = ejecutar_campaña_automatica(
        entry['game_state'], 
        'player',
        data.get('id_flota'),
        data.get('lista_objetivos', []),
        data.get('intervalo', 5)
    )
    GameModel.save_game(g.user_id, game_id, entry['game_state'])
    return jsonify(res), 200


@combat_bp.route('/tactical/start', methods=['POST'])
@token_required
def tactical_start(game_id):
    """Inicia un combate tactico paso a paso entre la flota del jugador y un objetivo."""
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    data = request.get_json() or {}
    fleet_id = data.get('fleet_id')
    target_owner = data.get('target_owner')
    target_fleet_id = data.get('target_fleet_id')
    fleet = find_fleet(entry['game_state'], 'player', fleet_id)
    target_fleet = find_fleet(entry['game_state'], target_owner, target_fleet_id) if target_owner else None
    if not fleet or not target_fleet:
        return jsonify({"error": "Fleet or target fleet not found"}), 400
    state = init_combat(fleet.get('ships', []), target_fleet.get('ships', []))
    return jsonify(state), 200


@combat_bp.route('/tactical/auto', methods=['POST'])
@token_required
def tactical_auto(game_id):
    """Resolucion deterministica del combate tactico."""
    data = request.get_json() or {}
    state = data.get('state') or {}
    if not state:
        return jsonify({"error": "state required"}), 400
    out = auto_resolve(state)
    return jsonify(out), 200


@combat_bp.route('/tactical/action', methods=['POST'])
@token_required
def tactical_action(game_id):
    data = request.get_json() or {}
    state = data.get('state') or {}
    unit_uid = data.get('unit_uid')
    action = data.get('action') or {}
    res = step_action(state, unit_uid, action)
    return jsonify({"result": res, "state": state}), 200


@combat_bp.route('/monster', methods=['POST'])
@token_required
def fight_monster(game_id):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    data = request.get_json() or {}
    fleet_id = data.get('fleet_id')
    system_id = data.get('system_id')
    fleet = find_fleet(entry['game_state'], 'player', fleet_id)
    system = find_system(entry['game_state'], system_id)
    if not fleet or not system:
        return jsonify({"error": "Fleet or system not found"}), 400
    monster = system.get('space_monster')
    if not monster or monster.get('defeated'):
        return jsonify({"error": "No monster present"}), 400
    result = resolve_monster_combat(monster['type'], {"ships": fleet.get('ships', [])})
    if result.get('winner') == 'attacker':
        empire = get_empire(entry['game_state'], 'player')
        rewards = defeat_monster(system, empire)
        result['rewards'] = rewards
    GameModel.save_game(g.user_id, game_id, entry['game_state'])
    return jsonify(result), 200


@combat_bp.route('/orion/defeat-guardian', methods=['POST'])
@token_required
def defeat_guardian(game_id):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    res = defeat_orion_guardian(entry['game_state'], 'player')
    if res.get('success'):
        empire = get_empire(entry['game_state'], 'player')
        if empire:
            grant_loknar(empire)
            empire.setdefault('stats', {})['defeated_guardian'] = True
    GameModel.save_game(g.user_id, game_id, entry['game_state'])
    return jsonify(res), 200


@combat_bp.route('/antaran/build-portal', methods=['POST'])
@token_required
def build_portal(game_id):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    data = request.get_json() or {}
    res = svc_build_portal(entry['game_state'], 'player', data.get('colony_id'))
    GameModel.save_game(g.user_id, game_id, entry['game_state'])
    return jsonify(res), 200


@combat_bp.route('/antaran/assault', methods=['POST'])
@token_required
def assault_antaran(game_id):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    data = request.get_json() or {}
    res = svc_attack_antaran(entry['game_state'], 'player', data.get('fleet_id'))
    GameModel.save_game(g.user_id, game_id, entry['game_state'])
    return jsonify(res), 200
