# 10 — Líderes (Héroes)

## Lo que ya está implementado

- Rutas stub: `/list_hired_leaders`, `/available`, `/hire` en [leaders.py](../backend/app/routes/leaders.py).
- Marco de "máximo 4 por tipo" no enforzado.
- [leader_service.py](../backend/app/services/leader_service.py) sin lógica.

## Cambios necesarios

### Modelo de datos
- [ ] Crear [backend/app/data/leaders.json](../backend/app/data/leaders.json) con un pool de ~40 líderes (mezcla de tipos de habilidades, niveles, costes):
  ```json
  [
    {
      "id": "leader_001",
      "name": "Tarken Volok",
      "type": "colony",
      "level": 3,
      "skills": [
        {"id": "researcher", "value": 30},
        {"id": "famous", "value": 20}
      ],
      "free_techs": 0,
      "hire_cost": 250,
      "upkeep_per_turn": 12,
      "portrait": "leaders/tarken.png"
    },
    {
      "id": "loknar",
      "name": "Loknar",
      "type": "ship",
      "level": 10,
      "unique": true,
      "spawn_condition": "guardian_defeated",
      "skills": [{"id": "galactic_lore", "value": 50}],
      "ship": {"hull": "orion_battleship", "weapons": [...], "specials": [...]}
    }
  ]
  ```
- [ ] Reglas de aparición: cada N turnos, hay probabilidad de que aparezca un líder aleatorio. La probabilidad se modifica por:
  - Carismático (+50%).
  - Líder Famoso ya contratado (+25% por cada uno).

### Lógica del servicio
- [ ] [leader_service.py](../backend/app/services/leader_service.py) debe implementar:
  - `roll_available_leaders(empire)` → genera un pool disponible.
  - `hire_leader(empire, leader_id)` → cobra `hire_cost`, asigna a la nómina, marca `hired_at_turn`.
  - `assign_leader(empire, leader_id, target_id)` → asigna a colonia o flota.
  - `unassign_leader(empire, leader_id)` → libera al líder (al pool del imperio).
  - `dismiss_leader(empire, leader_id)` → despedir; si tiene habilidad "free_tech", intenta quedárselas (con riesgo).
  - `expire_unhired_leaders(empire)` → tras 30 turnos sin ser contratado, sale del pool.
  - `pay_upkeep(empire)` → cada turno descuenta `upkeep_per_turn`.

### Aplicación de habilidades

Colonia (al asignar a una colonia, modifican sus cálculos):
- [ ] **Agricultor**: `food_per_farmer += value%`.
- [ ] **Obrero**: `pp_per_worker += value%`.
- [ ] **Investigador**: `rp_per_scientist += value%`.
- [ ] **Megafortuna**: `bc_bonus_per_turn += value`.
- [ ] **Instructor**: la colonia da +exp a las naves construidas en ella.
- [ ] **Famoso**: aumenta la probabilidad de aparición de líderes (a nivel imperio).
- [ ] **Espiritual**: bonus a todos los roles (food/pp/rp/bc).
- [ ] **Medioambiental**: -contaminación.
- [ ] **Tecnología gratis**: en el momento de contratar, otorgar 1-3 techs aleatorias.
- [ ] **Espía** / **Contraespionaje**: aplicar bonos en [espionage_service.py](../backend/app/services/espionage_service.py).
- [ ] **Protector Mental**: añade flag `mind_shield: true` a la colonia para resistir Mind Control de Telepáticos.

Nave (al asignar a flota, modifican el combate):
- [ ] **Raider**: +X attack a todas las naves.
- [ ] **Defender**: +X defense.
- [ ] **Navigator**: +X speed; protege de agujeros negros (ver [02_mecanicas_principales.md](02_mecanicas_principales.md)).
- [ ] **Engineer**: aplica reparación durante combate.
- [ ] **Fighter Pilot**: +ataque/defensa a cazas.
- [ ] **Galactic Lore**: revela info de sistemas estelares al sobrevolar; +daño contra monstruos espaciales.
- [ ] **Trader**: +X% a ingresos de tratados comerciales del imperio.

### Límites
- [ ] **4 líderes de colonia + 4 de nave** por defecto.
- [ ] El rasgo `charismatic` del imperio aumenta el límite a 5+5 y reduce el `hire_cost` un 50%.
- [ ] Configuración para subir el límite si se quiere (parche 1.50 lo hizo configurable).

### Eventos
- [ ] Cada N turnos (o tras un evento), notificación "Un líder solicita unirse: <nombre>". El jugador puede contratar o rechazar.
- [ ] Si rechaza, sigue disponible 30 turnos en el pool del imperio (luego desaparece).

### Loknar
- [ ] Crear entrada especial en `leaders.json` (ver bloque arriba).
- [ ] Spawn solo cuando `defeat_orion_guardian()` es llamado con éxito.
- [ ] Comanda un acorazado especial (`orion_battleship`) con stats máximos: prefijar diseño en datos.

### Frontend
- [ ] [LeadersView.vue](../frontend/src/views/LeadersView.vue) actual: ampliar a:
  - Lista de líderes contratados (con su asignación actual).
  - Lista de líderes disponibles (con turnos restantes para que se vayan).
  - Botón contratar / despedir / asignar / reasignar.
  - Modal con habilidades, valor numérico, ship sprite si tienen nave.
