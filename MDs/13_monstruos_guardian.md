# 13 — Monstruos espaciales y el Guardián de Orion

## Lo que ya está implementado

- Sistema Orion con guardian fleet (1 cruiser + 2 destroyers) en [game_service.py](../backend/app/services/game_service.py).
- Estructura: `orion["guardian"] = {"active": True, "fleet": {...}}`.
- 3 tipos de monstruos generados (`space_crystal`, `space_amoeba`, `space_eel`) en ~10% de sistemas no-Orion.
- `defeat_orion_guardian()` otorga 3 techs exóticas y un acorazado Avenger.
- Lista de exóticas: `phasing_cloak`, `stellar_converter`, `death_ray`, `doom_star_hull`, `antaran_xeno_psychology`.
- [creature_service.py](../backend/app/services/creature_service.py) — vacío.

## Cambios necesarios

### Catálogo de monstruos
- [ ] Crear [backend/app/data/space_monsters.json](../backend/app/data/space_monsters.json):
  ```json
  [
    {
      "id": "space_eel",
      "name": "Space Eel",
      "hp": 80, "armor": 50, "shields": 30,
      "speed": 5, "attack": 60, "defense": 40,
      "weapons": [{"id": "eel_bite", "damage_min": 5, "damage_max": 15, "shots": 1}],
      "tier": 1
    },
    {
      "id": "space_kraken",
      "name": "Space Kraken",
      "hp": 200, "armor": 120, "shields": 80,
      "weapons": [{"id": "kraken_tentacle", "damage_min": 15, "damage_max": 40, "shots": 4}],
      "tier": 2
    },
    {
      "id": "crystal_monolith",
      "name": "Crystal Monolith",
      "hp": 500, "armor": 400, "shields": 200,
      "damage_resistance": {"physical": 0.5},
      "weapons": [{"id": "crystal_beam", "damage_min": 30, "damage_max": 60}],
      "tier": 3
    },
    {
      "id": "cosmic_dragon",
      "name": "Cosmic Dragon",
      "hp": 800, "armor": 500, "shields": 400,
      "weapons": [
        {"id": "dragon_breath", "damage_min": 50, "damage_max": 100, "envelope": true}
      ],
      "tier": 4
    },
    {
      "id": "guardian_of_orion",
      "name": "Guardian of Orion",
      "hp": 2000, "armor": 1500, "shields": 1000,
      "weapons": [
        {"id": "guardian_phasor", "damage_min": 50, "damage_max": 200, "shots": 8},
        {"id": "guardian_torpedo", "damage_min": 200, "damage_max": 400, "shots": 2}
      ],
      "specials": ["damper_field", "battle_scanner", "phasing_cloak"],
      "tier": 5,
      "unique": true
    }
  ]
  ```

### Generación
- [ ] Reemplazar la generación actual con tier-aware: cuanto más rico el sistema, más probable un monstruo de tier alto.
- [ ] Sistema Orion: forzar `guardian_of_orion` activo si el flag de configuración está on.

### Implementar [creature_service.py](../backend/app/services/creature_service.py)
- [ ] `spawn_monster(system, type)` — coloca el monstruo en el sistema.
- [ ] `monster_movement(turn)` — algunos monstruos se mueven entre sistemas (Space Eel/Kraken pueden deambular).
- [ ] `monster_combat(monster, fleet)` — usa la lógica de [tactical_combat.py](../backend/app/services/tactical_combat.py) tratando al monstruo como una nave especial.
- [ ] `defeat_monster(monster, fleet)` — al ganar:
  - Permite colonizar el sistema previamente bloqueado.
  - Probabilidad pequeña de obtener tech especial (e.g. Cosmic Dragon → bonus a tech biológica).
  - **Guardián de Orion**: ver bloque dedicado abajo.
- [ ] El líder con habilidad **Galactic Lore** otorga +daño contra monstruos.

### Derrotar al Guardián
Ampliar `defeat_orion_guardian()`:
- [ ] Garantizar la concesión de la tech **Damping Field** (nuevo: añadir a la lista de techs Orion exclusivas).
- [ ] Spawnear al líder **Loknar** (ver [10_lideres.md](10_lideres.md)) con su Acorazado Orion único.
- [ ] Permitir colonizar el planeta natal de Orion: el `orion_homeworld` debe tener clima Gaia, riqueza ultra_rich, tamaño huge, sin penalizaciones.
- [ ] Sumar **+100 al score** del jugador (ver [16_puntuacion.md](16_puntuacion.md)).
- [ ] Marcar `game_state["orion_defeated_by"] = empire_id` para que el flag sea único.

### Frontend
- [ ] Marker visual distinto en [galaxyRenderer.ts](../frontend/src/canvas/galaxyRenderer.ts) para sistemas con monstruo (icono de calavera o tentáculo).
- [ ] Modal pre-combate al entrar en sistema con monstruo: muestra stats estimados (si el jugador tiene scanner), opción de retirarse.
- [ ] Pantalla especial al derrotar al Guardián: cinemática o splash con notificación de recompensas.
