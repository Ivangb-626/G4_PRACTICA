"""
council_service.py — Wrapper alrededor de la votacion del Senado Galactico.

La logica vive en diplomacy_service.check_galactic_council; este modulo expone
helpers explicitos para el consumo desde rutas / IA.
"""
from __future__ import annotations

from app.services.diplomacy_service import check_galactic_council, _make_relation_key, initialize_diplomacy


def convene_council(game_state: dict) -> dict:
    """Forza la convocatoria (util para depuracion)."""
    initialize_diplomacy(game_state)
    res = check_galactic_council(game_state)
    if res is None:
        return {"convened": False, "reason": "Conditions not met"}
    return {"convened": True, "result": res}


def player_vote(game_state: dict, candidate: str) -> dict:
    """Registra el voto del jugador para la siguiente convocatoria."""
    pending = game_state.setdefault("pending_council_vote", {})
    pending["player_choice"] = candidate
    return {"success": True, "candidate": candidate}


def estimate_council_votes(game_state: dict) -> dict:
    """Conteo de votos disponibles en este momento (poblacion total por imperio)."""
    initialize_diplomacy(game_state)
    counts = {}
    for emp in [game_state.get("player"), *game_state.get("ai_players", [])]:
        if not emp:
            continue
        owner = emp.get("id", "player")
        pop = sum(
            c.get("population", {}).get("total", 0) if isinstance(c.get("population"), dict) else 0
            for c in emp.get("colonies", [])
        )
        counts[owner] = pop
    total = sum(counts.values()) or 1
    needed_two_thirds = total * 2 / 3
    return {"votes": counts, "total": total, "needed_two_thirds": needed_two_thirds}
