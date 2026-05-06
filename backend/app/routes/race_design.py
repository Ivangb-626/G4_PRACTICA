"""
race_design — Catalogo de picks y validacion de raza personalizada.

Nota: el proyecto solo soporta tres razas predefinidas (Alkari, Meklar, Trilarian).
Estas rutas exponen el catalogo de picks por completitud y permiten construir
una raza custom para futuras partidas, pero no son obligatorias para el flujo
estandar.
"""
from flask import Blueprint, request, jsonify
from pathlib import Path
import json

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

with (DATA_DIR / "race_picks.json").open("r", encoding="utf-8") as f:
    PICKS = json.load(f)


race_design_bp = Blueprint('race_design', __name__)


@race_design_bp.route('/options', methods=['GET'])
def options():
    return jsonify(PICKS), 200


@race_design_bp.route('/validate', methods=['POST'])
def validate():
    data = request.get_json() or {}
    picks = data.get('picks', [])
    advantages = {a['id']: a for a in PICKS.get('advantages', [])}
    disadvantages = {d['id']: d for d in PICKS.get('disadvantages', [])}

    total_cost = 0
    flags = {}
    seen = set()
    for pid in picks:
        if pid in seen:
            return jsonify({"valid": False, "error": f"Duplicate pick: {pid}"}), 200
        seen.add(pid)
        if pid in advantages:
            total_cost += advantages[pid]['cost']
            flags.update(advantages[pid].get('flags', {}))
        elif pid in disadvantages:
            total_cost += disadvantages[pid]['cost']
            flags.update(disadvantages[pid].get('flags', {}))
        else:
            return jsonify({"valid": False, "error": f"Unknown pick: {pid}"}), 200

    if 'creative' in flags and 'uncreative' in flags:
        return jsonify({"valid": False, "error": "Creative and Uncreative are mutually exclusive"}), 200

    budget = PICKS.get('budget', 10)
    if total_cost > budget:
        return jsonify({"valid": False, "error": f"Picks cost {total_cost}, budget is {budget}"}), 200

    return jsonify({"valid": True, "cost": total_cost, "flags": flags}), 200
