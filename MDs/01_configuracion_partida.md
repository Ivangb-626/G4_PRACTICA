# 01 — Configuración de partida

## Lo que ya está implementado

- Generación de galaxia para 3 tamaños (small=20 sistemas, medium=30, large=40) en [backend/app/services/game_service.py](../backend/app/services/game_service.py) → `generate_galaxy()`.
- Marco de escenarios `SCENARIOS[]` con `max_opponents`, `galaxy_sizes`, `difficulty_options`.
- Inicialización del estado del juego con contador de turnos en `GameModel.create_game()` y `generate_game_state()`.
- Disparador Antarano: `antaran_next_attack_turn = 15 + random(0..5)`.
- 3 niveles de dificultad: `["easy", "normal", "hard"]`.

## Cambios necesarios

### Tamaño de galaxia
- [ ] Añadir el tamaño **Enorme** (huge, ~50-60 sistemas) a `generate_galaxy()`.
- [ ] Exponer el selector en el formulario de creación de partida del frontend ([frontend/src/views/Dashboard.vue](../frontend/src/views/Dashboard.vue)).

### Edad de la galaxia
- [ ] Añadir el campo `galaxy_age` al estado del juego (`Temprana`/`Media`/`Tardía`).
- [ ] Modificar la generación de planetas en `generate_galaxy()` para aplicar:
  - Temprana → más planetas Gaia/Templados, más minerales ricos, más monstruos.
  - Media → distribución equilibrada (estado actual).
  - Tardía → más planetas tóxicos/radiactivos/áridos, menos recursos.

### Número de razas
- [ ] Permitir elegir entre 2 y 8 oponentes (actual `max_opponents` está limitado por escenario).
- [ ] Validación de razas duplicadas si el usuario fija razas específicas.

### Niveles de dificultad
- [ ] Renombrar/expandir a los 5 oficiales: `gardener`, `officer`, `commander`, `lord`, `impossible`.
- [ ] Implementación detallada en [17_dificultad.md](17_dificultad.md).

### Tecnología inicial
- [ ] Añadir el campo `starting_tech_level` con valores `pre_warp`, `average`, `advanced`.
- [ ] En `generate_game_state()` desbloquear automáticamente las tecnologías iniciales según el nivel:
  - **Pre-Warp** → solo casco de fragata, motor base, láser básico, sin colony ship Warp.
  - **Average** → equivalente al estado actual (motor warp, fragata/destructor, laser/missile básico).
  - **Advanced** → varias tecnologías de nivel 1-3 desbloqueadas en cada rama.

### Eventos aleatorios
- [ ] Activar/desactivar el flag `random_events_enabled` en el estado.
- [ ] Implementar el [event_service.py](../backend/app/services/event_service.py) (actualmente vacío) con eventos: plagas, descubrimientos arqueológicos, supernova, piratas, sequías, accidentes industriales, etc.
- [ ] El `TurnEngine` debe consultar este servicio cada turno si el flag está on.

### Ataque Antarano
- [ ] Añadir flag `antaran_attacks_enabled` (actualmente siempre on).
- [ ] Si está off, suprimir la inicialización de `antaran_next_attack_turn` y la generación del Portal Dimensional. Ver [14_antaranos.md](14_antaranos.md).

### Guardián de Orion
- [ ] Añadir flag `orion_guardian_enabled`.
- [ ] Si está off, generar Orion sin defensores en `generate_galaxy()` (eliminar el bloque que añade el guardian fleet en `orion["guardian"]`).

### Frontend de configuración
- [ ] Crear/ampliar la vista de creación de partida con todos los selectores (actualmente parece reducida).
- [ ] Mostrar previsualización: número estimado de sistemas, oponentes, descripción de cada opción.
