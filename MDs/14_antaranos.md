# 14 — Los Antaranos

## Lo que ya está implementado

- `antaran_next_attack_turn = 15 + random(0..5)` en `game_service.py`.
- Campo `antaran_homeworld_conquered` en game_state.
- [antaran_service.py](../backend/app/services/antaran_service.py) **vacío**.
- Comprobación de victoria si `antaran_homeworld_conquered == true`.

## Cambios necesarios

### Configuración
- [ ] El flag `antaran_attacks_enabled` debe ser real (ver [01_configuracion_partida.md](01_configuracion_partida.md)).
- [ ] Si `False`: no inicializar `antaran_next_attack_turn`, no permitir construir `dimensional_portal`, suprimir el sistema Antara.

### Schedule de ataques
- [ ] Modificar el valor inicial del próximo ataque para alinearlo con el rango canónico **100 a 350**:
  - Primer ataque: turno aleatorio entre 100 y 150.
  - Siguientes ataques: cada `30 + random(0..30)` turnos hasta que el imperio sea destruido.
- [ ] Implementar en [antaran_service.py](../backend/app/services/antaran_service.py):
  - `should_attack(turn)` → bool.
  - `generate_attack_fleet(turn)` → genera una flota Antarana cuyo poder escala con el turno (más naves o naves más avanzadas en turnos altos).
  - `select_target(empire_list)` → elige una colonia aleatoria entre todos los imperios (no solo el jugador).
  - `execute_attack(fleet, target_colony)` → resuelve combate; si los defensores pierden, los Antaranos **destruyen** la colonia (no la conquistan).

### Naves Antaranas
- [ ] Definir varias clases de nave Antarana en `ships.json` con prefijo `antaran_`:
  - `antaran_destroyer`, `antaran_cruiser`, `antaran_battleship`, `antaran_titan`, `antaran_doom_star`.
  - Stats superiores (~50% más potentes que su contraparte humana del mismo tier).
  - Equipadas con armas exóticas: `xeno_psychology`, `disruptor`, `phasing_cloak`, `stellar_converter`.

### Captura de naves Antaranas
- [ ] En el resolutor de combate, si una nave Antarana queda con HP positivo pero sin tripulación (vía `assault_shuttles` o `troop_pods`), capturarla.
- [ ] Probabilidad de **autodestrucción**: 60%. Si se autodestruye, no se obtiene nada.
- [ ] Si no se autodestruye:
  - Opción 1: añadirla a la flota del jugador (sin posibilidad de replicarla).
  - Opción 2: desarmarla → otorga 1 tecnología única antarana entre las aún no investigadas.
- [ ] Endpoint `POST /api/fleets/{id}/dismantle_antaran/{ship_id}`.

### Portal Dimensional
- [ ] Añadir la tecnología `dimensional_portal` al árbol (rama Construcción o Ingeniería, nivel alto).
- [ ] Solo aparece si `antaran_attacks_enabled == true`.
- [ ] Una vez investigada, permite construir el edificio `dimensional_portal_facility` (coste 800 PP) en una colonia.
- [ ] Tras construirlo, aparece el **sistema Antara** en el mapa galáctico (puede ser un sistema oculto que se desvela).
- [ ] Solo flotas con un origen que tenga `dimensional_portal_facility` pueden viajar a Antara.

### Sistema Antara
- [ ] Crear un sistema especial (no en el mapa convencional) generado al activarse Antaran Attacks:
  - 1 planeta home Antarano con población masiva (e.g. 50).
  - Defendido por un capital ship antarano (la "DoomStar Antarana") y varias escoltas.
- [ ] Si el jugador captura el planeta home (combate terrestre exitoso tras combate espacial), `antaran_homeworld_conquered = True`.

### Victoria Antarana
- [ ] Al setear `antaran_homeworld_conquered = True`:
  - `victory_condition = "antaran_conquest"`.
  - +200 al score (ver [16_puntuacion.md](16_puntuacion.md)).
  - Pantalla de victoria especial con cinemática.

### Diplomacia
- [ ] Antaranos NO aparecen en la pantalla de Diplomacia. Si aparecen, todas las acciones devuelven "Communication impossible".

### Frontend
- [ ] Notificación pop-up cuando ocurre un ataque Antarano: "An Antaran fleet has emerged near system X!".
- [ ] Sistema Antara en el mapa: marker rojo distintivo, accesible solo si se tiene Portal Dimensional.
- [ ] Codex con la historia de los Antaranos en menú de información.
