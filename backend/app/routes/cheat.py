from flask import Blueprint, request, jsonify, g
from app.auth.middleware import token_required
from app.models.game import GameModel
from app.services.game_service import apply_cheat
from app.logging_config import get_logger

logger = get_logger('cheats')
cheat_bp = Blueprint('cheat', __name__)


def _entry(game_id):
    entry = GameModel.get_game(g.user_id, game_id)
    if not entry or entry == "forbidden":
        return None
    return entry


@cheat_bp.route('/', methods=['POST'])
@cheat_bp.route('', methods=['POST'])
@token_required
def apply(game_id):
    entry = _entry(game_id)
    if not entry:
        logger.warning(f"Cheat access denied: game {game_id} not found or forbidden for user {g.user_id}")
        return jsonify({"error": "Game not found"}), 404
    data = request.get_json() or {}
    code = data.get('code') or data.get('cheat_code')
    target = data.get('target')
    try:
        result = apply_cheat(entry['game_state'], code, target)
        logger.info(f"CHEAT APPLIED: user={g.user_id}, game={game_id}, code={code}, target_type={target.get('type') if target else None}")
    except ValueError as e:
        logger.warning(f"Invalid cheat: user={g.user_id}, game={game_id}, code={code}, error={str(e)}")
        return jsonify({"error": str(e)}), 400
    GameModel.save_game(g.user_id, game_id, entry['game_state'])
    return jsonify(result), 200


@cheat_bp.route('/codes', methods=['GET'])
@token_required
def list_cheat_codes(game_id):
    codes = [
        "recursos_infinitos",
        "revelar_galaxia",
        "tecnologia_total",
        "flota_invencible",
        "victoria_inmediata",
        "derrota_inmediata",
        "colonizar_todo",
        "poblacion_maxima",
        "naves_gratis",
        "guardian_eliminado",
        "antaranos_desactivados",
        "rushbuy",
        "crunch",
    ]
    return jsonify(codes), 200
