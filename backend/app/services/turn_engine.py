"""
turn_engine.py — Helper que delega en game_service.end_turn() para conservar la
secuencia canonica del juego (orden documentado en game_service.end_turn()):

1. Empire economy (food/PP/RP/BC)
2. Colony build queue
3. Research progress
4. Fleet movement
5. Space combat resolution
6. AI per-empire decisions (via ai-service)
7. Diplomacy maintenance
8. Espionage missions
9. Galactic Council check
10. Antaran activation/attacks
11. Ground assimilation
12. Random events
13. Victory check + autosave
"""
from __future__ import annotations


class TurnEngine:
    @staticmethod
    def execute_turn(game_state: dict) -> dict:
        from app.services.game_service import end_turn
        return end_turn(game_state)
