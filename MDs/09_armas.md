# 09 — Tipos de armas

## Lo que ya está implementado

- En `ships.json` existe el campo `attack` monolítico, sin distinción por arma.
- No hay catálogo de armas como entidad separada.
- No hay modificadores ni bombas planetarias.

## Cambios necesarios

### Catálogo de armas
- [ ] Crear [backend/app/data/weapons.json](../backend/app/data/weapons.json) con todas las armas:
  ```json
  {
    "beam": [
      {
        "id": "laser",
        "name": "Laser Cannon",
        "type": "beam",
        "damage_min": 1, "damage_max": 4,
        "range": 7,
        "size": 15,
        "cost": 8,
        "tech_required": "laser",
        "attack_bonus": 50,
        "available_mods": ["co", "nr", "ap", "hm", "pd", "af"]
      },
      {"id": "mass_driver", ...},
      {"id": "ion_cannon", "special": "damage_systems", ...},
      {"id": "phasor", "damage_min": 4, "damage_max": 16, ...},
      {"id": "tachyon_beam", "shield_piercing_partial": true, ...},
      {"id": "graviton_beam", "shield_bypass": true, ...},
      {"id": "plasma_cannon", "enveloping": true, ...},
      {"id": "disruptor", ...},
      {"id": "stellar_converter", "planet_destroyer": true, ...}
    ],
    "missile": [
      {"id": "nuclear_missile", "interceptable": true, ...},
      {"id": "merculite_missile", "available_mods": ["mirv", "eccm"], ...},
      {"id": "pulson_missile", ...},
      {"id": "zeon_missile", ...},
      {"id": "scatter_pack_v", "splits_on_impact": true, ...}
    ],
    "torpedo": [
      {"id": "anti_matter_torpedo", "interceptable": false, ...},
      {"id": "plasma_torpedo", ...},
      {"id": "doom_star_torpedo", "max_damage": true, ...}
    ],
    "fighter": [
      {"id": "interceptor", ...},
      {"id": "bomber", ...},
      {"id": "heavy_fighter", ...}
    ],
    "bombs": [
      {"id": "nuclear_bomb", "ground_damage": ..., "tech_required": "..."},
      {"id": "bio_terminator", ...},
      {"id": "death_spores", ...},
      {"id": "neutronium_bomb", ...}
    ]
  }
  ```

### Catálogo de modificadores
- [ ] Crear [backend/app/data/weapon_mods.json](../backend/app/data/weapon_mods.json):
  ```json
  [
    {"id": "co", "name": "Continuous", "size_mult": 2.0, "cost_mult": 2.0, "accuracy_bonus": 25},
    {"id": "nr", "name": "No Range Dissipation", "size_mult": 1.5, "cost_mult": 1.5},
    {"id": "sp", "name": "Shield Piercing", "size_mult": 2.0, "cost_mult": 2.0, "shield_pierce": true},
    {"id": "ap", "name": "Armor Piercing", "size_mult": 1.5, "cost_mult": 1.5, "armor_pierce": true},
    {"id": "hm", "name": "Heavy Mount", "size_mult": 2.0, "cost_mult": 2.0, "damage_mult": 1.5, "range_mult": 2},
    {"id": "pd", "name": "Point Defense", "size_mult": 0.5, "cost_mult": 0.5, "damage_mult": 0.5, "range_mult": 0.5, "accuracy_bonus": 25},
    {"id": "env", "name": "Enveloping", "size_mult": 2.0, "cost_mult": 2.0, "envelope": true},
    {"id": "af", "name": "Auto Fire", "size_mult": 2.0, "cost_mult": 2.0, "shots": 3, "accuracy_per_shot": -20},
    {"id": "mirv", "name": "MIRV", "size_mult": 2.0, "cost_mult": 2.0, "warheads": 4},
    {"id": "eccm", "name": "ECCM", "size_mult": 1.5, "cost_mult": 1.5, "accuracy_bonus": 25}
  ]
  ```

### Aplicación en combate
- [ ] [tactical_combat.py](../backend/app/services/tactical_combat.py) debe calcular daño por arma:
  ```python
  def fire_weapon(attacker, defender, weapon, mods):
      to_hit = base_attack + computer + scanner + range_mod - defender.defense
      if random < to_hit:
          damage = roll(weapon.damage_min, weapon.damage_max) * mods_damage_mult
          if weapon.shield_bypass: damage_to_structure(defender, damage)
          else if mod.shield_pierce: damage_to_armor(defender, damage)
          else: damage_through_shields(defender, damage, side)
  ```
- [ ] **Enveloping**: aplicar daño a los 4 cuadrantes de escudo del objetivo.
- [ ] **Plasma**: idem (envelope intrínseco).
- [ ] **Tachyon**: ignora 50% del shield level.
- [ ] **Auto Fire**: 3 tiradas con accuracy -20% acumulativo.
- [ ] **MIRV**: el misil se divide en N cabezas al llegar; cada cabeza puede ser interceptada por separado.
- [ ] **Point Defense**: dispara automáticamente contra misiles entrantes.
- [ ] **Stellar Converter**: si dispara contra un planeta, lo destruye permanentemente (todas las pop, edificios, marines a 0).

### Bombas planetarias
- [ ] Cuando una flota orbita una colonia enemiga, antes de invadir el jugador puede ordenar "Bombardear":
  - Por cada bomba a bordo, aplicar daño aleatorio a marines, población y edificios.
  - Diferentes tipos: nuclear (daño físico), bio_terminator (mata pop, no edificios), death_spores (efectos durante varios turnos), neutronium (máximo daño).
- [ ] Las razas **Telepáticas** pueden saltarse esto y usar Mind Control directamente (ver [12_combate_terrestre.md](12_combate_terrestre.md)).

### Frontend
- [ ] En el diseñador de naves (ver [08_diseno_combate_naval.md](08_diseno_combate_naval.md)) selector de armas con mods aplicables, preview de daño/coste/tamaño.
- [ ] Tooltip con descripción de cada mod.
- [ ] Indicador de armas en pantalla de combate táctico.
