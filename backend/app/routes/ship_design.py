from flask import Blueprint, request, jsonify, g
from pathlib import Path
from app.auth.middleware import token_required
from app.models.game import GameModel
import json
import random

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

with (DATA_DIR / "ships.json").open("r", encoding="utf-8") as f:
    SHIPS = {item["type"]: item for item in json.load(f)}

with (DATA_DIR / "weapons.json").open("r", encoding="utf-8") as f:
    WEAPONS_BLOB = json.load(f)
ALL_WEAPONS = {w["id"]: w for grp in WEAPONS_BLOB.values() for w in grp}

with (DATA_DIR / "ship_systems.json").open("r", encoding="utf-8") as f:
    SHIP_SYSTEMS = {item["id"]: item for item in json.load(f)}

with (DATA_DIR / "weapon_mods.json").open("r", encoding="utf-8") as f:
    WEAPON_MODS = {m["id"]: m for m in json.load(f)}


ship_design_bp = Blueprint('ship_design', __name__)


def _entry(game_id):
    entry = GameModel.get_game(g.user_id, game_id)
    if not entry or entry == "forbidden":
        return None
    return entry


@ship_design_bp.route('/catalog', methods=['GET'])
@token_required
def catalog(game_id):
    return jsonify({
        "hulls": [s for s in SHIPS.values() if s.get("category") == "warship"],
        "weapons": WEAPONS_BLOB,
        "ship_systems": list(SHIP_SYSTEMS.values()),
        "weapon_mods": list(WEAPON_MODS.values()),
    }), 200


@ship_design_bp.route('/', methods=['GET'])
@ship_design_bp.route('', methods=['GET'])
@token_required
def list_designs(game_id):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    designs = entry['game_state'].get('player', {}).get('ship_designs', [])
    return jsonify(designs), 200


@ship_design_bp.route('/', methods=['POST'])
@ship_design_bp.route('', methods=['POST'])
@token_required
def create_design(game_id):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    data = request.get_json() or {}
    hull = data.get('hull')
    weapons = data.get('weapons', [])
    specials = data.get('specials', [])

    hull_data = SHIPS.get(hull)
    if not hull_data or hull_data.get("category") != "warship":
        return jsonify({"error": "Invalid hull"}), 400

    size_used = 0
    cost = hull_data.get("cost", 0)
    for w in weapons:
        wid = w.get('id')
        count = int(w.get('count', 1))
        wdata = ALL_WEAPONS.get(wid)
        if not wdata:
            return jsonify({"error": f"Unknown weapon {wid}"}), 400
        size_mult = 1.0
        cost_mult = 1.0
        for mod_id in w.get('mods', []):
            mod = WEAPON_MODS.get(mod_id)
            if not mod:
                continue
            size_mult *= mod.get('size_mult', 1.0)
            cost_mult *= mod.get('cost_mult', 1.0)
        size_used += int(wdata.get('size', 0) * size_mult * count)
        cost += int(wdata.get('cost', 0) * cost_mult * count)
    for sid in specials:
        sd = SHIP_SYSTEMS.get(sid)
        if not sd:
            return jsonify({"error": f"Unknown ship system {sid}"}), 400
        size_used += sd.get('size', 0)
        cost += sd.get('cost', 0)

    hull_space = hull_data.get('hull_space', 0)
    # Battle Pods special increases hull_space by 50%
    if 'battle_pods' in specials:
        hull_space = int(hull_space * 1.5)

    if size_used > hull_space:
        return jsonify({"error": f"Design exceeds hull space ({size_used}/{hull_space})"}), 400

    design = {
        "id": f"design_{random.randint(10000, 99999)}",
        "name": data.get('name', f"{hull_data.get('name', 'Design')}"),
        "hull": hull,
        "weapons": weapons,
        "specials": specials,
        "size_used": size_used,
        "size_max": hull_space,
        "cost": cost,
        "command_points": hull_data.get('command_points', 0),
    }
    entry['game_state'].setdefault('player', {}).setdefault('ship_designs', []).append(design)
    GameModel.save_game(g.user_id, game_id, entry['game_state'])
    return jsonify(design), 201


@ship_design_bp.route('/<design_id>', methods=['DELETE'])
@token_required
def delete_design(game_id, design_id):
    entry = _entry(game_id)
    if not entry:
        return jsonify({"error": "Game not found"}), 404
    designs = entry['game_state'].get('player', {}).get('ship_designs', [])
    entry['game_state']['player']['ship_designs'] = [d for d in designs if d.get('id') != design_id]
    GameModel.save_game(g.user_id, game_id, entry['game_state'])
    return jsonify({"success": True}), 200
