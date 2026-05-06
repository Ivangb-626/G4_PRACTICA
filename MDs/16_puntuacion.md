# 16 — Sistema de puntuación

## Lo que ya está implementado

- Esquema `HallOfFameModel.add_entry()` y `get_top_entries()` en [game.py](../backend/app/models/game.py).
- Campo `victory_condition` en game_state.
- `turn` tracked.

**No** existe la fórmula de cálculo.

## Cambios necesarios

### Servicio de score
Crear `backend/app/services/score_service.py`:
- [ ] `calculate_final_score(game_state, empire_id) -> dict` que devuelva el desglose completo:
  ```python
  {
      "base": max(0, 500 - game_state["turn"]),
      "captured_colonists": captured_pop * 2,
      "own_population": own_pop * 1,
      "hyper_advanced_techs": ha_tech_count * 5,
      "rivals_eliminated": rivals * 50,
      "guardian_defeated": 100 if defeated else 0,
      "antarans_defeated": 200 if defeated else 0,
      "galactic_ruler": 50 or 100 or 0,
      "subtotal": <sum>,
      "custom_race_multiplier": 1.0 to 1.5,
      "final": int(subtotal * multiplier)
  }
  ```

### Cálculo de cada componente
- [ ] `base = max(0, 500 - turn)`.
- [ ] `captured_colonists`:
  - Trackear durante la partida en `empire["stats"]["captured_colonists"]` (incrementar cada vez que se conquista o asimila pop).
  - 2 puntos por cada uno.
- [ ] `own_population`:
  - Suma de population entera de todas las colonias propias al final.
- [ ] `hyper_advanced_techs`:
  - Las "Hiper-Avanzadas" son las del último nivel del árbol (e.g. Stellar Converter, Doom Star Construction, Death Spores). Marcar `tier: "hyper_advanced"` en `technologies.json` para identificarlas.
  - Contar cuántas tiene el imperio investigadas.
- [ ] `rivals_eliminated`:
  - Trackear en `empire["stats"]["rivals_eliminated"]` cuando una IA queda con 0 colonias y 0 flotas y el último ataque fue del jugador.
- [ ] `guardian_defeated`:
  - Setear `empire["stats"]["guardian_defeated"] = True` en `defeat_orion_guardian()`.
- [ ] `antarans_defeated`:
  - Setear cuando `antaran_homeworld_conquered` y el conquistador es este imperio.
- [ ] `galactic_ruler`:
  - +50 si fue elegido con margen ajustado (66-79% de votos).
  - +100 si fue elegido por amplia mayoría (≥80%).

### Multiplicador de raza custom
- [ ] El porcentaje base es 100%.
- [ ] Si la raza es custom: `multiplier = 1.0 + (10 - picks_used) * 0.025`. Es decir, una raza con menos picks gastados → más difícil → más bonus. (Ajustar la constante para que el rango quede en [1.0, 1.5].)
- [ ] Las razas predefinidas tienen multiplicadores fijos según su balance histórico:
  - Psilons: 0.95 (potentes).
  - Klackons: 0.95.
  - Silicoids: 1.0.
  - Sakkra: 1.0.
  - Bulrathi/Mrrshans/Alkari: 1.05.
  - Otros: 1.0.

### Persistencia
- [ ] Al detectar victoria o derrota, llamar `score_service.calculate_final_score()` y persistir en `HallOfFameModel`:
  - `score_total`, `victory_type`, `race`, `difficulty`, `galaxy_size`, `turns_played`, `breakdown` (JSON).

### Hall of Fame
- [ ] Endpoint `GET /api/hall_of_fame` con paginación y filtros (raza, dificultad, victoria).
- [ ] Vista frontend con tabla rankeable.

### Frontend
- [ ] Pantalla post-victoria muestra el desglose línea por línea:
  ```
  Base (500 - 187 turnos):           313
  Colonistas capturados (×2):         84
  Población propia (×1):             142
  Tecnologías Hiper-Avanzadas (×5):   25
  Rivales eliminados (×50):          150
  Guardián derrotado:                100
  Antaranos derrotados:              200
  ───────────────────────────────────────
  Subtotal:                         1014
  Multiplicador raza (×1.10):       1115
  ```
- [ ] Botón "Guardar en Hall of Fame".
