# 05 — Sistema de investigación tecnológica

## Lo que ya está implementado

- 8 ramas en [tech_tree.json](../backend/app/data/tech_tree.json) (falta una y los nombres no coinciden exactamente con las 9 oficiales).
- Servicio básico [research_service.py](../backend/app/services/research_service.py) con `process_research()`, acumulación de RP, probabilidad de completar.
- Tecnologías desbloquean edificios vía `unlocks.buildings`.
- Bonus de miniaturización: `-5% por nivel, mínimo 30%`.
- 4 tecnologías concretas en [technologies.json](../backend/app/data/technologies.json) (construction_1, sociology_1, biology_1, computers_1).

## Cambios necesarios

### Estructura de las 9 ramas
- [ ] Verificar/renombrar `tech_tree.json` para tener exactamente las 9 ramas oficiales: `construction`, `power`, `genetics`, `sociology`, `engineering`, `physics`, `computers`, `chemistry`, `force_fields`.
- [ ] Cada rama dividida en niveles (1-8) y cada nivel con 2-4 opciones mutuamente excluyentes.

### Catálogo completo de tecnologías
- [ ] Ampliar [technologies.json](../backend/app/data/technologies.json) con todas las tecnologías canónicas. Mínimo (lista no exhaustiva):
  - **Construction**: Cement, Reinforced Hull, Heavy Armor, Battle Pods, Battlestation, Star Fortress, Titan Construction, Doom Star Construction, Artificial Planet Construction.
  - **Power**: Nuclear Drive, Sub-Light Drive, Fusion Drive, Ion Drive, Anti-Matter Drive, Hyper Drive, Interphased Drive, Stellar Drive, Tritanium Armor, Zortrium Armor, Neutronium Armor, Adamantium Armor.
  - **Genetics**: Hydroponic Farm, Subterranean Farms, Weather Controller, Astro University, Gaia Transformation, Biomorphic Fungi, Death Spores, Bio-Terminator, Universal Antidote, Telepathic Training, Soldiers, Tank, Marine Tank, Battleoids, Microlite Construction.
  - **Sociology**: Federation, Galactic Currency Exchange, Star Base, Pleasure Dome, Confederation, Imperium, Galactic Unification, Holo-Simulator, Multi-Phased Shields.
  - **Engineering**: Armor Plate, Reinforced Hull, Battle Pods, Auto-Repair, Damper Field, Achilles Targeting, Augmented Engines, Inertial Stabilizer, Inertial Nullifier, Energy Absorber, Subspace Communications.
  - **Physics**: Laser Cannon, Phasor, Disruptor, Stellar Converter, Death Ray, Tachyon Beam, Mauler Device, Tractor Beam, Hard Shields, Phasing Cloak.
  - **Computers**: Optronic Computer, Pos-i-tronic Computer, Cybertronic Computer, Galactic Networking, Battle Scanner, Structural Analyzer, Holo-Simulator, Robotic Factory, Robo-Miner Plant, Cyber Security Link, Emissions Guidance.
  - **Chemistry**: Fuel Cells, Deuterium Fuel Cells, Iridium Fuel Cells, Uridium Fuel Cells, Thorium Fuel Cells, Nuclear Bomb, Merculite Missile, Pulson Missile, Zeon Missile, Anti-Matter Torpedo, Plasma Torpedo, Fighter Bay.
  - **Force Fields**: Class I-X Shields, Personal Shields, Planetary Radiation Shield, Planetary Flux Shield, Planetary Barrier Shield, Stasis Field, Warp Field Interdictor, Subspace Interdictor.

Cada tech debe llevar:
```json
{
  "id": "phasor",
  "branch": "physics",
  "level": 5,
  "tier": 2,
  "name": "Phasor",
  "rp_cost": 1500,
  "description": "...",
  "unlocks": {
    "weapons": ["phasor"],
    "buildings": [],
    "ship_systems": []
  },
  "exclusive_with": ["mauler_device", "phasing_cloak"]
}
```

### Una sola rama activa
- [ ] Modificar `set_research()` para validar que solo hay una tech activa global, no varias en paralelo.
- [ ] El frontend [TechTree.vue](../frontend/src/views/TechTree.vue) debe mostrar la rama actual con barra de progreso.

### Selección entre opciones del mismo nivel
- [ ] Al completar un nivel, presentar al jugador una pantalla modal con las 2-4 opciones para elegir UNA (a menos que sea Creativo).
- [ ] Si la raza es **Creativa**, otorgar todas las opciones automáticamente.
- [ ] Si la raza es **Uncreativa**, elegir una al azar.

### Vías alternativas de adquisición
- [ ] **Comercio tecnológico**: en [diplomacy_service.py](../backend/app/services/diplomacy_service.py), implementar acción `propose_tech_trade` con selección de tech ofrecida y solicitada.
- [ ] **Espionaje**: ver [11_diplomacia_espionaje.md](11_diplomacia_espionaje.md) — operación `steal_tech` con probabilidad de éxito.
- [ ] **Conquista**: al ganar `ground_combat.py`, ejecutar `roll_tech_capture(probability=0.3)` que otorga 1 tech aleatoria del enemigo.
- [ ] **Planetas de Artefactos**: añadir tipo de planeta `artifacts_world` en la generación; al colonizarlo el primer empire recibe 1-2 techs aleatorias.
- [ ] **Líderes**: la habilidad "Free Tech" en [leader_service.py](../backend/app/services/leader_service.py) debe otorgar 1-3 techs al contratar (ver [10_lideres.md](10_lideres.md)).
- [ ] **Guardián de Orion**: ya parcialmente implementado en `defeat_orion_guardian()`. Ver [13_monstruos_guardian.md](13_monstruos_guardian.md). Verificar que entrega `damping_field` además de las exóticas.
- [ ] **Naves Antaranas capturadas**: ver [14_antaranos.md](14_antaranos.md) — al desarmarlas, otorgar tech única antarana.

### Edificios de investigación
- [ ] En [buildings.json](../backend/app/data/buildings.json) existe `research_lab` pero faltan `research_center`, `research_institute_advanced`, `autolab` con sus fórmulas exactas:
  ```json
  {"id": "research_lab", "rp_base": 5, "rp_per_scientist": 1, ...},
  {"id": "research_center", "rp_base": 10, "rp_per_scientist": 2, ...},
  {"id": "research_institute_advanced", "rp_base": 15, "rp_per_scientist": 3, ...},
  {"id": "autolab", "rp_fixed": 30, "rp_per_scientist": 0, ...}
  ```
- [ ] `colony_service.calculate_colony_production()` debe sumar correctamente estos valores.

### Frontend del árbol tecnológico
- [ ] Vista de árbol completa con las 9 ramas, niveles, opciones mutuamente excluyentes en cada nivel.
- [ ] Tooltip con descripción, coste, prerrequisitos y desbloqueos.
- [ ] Resaltado de la rama activa y barra de progreso (%).
- [ ] Codex separado para techs exóticas (Orion/Antaran) que muestra su efecto pero indica "No investigable".
