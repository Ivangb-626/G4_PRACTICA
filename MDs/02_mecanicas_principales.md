# 02 — Mecánicas principales de juego

## Lo que ya está implementado

- `TurnEngine.execute_turn()` en [turn_engine.py](../backend/app/services/turn_engine.py) procesa colonias → investigación → flotas → eventos.
- Cálculo de producción por colonia en [colony_service.py](../backend/app/services/colony_service.py) → `calculate_colony_production()` (food/industry/research/BC).
- Movimiento de flotas con ETA (la nave más lenta determina la velocidad) en `move_fleet()`.
- Persistencia: `GameModel.save_game()` con timestamp `last_saved`.
- Estructura del estado de juego con `player`, `ai_players`, `galaxy`, `diplomacy`.

## Cambios necesarios

### Inicio de la partida
- [ ] Verificar que el imperio inicial reciba **1 colony ship + 2 scouts** (el PDF lo especifica). Si actualmente recibe otra cosa, ajustar `_initial_empire()` en `game_service.py`.
- [ ] La nave colonizadora debe poder fundar inmediatamente una colonia (acción "Found Colony" en `fleet.py`).

### Agujeros negros
- [ ] Añadir tipo de sistema `black_hole` en la generación de galaxia.
- [ ] Los `black_hole` no contienen planetas (excluir generación de planets para ese system).
- [ ] Al mover una flota a un black_hole sin líder con habilidad **Navigator**: aplicar destrucción probabilística (p.ej. 50% de pérdida por nave).
- [ ] Si la flota lleva un líder Navigator, paso libre.
- [ ] Mostrar advertencia visual en [galaxyRenderer.ts](../frontend/src/canvas/galaxyRenderer.ts) y bloqueo de movimiento confirmado.

### Asignación de población
- [ ] Confirmar que la pantalla de colonia ([ColonyView.vue](../frontend/src/views/ColonyView.vue)) permite mover trabajadores entre **farmer / worker / scientist** con sliders y muestra producción resultante en tiempo real.
- [ ] Validación: la suma debe igualar la población total; los androides cuentan aparte.

### Autosave cada 4 turnos
- [ ] En `TurnEngine.execute_turn()` añadir al final:
  ```python
  if game_state["turn"] % 4 == 0:
      GameModel.save_game(game_id, game_state, autosave=True)
  ```
- [ ] Mantener un slot de autosave separado del save manual para no sobreescribirlo.
- [ ] Mostrar notificación "Autosaved" en frontend.

### Ciclo de fin de turno
- [ ] El orden actual (colonias → research → fleets → events) debe completarse con: **resolución de combates espaciales pendientes**, **resolución de combate terrestre**, **acciones de IA**, **eventos antaranos**, **chequeo de victoria**.
- [ ] Mostrar resumen de fin de turno en frontend con: tecnologías completadas, edificios terminados, naves construidas, conflictos diplomáticos, ataques recibidos.

### Menú de información
El PDF describe un menú de info amplio. Necesita:
- [ ] **Gráfico histórico comparativo**: serie temporal por imperio de población, producción, investigación, flota total, BC. Persistir snapshots cada N turnos en el game_state. Vista nueva `HistoryView.vue` con un canvas de líneas (puede usar Chart.js o canvas simple).
- [ ] **Pantalla de razas**: lista de civilizaciones contactadas con sus rasgos, gobierno, relación diplomática actual. Añadir endpoint `/api/races/contacted` que devuelva solo razas conocidas.
- [ ] **Lista de tecnologías investigadas**: ya existe parcialmente vía [TechTree.vue](../frontend/src/views/TechTree.vue), pero falta una vista filtrada de "ya investigadas".
- [ ] **Descripciones de tecnologías exóticas (Orion/Antaran)**: aunque no investigables, deben mostrarse en el codex con su efecto descrito.

### Acciones IA
- [ ] El servicio [ai_service.py](../backend/app/services/ai_service.py) debe ejecutar al final de cada turno: gestión de colonias enemigas, decisiones de investigación, movimientos de flotas, propuestas diplomáticas, declaración de guerra según relación.
- [ ] Personalidad por raza (agresiva/pacífica/comerciante/militarista) que sesgue las decisiones.

### Fog of War
- [ ] Verificar el filtrado en [galaxy.py](../backend/app/routes/galaxy.py): el frontend solo debe ver sistemas explorados o en rango de sensores; el resto en negro o con datos de "última visita".

### Eventos aleatorios
- [ ] Implementar [event_service.py](../backend/app/services/event_service.py) (vacío). Eventos sugeridos: plaga (pierde 1 pop), supernova (destruye sistema), descubrimiento arqueológico (gana tech), brote de comunismo (cambio de gobierno temporal), líder ofreciéndose, etc.
- [ ] Generar al final del turno con probabilidad baja (~5%).
