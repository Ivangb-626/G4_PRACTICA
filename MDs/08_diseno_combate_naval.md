# 08 — Diseño y combate naval

## Lo que ya está implementado

- 6 ship_types en [ships.json](../backend/app/data/ships.json): frigate, destroyer, cruiser, battleship, colony_ship, transport con `hp`, `armor`, `speed`, `attack`, `defense`, `command_points`, `cost`.
- Estructura de flota con `id`, `owner`, `star_system_id`, `ships[]`, `destination`, `eta_turns`, `command_points_used`.
- Cálculo de command points usados.
- `combat_service.py` y `tactical_combat.py` existen pero **están vacíos**.

## Cambios necesarios

### Clases de naves faltantes
- [ ] Añadir a [ships.json](../backend/app/data/ships.json):
  - `titan` con doble del espacio interno del battleship, +25% shields, mayor coste de mando, requiere tech `titan_construction`.
  - `doom_star` máximo poder, requiere `doom_star_construction`, **límite 1 por imperio**.
  - `outpost_ship` para puestos avanzados.
- [ ] Marcar `requires_tech` en cada clase (titan/doom_star).
- [ ] Espacio interno (`hull_space`) por clase: frigate=10, destroyer=25, cruiser=70, battleship=150, titan=350, doom_star=750.

### Sistema de diseño de naves
Actualmente las naves son fijas. Hay que añadir:
- [ ] Modelo `ship_design`:
  ```json
  {
    "id": "design-uuid",
    "owner": "player_id",
    "name": "Falcon Mk II",
    "hull": "cruiser",
    "weapons": [
      {"id": "phasor", "count": 8, "mods": ["heavy_mount", "auto_fire"]}
    ],
    "specials": ["battle_pods", "battle_scanner", "augmented_engines"],
    "armor": "tritanium",
    "shield": "class_iii",
    "computer": "optronic",
    "drive": "ion_drive",
    "size_used": 65,
    "size_max": 70,
    "cost_pp": 350,
    "cost_bc_maint": 5,
    "command_points": 3
  }
  ```
- [ ] Endpoint `POST /api/ships/design` con validación de espacio (suma de tamaños ≤ hull_space) y techs requeridas desbloqueadas.
- [ ] Endpoint `GET /api/ships/designs` con todos los diseños del jugador.
- [ ] Endpoint `DELETE /api/ships/designs/{id}` para retirar diseños.
- [ ] La cola de construcción de colonia debe seleccionar de los diseños del imperio (no del catálogo fijo).

### Sistemas especiales
Añadir como objetos en [backend/app/data/ship_systems.json](../backend/app/data/ship_systems.json):
- [ ] `battle_pods` — +50% al hull_space efectivo del diseño.
- [ ] `battle_scanner` — +50% precisión a armas de haz.
- [ ] `structural_analyzer` — bypassea armadura, daña estructura directamente.
- [ ] `augmented_engines` — +1 speed, +25 defense.
- [ ] `reinforced_hull` — +50% structure HP.
- [ ] `heavy_armor` — -25% daño recibido por arma.
- [ ] `automated_repair_unit` — repara 20% armadura por turno de combate.
- [ ] `advanced_damage_control` — reparación completa post-combate, no ocupa espacio.
- [ ] `emission_guidance` — modifica misiles para apuntar a motores.
- [ ] `achilles_targeting` — ignora armadura adicional.
- [ ] `warp_dissipator` — impide retirada del enemigo.
- [ ] `stasis_field` — congela 1 nave enemiga por turno.
- [ ] `inertial_stabilizer` — +50 defense.
- [ ] `inertial_nullifier` — +100 defense, +1 speed.
- [ ] `lightning_field` — destruye torpedos cercanos.
- [ ] `tractor_beam` — inmoviliza nave enemiga.
- [ ] `cloaking_device` — invisible hasta atacar.
- [ ] `phasing_cloak` — invisible incluso atacando.
- [ ] `hard_shields` — -3 daño por hit.
- [ ] `time_warp_facilitator` — turno extra.
- [ ] `damper_field` — bloquea % daño según tamaño.
- [ ] `subspace_teleporter` — movimiento instantáneo.
- [ ] `troop_pods` — +marines transportados.
- [ ] `assault_shuttles` — abordaje.

### Puntos de mando
- [ ] Cada `star_base`, `battlestation`, `star_fortress` y `outpost` añade `command_points` al imperio.
- [ ] La tech `subspace_communications` añade +X command points.
- [ ] Si `command_points_used > command_points_max`, cobrar **20 BC × exceso** cada turno (lo gestiona `_compute_empire_economy`).

### Combate espacial táctico
Implementar [tactical_combat.py](../backend/app/services/tactical_combat.py) (vacío):
- [ ] Tablero hexagonal (offsets axiales) de ~30×20 hexes.
- [ ] Naves con: posición, hp, armadura por cara (4 caras: front/rear/left/right), shields, structure, weapons disponibles, init order.
- [ ] Iniciativa = base + computer + speed.
- [ ] Cada turno cada nave puede mover (≤speed hexes) y disparar.
- [ ] Cálculo `to_hit = 50 + (attack - defense) + computer_bonus + scanner_bonus + range_modifier`.
- [ ] Daño por arma (ver [09_armas.md](09_armas.md)) atraviesa: shield → armor → structure.
- [ ] Modos automáticos: agresivo / defensivo / pasivo / huida.
- [ ] Endpoint `POST /api/combat/tactical/{combat_id}/action` con `{ship_id, move_to, target, weapons}`.
- [ ] Endpoint `POST /api/combat/tactical/{combat_id}/end_turn`.
- [ ] Eventos detallados (golpes, fallos, destrucciones) emitidos al frontend.

### Combate automático
- [ ] Si el jugador desactiva el modo táctico, simular en `combat_service.py` con la misma lógica subyacente pero sin interacción.

### Frontend
- [ ] Vista [FleetManager.vue](../frontend/src/views/FleetManager.vue) con lista de flotas, ship designs, asignación de naves a flotas.
- [ ] Nueva vista `ShipDesigner.vue` con plano de la nave, slots de armas, sistemas, validador de espacio en tiempo real.
- [ ] Vista de combate táctico ([CombatResult.vue](../frontend/src/views/CombatResult.vue) actual es solo resultado): canvas hexagonal con naves, animaciones de disparo, panel de control.
