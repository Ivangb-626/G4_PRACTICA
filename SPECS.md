# SPECS.md — MasterDeHostias: Especificación Técnica Completa (SDD)

> **Este fichero es la fuente de verdad** para toda la implementación del proyecto.
> Cada endpoint, modelo de datos, componente frontend, regla de juego y criterio de aceptación
> está definido aquí. Consultad este fichero ANTES de implementar cualquier funcionalidad.

---

## ÍNDICE

1. [Modelos de Datos](#1-modelos-de-datos)
2. [API REST — Endpoints](#2-api-rest--endpoints)
3. [Reglas del Juego](#3-reglas-del-juego)
4. [Componentes Frontend](#4-componentes-frontend)
5. [Integración LLM (GroQ / GitHub Models)](#5-integración-llm-groq--github-models)
6. [Módulos Específicos por Grupo](#6-módulos-específicos-por-grupo)
7. [Docker & Deployment](#7-docker--deployment)
8. [Criterios de Aceptación Globales](#8-criterios-de-aceptación-globales)

---

## 1. MODELOS DE DATOS

### 1.1. User

```json
{
  "_id": "ObjectId",
  "username": "string (3-30 chars, unique)",
  "email": "string (valid email, unique)",
  "password_hash": "string (bcrypt)",
  "created_at": "ISO 8601 datetime",
  "last_login": "ISO 8601 datetime",
  "games_played": "number",
  "games_won": "number"
}
```

**Validaciones:**
- `username`: 3-30 caracteres, alfanumérico + guiones
- `email`: formato válido, único en la colección
- `password`: mínimo 8 caracteres, almacenado como hash bcrypt

---

### 1.2. Race

```json
{
  "id": "string (slug)",
  "name": "string",
  "description": "string",
  "image_url": "string",
  "government": "string (dictatorship|democracy|unification|feudalism)",
  "home_planet": {
    "name": "string",
    "type": "string",
    "size": "string",
    "minerals": "string",
    "gravity": "string"
  },
  "traits": {
    "research_bonus": "number (percentage, default 0)",
    "ground_combat_bonus": "number (absolute, default 0)",
    "diplomacy_bonus": "number (percentage, default 0)",
    "trade_bonus": "number (BC per capita, default 0)",
    "food_bonus": "number (per farmer, default 0)",
    "industry_bonus": "number (per worker, default 0)",
    "population_growth_bonus": "number (percentage, default 0)",
    "ship_attack_bonus": "number (percentage, default 0)",
    "ship_defense_bonus": "number (percentage, default 0)",
    "spy_bonus": "number (percentage, default 0)",
    "bc_per_capita": "number (BC per population unit, default 0)"
  },
  "special_abilities": ["string"]
}
```

**Razas (18 razas, 3 por grupo):**

Cada grupo implementa exactamente las 3 razas asignadas en `MasterDeHostias_practica.md § 2`.

| id | name | government | traits principales | Grupo |
|----|------|------------|-------------------|-------|
| `humans` | Humanos | democracy | diplomacy_bonus: 25, trade_bonus: 1 | 1 |
| `bulrathi` | Bulrathi | dictatorship | ground_combat_bonus: 10, research_bonus: -10 | 1 |
| `mrrshan` | Mrrshan | dictatorship | ship_attack_bonus: 50, ground_combat_bonus: 5, diplomacy_bonus: -20 | 1 |
| `psilons` | Psilons | dictatorship | research_bonus: 50, ground_combat_bonus: -5 | 2 |
| `darlok` | Darlok | dictatorship | spy_bonus: 20, diplomacy_bonus: -10 | 2 |
| `elerian` | Elerian | dictatorship | ship_defense_bonus: 30, spy_bonus: 10 | 2 |
| `sakkra` | Sakkra | dictatorship | population_growth_bonus: 100, food_bonus: -1 | 3 |
| `silicoid` | Silicoid | dictatorship | industry_bonus: 1, diplomacy_bonus: -20, special_abilities: [lithovore] | 3 |
| `gnolam` | Gnolam | feudalism | trade_bonus: 2, bc_per_capita: 1, ground_combat_bonus: -5 | 3 |
| `alkari` | Alkari | democracy | ship_defense_bonus: 40, ground_combat_bonus: -5 | 4 |
| `meklar` | Meklar | dictatorship | industry_bonus: 2, food_bonus: -1, population_growth_bonus: -50 | 4 |
| `trilarian` | Trilarian | unification | ship_attack_bonus: 25, food_bonus: 1, research_bonus: -10 | 4 |
| `klackon` | Klackon | unification | industry_bonus: 2, food_bonus: 1, diplomacy_bonus: -30 | 5 |
| `nommo` | Nommo | democracy | research_bonus: 25, food_bonus: 1, industry_bonus: -1 | 5 |
| `cynoid` | Cynoid | feudalism | ship_attack_bonus: 30, ship_defense_bonus: 20, ground_combat_bonus: -10 | 5 |
| `draconian` | Draconianos | dictatorship | ship_attack_bonus: 25, ground_combat_bonus: 8, food_bonus: -1 | 6 |
| `icthyar` | Icthyar | unification | food_bonus: 2, population_growth_bonus: 50, ship_attack_bonus: -20 | 6 |
| `voidborn` | Nacidos del Vacío | feudalism | research_bonus: 20, ship_defense_bonus: 20, ground_combat_bonus: -10 | 6 |

---

### 1.3. Planet

```json
{
  "index": "number (0-4)",
  "name": "string",
  "type": "string",
  "size": "string",
  "minerals": "string",
  "gravity": "string",
  "max_population": "number",
  "colonized_by": "string|null (player|ai_0|ai_1|...)",
  "special": "string|null (artifacts|gold_deposits|splinter_colony|hostile_natives)"
}
```

**Tipos de planeta (type):**

| type | habitable | food_modifier | description |
|------|-----------|--------------|-------------|
| `toxic` | No (requiere tech) | -3 | Atmósfera venenosa |
| `barren` | No (requiere tech) | -2 | Sin atmósfera |
| `desert` | Sí | -1 | Seco, poca agua |
| `tundra` | Sí | -1 | Frío, helado |
| `arid` | Sí | 0 | Semi-seco |
| `swamp` | Sí | 0 | Pantanoso |
| `ocean` | Sí | +1 | Mayormente agua |
| `terran` | Sí | +1 | Equilibrado, ideal |
| `gaia` | Sí | +2 | Paraíso, perfecto |

**Tamaños (size):**

| size | max_pop_base | build_slots |
|------|-------------|-------------|
| `tiny` | 8 | 3 |
| `small` | 12 | 4 |
| `medium` | 16 | 5 |
| `large` | 22 | 7 |
| `huge` | 28 | 8 |

**Minerales (minerals):**

| minerals | production_modifier |
|----------|-------------------|
| `ultra_poor` | ×0.33 |
| `poor` | ×0.66 |
| `abundant` | ×1.0 |
| `rich` | ×1.5 |
| `ultra_rich` | ×2.0 |

**Gravedad (gravity):**

| gravity | penalty_unless_adapted |
|---------|----------------------|
| `low` | -25% population efficiency |
| `normal` | none |
| `high` | -25% population efficiency |

---

### 1.4. StarSystem

```json
{
  "id": "string (sys_xxx)",
  "name": "string",
  "position": {"x": "number", "y": "number"},
  "star_type": "string (red|orange|yellow|white|blue)",
  "planets": ["Planet"],
  "connections": ["string (system_ids)"],
  "explored_by": ["string (player|ai_0|...)"],
  "guardian": {
    "active": "boolean",
    "fleet": "Fleet|null"
  }
}
```

**Tipos de estrella (star_type):**

| star_type | max_planets | planet_bias |
|-----------|------------|-------------|
| `red` | 3 | toxic, barren, tundra |
| `orange` | 4 | desert, tundra, arid |
| `yellow` | 5 | balanced (all types) |
| `white` | 4 | barren, desert, terran |
| `blue` | 3 | toxic, barren, rich minerals |

---

### 1.5. Colony

```json
{
  "id": "string",
  "name": "string",
  "star_system_id": "string",
  "planet_index": "number",
  "owner": "string (player|ai_0|...)",
  "population": {
    "total": "number",
    "max": "number",
    "farmers": "number",
    "workers": "number",
    "scientists": "number"
  },
  "buildings": [
    {
      "id": "string",
      "name": "string",
      "completed": "boolean"
    }
  ],
  "build_queue (max 7)": [
    {
      "type": "string (building|ship)",
      "id": "string",
      "progress": "number",
      "cost": "number"
    }
  ],
  "morale": "string (jubilant|happy|stable|unrest|revolt)",
  "food_output": "number",
  "food_consumption": "number",
  "industry_output": "number",
  "research_output": "number",
  "bc_output": "number"
}
```

---

### 1.6. Building

```json
{
  "id": "string",
  "name": "string",
  "description": "string",
  "cost": "number (production points)",
  "maintenance": "number (BC per turn)",
  "effects": {
    "production_bonus": "number",
    "research_bonus": "number",
    "food_bonus": "number",
    "bc_bonus": "number",
    "command_points": "number",
    "ground_defense": "number",
    "orbital_defense": "number",
    "ship_production_bonus": "number (percentage)",
    "morale_bonus": "number"
  },
  "prerequisites": {
    "tech": ["string (tech_ids)"],
    "buildings": ["string (building_ids)"]
  }
}
```

**Edificios Core:**

| id | name | cost | maintenance | main_effect | tech_req |
|----|------|------|------------|-------------|----------|
| `marine_barracks` | Cuartel de Marines | 30 | 1 | ground_defense: +10 | — |
| `automated_factory` | Fábrica Automatizada | 60 | 2 | production_bonus: +5 | construction_1 |
| `research_lab` | Laboratorio de Investigación | 60 | 2 | research_bonus: +5 | computers_1 |
| `hydroponic_farm` | Granja Hidropónica | 40 | 1 | food_bonus: +2 | biology_1 |
| `star_base` | Base Estelar | 200 | 4 | command_points: +2, big_ships: true | construction_2 |
| `missile_base` | Base de Misiles | 80 | 2 | orbital_defense: +20 | chemistry_1 |
| `spaceport` | Puerto Espacial | 100 | 3 | ship_production_bonus: +50% | construction_1 |
| `trade_center` | Centro de Comercio | 60 | 1 | bc_bonus: +3 | sociology_1 |

---

### 1.7. Technology

```json
{
  "id": "string",
  "field": "string (construction|power|chemistry|sociology|computers|biology|physics|force_fields)",
  "level": "number (1-11, varies by field)",
  "level_name": "string (MOO2 level name)",
  "name": "string",
  "description": "string",
  "research_cost": "number (50–15000 RP)",
  "alternative_group": "number (technologies in same field+level are mutually exclusive)",
  "unlocks": {
    "buildings": ["string"],
    "ship_components": ["string"],
    "abilities": ["string"],
    "empire_bonus": "string (optional: gov_upgrade, etc.)"
  }
}
```

**Árbol Tecnológico Completo MOO2 (8 campos × 7-11 niveles ≈ 200 techs):**

##### Construction / Engineering (11 niveles)

| Lvl | Nivel MOO2 | RP | Techs (choose 1, Creative gets all) |
|-----|-----------|-----|--------------------------------------|
| 1 | Engineering | 80 | Colony Base, Star Base |
| 2 | Advanced Engineering | 150 | Automated Factory, Missile Base |
| 3 | Advanced Construction | 250 | Pollution Processor, Reinforced Hull |
| 4 | Capsule Construction | 400 | Battle Pods, Troop Pods, Survival Pods |
| 5 | Astro Engineering | 650 | Spaceport, Fighter Bays |
| 6 | Robotics | 900 | Robotic Factory, Ground Batteries |
| 7 | Servo Mechanics | 1150 | Fast Missile Racks, Armor Barracks |
| 8 | Astro Construction | 1500 | Titan Construction, Hercular Construction |
| 9 | Advanced Manufacturing | 2000 | Recyclotron, Automated Repair Unit |
| 10 | Super Construction | 3500 | Star Fortress, Advanced Damage Control |
| 11 | Hyper-Advanced Engineering | 7500+ | Future Tech (repeatable, miniaturization) |

##### Power (8 niveles)

| Lvl | Nivel MOO2 | RP | Techs |
|-----|-----------|-----|-------|
| 1 | Nuclear Fission | 50 | Nuclear Drive, Nuclear Bomb |
| 2 | Cold Fusion | 80 | Colony Ship, Freighters, Outpost Ship |
| 3 | Advanced Fusion | 250 | Fusion Drive, Fusion Bomb, Augmented Engines |
| 4 | Ion Fission | 900 | Ion Drive, Ion Pulse Cannon |
| 5 | Anti-Matter Fission | 2000 | Anti-Matter Drive, Anti-Matter Bomb, Anti-Matter Torpedoes |
| 6 | Matter-Energy Conversion | 2750 | High Energy Focus, Energy Absorber |
| 7 | Hyper-Dimensional Fission | 3500 | Hyper Drive, Proton Torpedoes |
| 8 | Interphased Fission | 4500 | Interphased Drive, Plasma Torpedoes |
| 9 | Hyper-Advanced Power | 10000+ | Future Tech (repeatable) |

##### Chemistry (7 niveles)

| Lvl | Nivel MOO2 | RP | Techs |
|-----|-----------|-----|-------|
| 1 | Chemistry | 50 | Nuclear Missile, Standard Fuel Cells |
| 2 | Advanced Metallurgy | 250 | Tritanium Armor, Merculite Missile |
| 3 | Advanced Chemistry | 650 | Pollution Processor, Atmospheric Renewer |
| 4 | Molecular Compression | 1150 | Deuterium Fuel Cells, Zortrium Armor |
| 5 | Nano Technology | 2000 | Nano Disassemblers, Microlite Construction |
| 6 | Molecular Manipulation | 4500 | Pulson Missile, Adamantium Armor |
| 7 | Hyper-Advanced Chemistry | 10000+ | Future Tech (repeatable) |

##### Sociology (7 niveles)

| Lvl | Nivel MOO2 | RP | Techs |
|-----|-----------|-----|-------|
| 1 | Military Tactics | 150 | Space Academy |
| 2 | Xeno Relations | 650 | Xeno Psychology, Alien Management Center |
| 3 | Macro Economics | 1150 | Planetary Stock Exchange |
| 4 | Teaching Methods | 2000 | Astro University |
| 5 | Advanced Government | 4500 | Confederation, Imperium, Federation, Galactic Unification (según gobierno actual) |
| 6 | Galactic Economics | 6000 | Galactic Currency Exchange |
| 7 | Hyper-Advanced Sociology | 9000+ | Future Tech (repeatable) |

> **Nota:** Sociology es especial — la mayoría de niveles tienen 1 sola tech (no electiva). El nivel 5 (Advanced Government) desbloquea la mejora de gobierno actual.

##### Computers (8 niveles)

| Lvl | Nivel MOO2 | RP | Techs |
|-----|-----------|-----|-------|
| 1 | Electronics | 50 | Electronic Computer, Scanner |
| 2 | Optronics | 150 | Optronic Computer, Dauntless Guidance System, Scout Lab |
| 3 | Artificial Intelligence | 400 | Positronic Computer, Neural Scanner, Holo Simulator |
| 4 | Positronics | 900 | Emissions Guidance System, Rangemaster Unit, Cyber Security Link |
| 5 | Cybertronics | 1500 | Cybertronic Computer, Battle Scanner, Virtual Reality Network |
| 6 | Cybertechnics | 2750 | Android Workers, Android Farmers, Android Scientists |
| 7 | Galactic Networking | 3500 | Galactic Cybernet |
| 8 | Moleculartronics | 4500 | Moleculartronic Computer, Achilles Targeting Unit |
| 9 | Hyper-Advanced Computers | 6000+ | Future Tech (repeatable) |

##### Biology (8 niveles)

| Lvl | Nivel MOO2 | RP | Techs |
|-----|-----------|-----|-------|
| 1 | Astro Biology | 80 | Hydroponic Farm, Biospheres |
| 2 | Advanced Biology | 400 | Soil Enrichment, Cloning Center |
| 3 | Genetic Engineering | 900 | Death Spores, Bio Terminator |
| 4 | Genetic Mutations | 1150 | Telepathic Training, Microbiotics |
| 5 | Macro Genetics | 1500 | Terraforming, Subterranean Farms |
| 6 | Evolutionary Genetics | 2750 | Evolutionary Mutation, Gaia Transformation |
| 7 | Artificial Life | 4500 | Bio Armor, Universal Antidote |
| 8 | Hyper-Advanced Biology | 7500+ | Future Tech (repeatable) |

##### Physics (10 niveles)

| Lvl | Nivel MOO2 | RP | Techs |
|-----|-----------|-----|-------|
| 1 | Physics | 50 | Laser Cannon, Laser Rifle, Space Scanner |
| 2 | Fusion Physics | 150 | Fusion Beam, Fusion Rifle |
| 3 | Tachyon Physics | 250 | Tachyon Communications, Tachyon Scanner |
| 4 | Neutrino Physics | 900 | Neutron Blaster, Neutron Scanner |
| 5 | Artificial Gravity | 1150 | Tractor Beam, Graviton Beam, Planetary Gravity Generator |
| 6 | Subspace Physics | 1500 | Subspace Communications |
| 7 | Multi-Phased Physics | 2000 | Phasor, Phasor Rifle, Multi-Phased Shields |
| 8 | Plasma Physics | 3500 | Plasma Cannon, Plasma Rifle, Plasma Web |
| 9 | Multi-Dimensional Physics | 4500 | Disruptor Cannon, Dimensional Portal |
| 10 | Temporal Physics | 6000 | Stellar Converter, Star Gate, Time Warp Facilitator |
| 11 | Hyper-Advanced Physics | 15000+ | Future Tech (repeatable) |

##### Force Fields (9 niveles)

| Lvl | Nivel MOO2 | RP | Techs |
|-----|-----------|-----|-------|
| 1 | Advanced Magnetism | 250 | Class I Shield, Mass Driver |
| 2 | Gravimetrics | 650 | Anti-Missile Rockets, Gyro Destabilizer |
| 3 | Magneto Gravitics | 900 | Class III Shield, Planetary Radiation Shield, Warp Field Interdictor |
| 4 | Electromagnetic Refraction | 1500 | Stealth Field, Personal Shield, Stealth Suit |
| 5 | Warp Fields | 2000 | Class V Shield, Multi-Wave ECM Jammer, Gauss Cannon |
| 6 | Subspace Fields | 2750 | Class VII Shield, Planetary Flux Shield, Wide Area Jammer |
| 7 | Distortion Fields | 3500 | Cloaking Device, Stasis Field |
| 8 | Quantum Fields | 4500 | Class X Shield, Planetary Barrier, Phasing Cloak |
| 9 | Transwarp Fields | 7500 | Displacement Device, Subspace Teleporter |
| 10 | Hyper-Advanced Force Fields | 15000+ | Future Tech (repeatable) |

---

### 1.8. Ship

```json
{
  "type": "string",
  "design_id": "string",
  "name": "string",
  "hull": {
    "hp": "number",
    "armor": "number",
    "space": "number (total component slots)"
  },
  "weapons": [
    {
      "id": "string",
      "damage_min": "number",
      "damage_max": "number",
      "range": "number",
      "type": "string (beam|missile|torpedo)"
    }
  ],
  "shields": "number",
  "speed": "number",
  "command_points": "number",
  "cost": "number (production points)"
}
```

**Tipos de Nave Core:**

| type | hp | armor | speed | command_points | cost | requires |
|------|-----|-------|-------|---------------|------|----------|
| `frigate` | 10 | 2 | 4 | 1 | 25 | — |
| `destroyer` | 25 | 5 | 3 | 2 | 60 | — |
| `cruiser` | 60 | 10 | 2 | 4 | 120 | — |
| `battleship` | 120 | 20 | 1 | 8 | 250 | star_base |
| `colony_ship` | 5 | 0 | 2 | 0 | 50 | — |
| `transport` | 5 | 0 | 2 | 0 | 25 | marine_barracks |

---

### 1.9. Fleet

```json
{
  "id": "string",
  "name": "string",
  "owner": "string (player|ai_0|...)",
  "star_system_id": "string",
  "ships": [
    {"type": "string", "count": "number", "design_id": "string"}
  ],
  "destination": "string|null",
  "eta_turns": "number|null",
  "command_points_used": "number"
}
```

---

### 1.10. GameState

```json
{
  "game_id": "string",
  "name": "string",
  "scenario_id": "string",
  "turn": "number",
  "current_player": "string (player|ai_0|...)",
  "created_at": "ISO 8601",
  "last_saved": "ISO 8601",
  "is_autosave": "boolean",
  "cheats_used": ["string"],
  "antaran_next_attack_turn": "number|null (initially 15 + random(0,5); null if disabled)",
  "victory_condition": "string|null",
  "player": "PlayerState",
  "ai_players": ["AIPlayerState"],
  "galaxy": "GalaxyState"
}
```

---

### 1.11. PlayerState / AIPlayerState

```json
{
  "race": "Race",
  "resources": {
    "bc": "number",
    "total_food_surplus": "number",
    "total_production": "number",
    "total_research": "number",
    "command_points": "number",
    "command_points_used": "number"
  },
  "colonies": ["Colony"],
  "fleets": ["Fleet"],
  "technologies": {
    "researched": [
      {"field": "string", "level": "number", "tech_id": "string"}
    ],
    "current_research": {
      "field": "string",
      "level": "number",
      "tech_id": "string",
      "progress": "number",
      "total_cost": "number"
    }
  }
}
```

Para `AIPlayerState`, agregar:
```json
{
  "...all PlayerState fields...",
  "personality": "string (aggressive|defensive|expansionist|researcher|balanced)",
  "diplomacy_stance": "string (hostile|cautious|neutral|friendly|allied)"
}
```

---

### 1.12. GalaxyState

```json
{
  "size": "string (small|medium|large)",
  "num_systems": "number",
  "star_systems": ["StarSystem"],
  "fog_of_war": {
    "player": ["string (visible system_ids)"],
    "ai_0": ["string (visible system_ids)"]
  }
}
```

### 1.13. Leader

```json
{
  "id": "string",
  "name": "string",
  "title": "string",
  "type": "string (colony | fleet)",
  "bonuses": {
    "production_bonus_pct": "number (optional, % boost to colony production)",
    "research_bonus_pct": "number (optional, % boost to colony research)",
    "food_bonus_pct": "number (optional, % boost to colony food)",
    "income_bonus_pct": "number (optional, % boost to colony BC income)",
    "morale_bonus": "number (optional, flat morale boost)",
    "pop_growth_bonus_pct": "number (optional, % boost to pop growth)",
    "attack_bonus_pct": "number (optional, % boost to fleet attack power)",
    "defense_bonus_pct": "number (optional, % boost to fleet defense)",
    "speed_bonus": "number (optional, flat speed bonus for fleet)",
    "initiative_bonus": "number (optional, combat initiative bonus)"
  },
  "description": "string",
  "hire_cost": "number (BC)",
  "upkeep": "number (BC/turno)",
  "assigned_to": "string|null (colony_id or fleet_id)"
}
```

El juego incluye 19 líderes estilo MOO2, divididos en:
- **Líderes de colonia**: mejoran producción, investigación, comida, ingresos, moral o crecimiento de la colonia asignada.
- **Líderes de flota**: mejoran potencia de ataque, defensa, velocidad o iniciativa de la flota asignada.

**Mecánica:**
- Solo aparecen en el mercado de líderes disponibles (GET `/leaders/available`).
- Se contratan pagando `hire_cost` BC; el coste se descuenta inmediatamente.
- Consumen `upkeep` BC/turno (descontado en `turn_engine`).
- Se asignan a una colonia o flota específica vía PUT `/leaders/{id}/assign`.
- Los bonuses de colonia se aplican durante el cálculo de producción/investigación/comida/BC en `turn_engine`.
- Los bonuses de flota se aplican al combate automático (multiplican la potencia de combate de la flota).
- Solo un líder puede estar asignado a cada colonia/flota al mismo tiempo.

---

## 2. API REST — ENDPOINTS

### 2.1. Autenticación

#### POST /api/auth/register
Registra un nuevo usuario.

**Request Body:**
```json
{
  "username": "string",
  "email": "string",
  "password": "string"
}
```

**Response 201:**
```json
{
  "user_id": "string",
  "username": "string",
  "token": "string (JWT)"
}
```

**Response 400:**
```json
{"error": "Username already exists | Email already registered | Invalid email format | Password too short"}
```

**Criterios de aceptación:**
- [ ] Registra usuario con credenciales válidas
- [ ] Rechaza username duplicado (400)
- [ ] Rechaza email duplicado (400)
- [ ] Rechaza password < 8 caracteres (400)
- [ ] Password se almacena como hash bcrypt
- [ ] Devuelve JWT válido

---

#### POST /api/auth/login
Inicia sesión.

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response 200:**
```json
{
  "user_id": "string",
  "username": "string",
  "token": "string (JWT)"
}
```

**Response 401:**
```json
{"error": "Invalid credentials"}
```

**Criterios de aceptación:**
- [ ] Login correcto con credenciales válidas
- [ ] Rechaza credenciales incorrectas (401)
- [ ] Devuelve JWT con expiración configurada
- [ ] Actualiza `last_login` del usuario

---

#### GET /api/auth/profile
Devuelve el perfil del usuario autenticado.

**Headers:** `Authorization: Bearer <JWT>`

**Response 200:**
```json
{
  "user_id": "string",
  "username": "string",
  "email": "string",
  "created_at": "string",
  "games_played": "number",
  "games_won": "number"
}
```

**Response 401:**
```json
{"error": "Unauthorized"}
```

---

### 2.2. Gestión de Partidas

#### GET /api/games
Lista partidas guardadas del usuario autenticado.

**Headers:** `Authorization: Bearer <JWT>`

**Response 200:**
```json
{
  "games": [
    {
      "game_id": "string",
      "name": "string",
      "scenario_id": "string",
      "turn": "number",
      "last_saved": "string",
      "is_autosave": "boolean",
      "player_race": "string",
      "galaxy_size": "string"
    }
  ]
}
```

**Criterios de aceptación:**
- [ ] Lista solo partidas del usuario autenticado
- [ ] Incluye partidas de autoguardado
- [ ] Ordenadas por `last_saved` descendente

---

#### POST /api/games
Crea una nueva partida.

**Headers:** `Authorization: Bearer <JWT>`

**Request Body:**
```json
{
  "name": "string",
  "scenario_config": {
    "galaxy_size": "string (small|medium|large)",
    "num_opponents": "number (1-3)",
    "difficulty": "string (easy|normal|hard)",
    "player_race": "string (race_id)"
  }
}
```

**Response 201:**
```json
{
  "game_id": "string",
  "game_state": "GameState (complete initial state)"
}
```

**Criterios de aceptación:**
- [ ] Crea partida con galaxia generada aleatoriamente
- [ ] Asigna razas a IAs automáticamente (distintas entre sí y del jugador)
- [ ] Cada jugador comienza con 1 colonia (planeta natal) y 2 fragatas
- [ ] Fog of War activo, solo sistema natal visible
- [ ] Devuelve estado completo para renderizar

---

#### GET /api/game/{gameId}
Carga una partida guardada.

**Headers:** `Authorization: Bearer <JWT>`

**Response 200:**
```json
{
  "game_id": "string",
  "game_state": "GameState"
}
```

**Response 403:**
```json
{"error": "This game does not belong to you"}
```

**Response 404:**
```json
{"error": "Game not found"}
```

**Criterios de aceptación:**
- [ ] Carga correctamente el estado completo
- [ ] Solo permite cargar partidas propias (403 para ajenas)
- [ ] Devuelve 404 si no existe

---

#### POST /api/game/{gameId}/save
Guarda manualmente la partida actual.

**Headers:** `Authorization: Bearer <JWT>`

**Request Body:**
```json
{
  "name": "string (optional, defaults to existing name)"
}
```

**Response 200:**
```json
{
  "success": true,
  "last_saved": "string (ISO 8601)"
}
```

---

#### DELETE /api/game/{gameId}
Elimina una partida guardada.

**Headers:** `Authorization: Bearer <JWT>`

**Response 200:**
```json
{"success": true}
```

---

### 2.3. Acciones en Partida

Todos los endpoints de esta sección requieren `Authorization: Bearer <JWT>` y validan que la partida pertenece al usuario.

#### POST /api/game/{gameId}/colony/{colonyId}/manage
Gestiona una colonia (asignar población, modificar cola de construcción).

**Request Body:**
```json
{
  "population": {
    "farmers": "number",
    "workers": "number",
    "scientists": "number"
  },
  "build_queue": [
    {"type": "string (building|ship)", "id": "string"}
  ]
}
```

**Response 200:**
```json
{
  "colony": "Colony (updated)",
  "validation_warnings": ["string (e.g., 'Food deficit: population will decrease')"]
}
```

**Response 400:**
```json
{"error": "Population assignment does not match total | Building not available | Tech requirement not met"}
```

**Criterios de aceptación:**
- [ ] Suma de farmers+workers+scientists = total population
- [ ] Solo permite edificios cuyas dependencias tecnológicas se cumplen
- [ ] Solo permite edificios cuyas dependencias de otros edificios se cumplen
- [ ] Advierte si hay déficit de comida
- [ ] Actualiza cálculos de producción inmediatamente
- [ ] No permite duplicar edificios ya construidos en la cola

---

#### POST /api/game/{gameId}/research
Selecciona qué tecnología investigar.

**Request Body:**
```json
{
  "field": "string",
  "level": "number",
  "tech_id": "string"
}
```

**Response 200:**
```json
{
  "current_research": {
    "field": "string",
    "level": "number",
    "tech_id": "string",
    "progress": "number",
    "total_cost": "number"
  }
}
```

**Response 400:**
```json
{"error": "Technology not available | Previous level not completed | Already researched"}
```

**Criterios de aceptación:**
- [ ] Solo permite investigar nivel N+1 si nivel N está completado en ese campo
- [ ] Solo permite techs que no han sido descartadas (elección excluyente)
- [ ] La investigación en curso se pierde si se cambia de tecnología

---

#### POST /api/game/{gameId}/fleet/{fleetId}/move
Mueve una flota a otro sistema.

**Request Body:**
```json
{
  "destination": "string (system_id)"
}
```

**Response 200:**
```json
{
  "fleet": "Fleet (updated with destination and ETA)",
  "path": ["string (system_ids)"]
}
```

**Response 400:**
```json
{"error": "Destination not reachable | No fuel range | Fleet already in transit"}
```

**Criterios de aceptación:**
- [ ] Solo permite destinos conectados o dentro del rango
- [ ] Calcula ETA correctamente basado en velocidad de la nave más lenta
- [ ] No permite mover flotas que ya están en tránsito
- [ ] Actualiza fog of war si la flota llega a un sistema no explorado

---

#### POST /api/game/{gameId}/fleet/{fleetId}/split
Divide una flota en dos, moviendo las naves indicadas a una nueva flota.

**Request Body:**
```json
{
  "ships": [{"design_id": "string", "count": "number"}]
}
```

**Response 200:**
```json
{
  "original": "Fleet (updated, remaining ships)",
  "new_fleet": "Fleet (newly created with split ships)"
}
```

**Response 400:**
```json
{"error": "Cannot split — not enough ships | Fleet in transit"}
```

**Criterios de aceptación:**
- [ ] Solo permite split si la flota tiene suficientes naves del tipo indicado
- [ ] No permite split de flotas en tránsito
- [ ] La nueva flota hereda la posición (star_index) de la original
- [ ] Ambas flotas mantienen ships consistentes tras el split

---

#### POST /api/game/{gameId}/colonize
Envía nave colonizadora a colonizar un planeta.

**Request Body:**
```json
{
  "fleet_id": "string",
  "planet_index": "number"
}
```

**Response 200:**
```json
{
  "new_colony": "Colony",
  "fleet": "Fleet (updated, colony ship consumed)"
}
```

**Response 400:**
```json
{"error": "No colony ship in fleet | Planet already colonized | Planet not colonizable"}
```

**Criterios de aceptación:**
- [ ] La flota debe contener al menos una nave colonizadora
- [ ] La nave colonizadora se consume al colonizar
- [ ] La nueva colonia empieza con 1 de población
- [ ] Colonias en planetas tóxicos/estériles requieren tech correspondiente
- [ ] El sistema debe estar explorado

---

#### POST /api/game/{gameId}/endTurn
Finaliza el turno del jugador y ejecuta el turno de la IA.

**Request Body:**
```json
{}
```

**Response 200:**
```json
{
  "turn": "number (new turn number)",
  "game_state": "GameState (after AI turn)",
  "ai_actions": [
    {
      "action_id": "number",
      "type": "string",
      "entity": {"id": "string", "name": "string", "type": "string"},
      "details": {},
      "visible_to_player": "boolean"
    }
  ],
  "events": [
    {
      "type": "string (combat|colonization|research_complete|food_shortage|population_growth|building_complete|ship_complete|antaran_attack|council_vote|victory|defeat)",
      "details": {}
    }
  ],
  "combat_results": [
    {
      "location": "string",
      "attacker": "string",
      "defender": "string",
      "winner": "string",
      "casualties": {}
    }
  ]
}
```

**Criterios de aceptación:**
- [x] Procesa fin de turno del jugador: recursos, crecimiento, investigación, producción, combates
- [x] Ejecuta turno de la IA (llamada a LLM)
- [x] Devuelve lista de acciones de IA para visualización (solo las visibles al jugador)
- [x] Incluye eventos generados (combates, investigaciones completadas, etc.)
- [x] Autoguarda la partida
- [x] Detecta condiciones de victoria/derrota
- [x] Incrementa contador de turno

---

#### POST /api/game/{gameId}/cheat
Aplica un código de cheat.

**Request Body:**
```json
{
  "cheat_code": "string",
  "target": {
    "type": "string|null (star_system|colony)",
    "id": "string|null"
  }
}
```

**Response 200:**
```json
{
  "success": true,
  "message": "string (description of what happened)",
  "game_state": "GameState (updated)"
}
```

**Response 400:**
```json
{"error": "Invalid cheat code | Target required for this cheat"}
```

**Códigos de cheat válidos:**

Los códigos son **MOO2 clásicos** (en mayúsculas), enviados en el campo `code`:

| code | target | effect |
|------|--------|--------|
| `MOOLA` | — | +1000 BC. Devuelve `new_bc` en la respuesta |
| `MENLO` | — | Completa la investigación actual al instante |
| `EINSTEIN` | — | Desbloquea todas las tecnologías del árbol |
| `OMEGA` | — | Alias de EINSTEIN |
| `CRUNCH` | — | Completa TODA la cola de construcción de TODAS las colonias del jugador |
| `RUSHBUY` | `colony_id` | Completa TODA la cola de una colonia específica |
| `ISEEALL` | — | Revela el mapa completo de la galaxia (desactiva fog of war) |
| `GALAXY` | — | Muestra todas las estrellas (alias de ISEEALL) |
| `EVENTS` | — | Alterna eventos aleatorios activos/desactivados |
| `ANTARANS` | — | Alterna ataques Antaranos (`antaran_disabled` flag) |
| `COUNCIL` | — | Fuerza votación del consejo galáctico en el siguiente turno |
| `SCORE` | — | Muestra estadísticas de puntuación sin modificar el estado |

**Criterios de aceptación:**
- [ ] Cada cheat produce el efecto descrito
- [ ] Cheats que requieren target devuelven error si no se proporciona
- [ ] Los cheats se registran en `cheats_used` del estado de juego
- [ ] Los cheats se loguean en el servidor para debug

---

### 2.4. Consultas de Estado

#### GET /api/game/{gameId}/galaxy
Devuelve el estado actual de la galaxia (respetando fog of war).

**Response 200:**
```json
{
  "star_systems": [
    {
      "id": "string",
      "name": "string",
      "position": {"x": "number", "y": "number"},
      "star_type": "string",
      "explored": "boolean",
      "planets": ["Planet (only if explored)"],
      "connections": ["string"],
      "has_player_colony": "boolean",
      "has_player_fleet": "boolean",
      "has_enemy_fleet": "boolean (only if system is visible)"
    }
  ]
}
```

---

#### GET /api/game/{gameId}/tech-tree
Devuelve el árbol tecnológico con estado de investigación actual.

**Response 200:**
```json
{
  "fields": [
    {
      "field": "string",
      "levels": [
        {
          "level": "number",
          "options": [
            {
              "tech_id": "string",
              "name": "string",
              "description": "string",
              "research_cost": "number",
              "status": "string (available|researched|locked|discarded)",
              "unlocks": {}
            }
          ]
        }
      ]
    }
  ],
  "current_research": {}
}
```

---

#### GET /api/game/{gameId}/colony/{colonyId}
Devuelve detalle completo de una colonia.

**Response 200:**
```json
{
  "colony": "Colony (full detail)",
  "available_buildings": [
    {"id": "string", "name": "string", "cost": "number", "requirements_met": "boolean"}
  ],
  "available_ships": [
    {"type": "string", "name": "string", "cost": "number", "requirements_met": "boolean"}
  ]
}
```

---

#### GET /api/scenarios
Lista escenarios disponibles.

**Response 200:**
```json
{
  "scenarios": [
    {
      "id": "string",
      "name": "string",
      "description": "string",
      "galaxy_sizes": ["small"],
      "max_opponents": 3,
      "difficulty_options": ["easy", "normal", "hard"]
    }
  ]
}
```

---

## 3. REGLAS DEL JUEGO

### 3.1. Economía de Colonia (MOO2 Wiki-accurate)

La producción en cada colonia sigue la fórmula general:
```
P = P_const + ROUND(P_base + P_bonus)
```
Donde:
- `P_const` = bonuses fijos de edificios (ej. Hydroponic Farm +2 FP, Auto Factory +5 PP)
- `P_base` = colonists × (planet_coeff + race_coeff + tech_coeff + buildings_coeff)
- `P_bonus` = P_total ajustado por gobierno, moral, gravedad, líder, etc.

#### Producción de Comida (FP)
```
FP_const = sum(building.flat_food_bonus)   // Hydroponic Farm +2, etc.
FP_base = farmers × (planet.food_modifier + race.food_bonus + tech_food_bonus)
FP_gov = FP_base × gov.food_multiplier    // Unification +50%, Galactic Unification +100%
FP_total = FP_const + ROUND(FP_base + FP_gov)

food_consumed = total_population × 1      // Lithovores consume 0
food_surplus = FP_total - food_consumed
```
- Si `food_surplus < 0`: la colonia pierde 1 de población por turno
- Si `food_surplus > 0`: la colonia gana población según § 3.2

#### Producción Industrial (PP)
```
PP_const = sum(building.flat_prod_bonus)   // Auto Factory +5, Robo Miners +10, etc.
PP_base = workers × (2 + race.industry_bonus + tech_prod_bonus)
PP_mineral = PP_base × planet.minerals_modifier   // Ultra Poor ×0.33, Ultra Rich ×2.0
PP_gov = PP_mineral × gov.prod_multiplier         // Unification +50%, Galactic Unif +100%
PP_morale = PP_gov × morale_modifier              // jubilant +20%, revolt -50%
PP_gravity = PP_morale × gravity_penalty           // 1.0 normal, 0.75 heavy (wrong gravity)
PP_total = PP_const + ROUND(PP_gravity)

// Pollution reduces effective PP:
pollution = ROUNDUP((PP_base + PP_gov) / pollution_divisor × tolerance - planet_size) / 2)
PP_effective = PP_total - pollution
```

#### Producción Científica (RP)
```
RP_const = sum(building.flat_research_bonus)  // Research Lab +5, Supercomputer +10, etc.
RP_base = scientists × (2 + race.research_bonus + tech_research_bonus)
RP_gov = RP_base × gov.research_multiplier    // Democracy +50%, Federation +75%, Feudal -50%, Confederation -25%
RP_morale = (RP_base + RP_gov) × morale_modifier
RP_total = RP_const + ROUND(RP_morale)
```

#### Recaudación de BC (créditos)
```
BC_const = sum(building.flat_bc_bonus)        // Marketplace, Stock Exchange, etc.
BC_population = total_population × base_tax    // base tax ~1 BC/pop
BC_gov = BC_population × gov.income_multiplier // Democracy +50%, Federation +75%
BC_trade = race.trade_bonus × total_population
BC_total = BC_const + BC_population + BC_gov + BC_trade - maintenance

maintenance = sum(building.maintenance_cost) + fleet_maintenance
```

#### Tabla de Modificadores de Planeta

| Propiedad | Modificadores |
|-----------|--------------|
| Minerales | Ultra Poor ×0.33, Poor ×0.5, Abundant ×1.0, Rich ×1.5, Ultra Rich ×2.0 |
| Comida | Toxic -1, Radiated -1, Barren 0, Desert 0, Tundra 0, Ocean +1, Swamp +1, Arid 0, Terran +1, Gaia +2 |
| Gravedad | Low Gravity ×0.75 (wrong gravity races), Normal ×1.0, Heavy Gravity ×0.75 (wrong gravity races) |
| Tamaño → Max Pop | Tiny: 1-3, Small: 3-5, Medium: 5-8, Large: 8-12, Huge: 12-17 |

#### Tabla de Costes de Compra Inmediata

| % completado | Coste multiplicador |
|-------------|---------------------|
| 0% | 4× coste restante |
| 1-25% | 3× coste restante |
| 25-50% | 2× coste restante |
| 50%+ | 2× coste restante |

### 3.2. Crecimiento de Población (MOO2 Wiki-accurate)

```
// Fórmula MOO2 real:
growth = ROUNDDOWN(SQRT(2000 × colonists × free_space / capacity))
// donde:
//   colonists = current_population (en millones)
//   free_space = max_pop - current_population
//   capacity = max_pop

// Modificadores:
race_modifier = 1 + (race.population_growth_bonus / 100)
cloning_center_bonus = +100K/turn if cloning_center built
growth_final = growth × race_modifier + cloning_center_bonus

new_population = min(current_pop + growth_final, max_pop)
```

- Crecimiento = 0 si `food_surplus < 0` o `morale == revolt`
- Máximo crecimiento cuando población está al ~50% de capacidad (curva parabólica)

### 3.3. Investigación (MOO2 Wiki-accurate)

```
total_empire_research = sum(all_colonies.research_output)
research_progress += total_empire_research

// Mecánica de breakthrough (MOO2):
if research_progress >= tech.research_cost:
    // Guaranteed completion at 1× cost
    tech is completed
elif research_progress >= tech.research_cost × 0.5:
    // After 50% of cost: breakthrough chance each turn
    // Chance increases linearly, guaranteed at 2× cost
    breakthrough_chance = (research_progress - cost) / cost
    if random() < breakthrough_chance:
        tech is completed

// On completion:
unlock tech effects
discard alternatives (same field+level, other group)
prompt for next research selection
```

**Rasgos de raza que afectan investigación:**
- **Creative**: obtiene TODAS las techs de cada nivel (no elige, no descarta)
- **Uncreative**: se le asigna 1 tech aleatoria por nivel (no puede elegir)
- **Normal**: elige 1 tech por nivel, las demás se descartan

**El árbol tiene 8 campos con 7-11 niveles cada uno (ver § 1.7). Solo se puede investigar 1 tech a la vez (empire-wide). Cada nivel requiere completar el nivel anterior del mismo campo.**

#### Investigación Hiper-Avanzada (Future Techs)

Cuando **todas** las tecnologías regulares de un campo han sido investigadas o descartadas, se desbloquea una tecnología sintética repetible:

| Propiedad | Valor |
|-----------|-------|
| id | `future_{field}` |
| cost | campo-dependiente (último nivel × 1.5) |
| repeatable | sí (se puede investigar múltiples veces) |
| unlocks | `{"bonus": "miniaturization"}` |

Esto permite al jugador seguir investigando (y terminar turno) cuando el árbol regular está completo.

#### Miniaturización

En MOO2, cada nivel tecnológico ganado más allá del nivel original de un componente reduce su tamaño y coste:
```
miniaturization_levels = current_field_level - component_original_level
size_reduction = min(miniaturization_levels × 5%, 50%)   // máximo 50%
cost_reduction = min(miniaturization_levels × 5%, 50%)
```
Las Future Techs cuentan como niveles adicionales para miniaturización.

### 3.4. Puntos de Comando

```
base_command_points = 4
star_base_bonus = num_star_bases × 2
total_command_points = base_command_points + star_base_bonus
command_points_used = sum(all_ships.command_points)
```
- No puedes construir más naves si `command_points_used >= total_command_points`
- Exceder el límite al perder una base estelar: las naves existentes se mantienen pero no puedes construir más

### 3.5. Movimiento de Flotas

```
fleet_speed = min(ship.speed for ship in fleet)  // slowest ship determines speed
eta_turns = ceil(distance / fleet_speed)
```
- Las flotas solo pueden moverse a sistemas conectados
- Al llegar a un sistema no explorado, se revela el sistema (fog of war)
- **Auto-assign to fleet**: cuando una nave se completa en build queue, se crea una flota automáticamente en el sistema de la colonia (o se añade a la flota existente del jugador)
- **Fleet Split**: `POST /fleet/{id}/split` permite dividir una flota especificando qué naves mover a una nueva flota

### 3.6. Combate Automático (Core)

El combate automático usa una **potencia de combate basada en clase de casco** (hull-weighted power), inspirada en el escalado real de MOO2:

```
// Potencia base por clase de casco (MOO2-inspired)
HULL_POWER = {
    frigate:    50,
    destroyer:  150,
    cruiser:    400,
    battleship: 1000,
    titan:      2500,
    doom_star:  6000,
    // Non-combat hulls:
    colony_ship: 5,
    transport:   5,
}

// Potencia total de una flota
fleet_power(fleet) = sum(
    HULL_POWER.get(ship.hull, 50) * ship.count
    for each ship in fleet
) × fleet_leader_multiplier

// fleet_leader_multiplier = 1.0 + (attack_bonus_pct or defense_bonus_pct) / 100
//   if a fleet leader is assigned

// Resolución: ambos bandos lanzan un dado de combate
attacker_roll = attacker_power × random(0.75, 1.25)
defender_roll = defender_power × random(0.75, 1.25)

if attacker_roll > defender_roll: attacker wins
elif defender_roll > attacker_roll: defender wins
else: defender wins (tie goes to defender)
```

**Rationale:** En MOO2 un Doom Star equivale aproximadamente a 120× una Fragata en valor de combate efectivo (HP × DPS). Los valores de HULL_POWER capturan esta escala sin necesidad de simular armas individuales.

**Para combate con criaturas espaciales**, se realiza una simulación de 5 rondas con potencias parciales (ver § 3.11). Para el ataque a Antares, se usa la potencia total de la flota directamente.

### 3.7. Invasión Terrestre

```
attack_strength = num_transports × 5 + race.ground_combat_bonus
defense_strength = colony.population + colony.ground_defense + race.ground_combat_bonus

rounds = 3
for each round:
    att_casualties = defense_strength × random(0.3, 0.5)
    def_casualties = attack_strength × random(0.3, 0.5)
    
    attack_strength -= att_casualties
    defense_strength -= def_casualties

if attack_strength > 0 and colony.population == 0: colony captured
else: invasion fails, attackers destroyed
```

### 3.8. Fog of War

Un sistema es visible para un jugador si:
- El jugador tiene una colonia en ese sistema
- El jugador tiene una flota en ese sistema
- El jugador tiene un escáner que alcanza ese sistema (tech bonus)
- El sistema es adyacente a un sistema con colonia del jugador (1 salto de visibilidad base)

### 3.9. Condiciones de Victoria

- **Conquista**: `count(enemy_colonies) == 0 AND count(enemy_fleets) == 0` para todos los oponentes
- **Consejo Galáctico**: Cada 25 turnos, se celebra votación. `player_population / total_population >= 2/3` → victoria
- **Derrota de Antares**: El jugador ataca el hogar Antarano a través del Portal Dimensional y gana (`antares_defeated = true`). Esta es la condición de victoria "canónica" de MOO2. El juego termina inmediatamente: se calcula una puntuación final, se guarda en la Hall of Fame y se muestra la pantalla de victoria (`VictoryScreen`).
- **Derrota**: `count(player_colonies) == 0 AND count(player_fleets) == 0`

### 3.9b. Comprar Producción (Rush Buy)

El jugador puede pagar BC para completar el **primer elemento de la cola** de una colonia al final del siguiente turno.

```
cost_to_buy = (item.cost - item.progress) × 2  // BC

if player.bc >= cost_to_buy:
    player.bc -= cost_to_buy
    item.progress = item.cost               // se completará en el próximo end-of-turn
else:
    error: insufficient BC
```

**Endpoint:** `POST /api/game/{gameId}/colony/{colonyId}/buy`  
**Requiere:** Al menos 1 elemento en la cola de construcción.

El botón "💰 X BC" aparece en el primer elemento de la cola en `ColonyManagement`. Se desactiva si el jugador no tiene suficientes BC.

### 3.10. Moral y Gobierno

#### Niveles de Moral

| morale | production_modifier | description |
|--------|-------------------|-------------|
| `jubilant` | +20% | Felicidad máxima |
| `happy` | +10% | Contentos |
| `stable` | 0% | Normal |
| `unrest` | -20% | Descontentos |
| `revolt` | -50%, no growth | Sublevación |

Factores que afectan moral:
- Gobierno tipo: cada gobierno tiene efectos complejos (ver tabla abajo)
- Conquista reciente de la colonia: -2 durante 5 turnos (asimilación)
- Sobrepoblación (pop > max\_pop × 0.9): -1
- Edificios de moral (ej. Virtual Reality Center): +1
- Pérdida de capitol: penalización según gobierno

> **Nota:** La Unificación es **INMUNE a la moral** (positiva y negativa). Los colonos siempre producen al 100%.

#### Tipos de Gobierno (Wiki-accurate)

Cada raza tiene un gobierno base. La tecnología `advanced_government` (Sociology, 4500 RP) mejora el gobierno **actual** a su forma avanzada (NO es una escalera lineal).

| Gobierno Base | Picks | Food | Producción | Investigación | Ingresos | Spy Def | Moral | Coste naves | Asimilación | Pérdida Capitol |
|---------------|-------|------|-----------|---------------|----------|---------|-------|------------|-------------|-----------------|
| **Feudalismo** | -4 | — | — | **-50%/scientist** | — | +10% | barracks requeridos | **-33%** | normal | -50% moral |
| **Dictadura** | 0 | — | — | — | — | +10% | barracks requeridos | — | normal | -35% moral |
| **Democracia** | 7 | — | — | **+50%/scientist** | **+50%/taxpayer** | -10% | sin penalización en colonias nuevas | — | 2× más rápida | -20% moral |
| **Unificación** | 6 | **+50%/farmer** | **+50%/worker** | — | — | +15% | **INMUNE** | — | 250% más lenta (20 turnos) | N/A (sin capitol) |

#### Gobiernos Avanzados (tras investigar `advanced_government`)

| Gobierno Avanzado | Evoluciona de | Food | Producción | Investigación | Ingresos | Spy Def | Moral | Extras |
|-------------------|--------------|------|-----------|---------------|----------|---------|-------|--------|
| **Confederación** | Feudalismo | — | — | **-25%/scientist** (mejora de -50%) | — | +10% | barracks requeridos | -33% coste naves |
| **Imperium** | Dictadura | — | — | — | — | +20% | **+20% con barracks** | **+50% command pts**, 2× asimilación |
| **Federación** | Democracia | — | — | **+75%/scientist** | **+75%/taxpayer** | -10% | sin penalización | 4× asimilación |
| **Unificación Galáctica** | Unificación | **+100%/farmer** | **+100%/worker** | — | — | +15% | **INMUNE** | asimilación 188% (15 turnos) |

#### Gobierno en el Estado del Juego

El gobierno se almacena en `player.government` (inicializado desde `race.government`). Al investigar `advanced_government`, se actualiza automáticamente:
- `feudalism` → `confederation`
- `dictatorship` → `imperium`
- `democracy` → `federation`
- `unification` → `galactic_unification`

Los modificadores de gobierno se aplican como multiplicadores en las fórmulas de economía (§ 3.1), NO como simples bonuses de moral.

### 3.11. Ataques Antaranos

Los Antaranos son una facción hostil no jugable que ataca periódicamente colonias aleatorias.

**Programación de ataques:**
```
primer_ataque = 15 + random(0, 5)
siguiente_ataque = último_ataque + 15 + random(-5, 5)   // mínimo: último_ataque + 10
```

**Selección de objetivo:**
```
target = random.choice(all_colonies)   // incluye colonias de jugador y de IA
```

**Escalada de flota Antarana:**

| Turno | Composición |
|-------|-------------|
| 15–29 | 2 fragatas (hp:15, atk:10) + 1 destructor (hp:30, atk:20) |
| 30–44 | 1 crucero (hp:80, atk:40) + 2 destructores (hp:30, atk:20) |
| 45+ | 1 acorazado (hp:160, atk:80) + 2 cruceros (hp:80, atk:40) |

**Resolución:**
- Se aplican las fórmulas de combate automático de § 3.6 (flota Antarana = atacante).
- Las defensas orbitales y flotas estacionadas del defensor participan.

**Bombardeo (si colonia sin defensa):**
```
colony.population -= 3          // mínimo 1
remove 1 random building         // si hay edificios
if colony.population <= 0: colony destroyed
```

**Recompensa por victoria defensiva:**
```
tech_reward = random.choice(unresearched_techs)  // 1 tech aleatoria no investigada
if no unresearched_techs: reward = 500 BC
```

**Cheat:** El código `ANTARANS` alterna `antaran_disabled` en el estado de partida, impidiendo o re-habilitando futuros ataques.

#### Ataque a Antares (Hogar Antarano)

Condición: el jugador tiene una flota estacionada en un sistema con una colonia que posee el edificio `dimensional_portal`.

**Guardia: ataque único.** Una vez que `game.antares_defeated == true`, el endpoint devuelve HTTP 400. No se puede atacar Antares dos veces.

**Defenders de Antares (fijos):**

| Clase | Potencia unitaria | Cantidad | Potencia total |
|-------|-----------------|----------|----------------|
| Battleship | 1000 | 3 | 3000 |
| Cruiser | 400 | 4 | 1600 |
| Destroyer | 150 | 5 | 750 |
| **Total** | | **12** | **5350** |

**Resolución:**
```
player_power = fleet_power(fleet)   // hull-weighted (§ 3.6)
player_roll  = player_power × random(0.75, 1.25)
antares_roll = 5350 × random(0.75, 1.25)

if player_roll > antares_roll:
    // VICTORIA DE FIN DE JUEGO:
    //   game.status = "victory"
    //   game.victory_type = "antares"
    //   game.antares_defeated = true
    //   3 techs aleatorias + 5000 BC
    //   score calculado e insertado en hall_of_fame
    //   response incluye status="victory" y score breakdown
else:
    // DERROTA: flota destruida
```

**Fórmula de puntuación:**
```
score = colonies × 500
      + population × 10
      + technologies × 100
      + BC × 0.1
      − turns × 2
```
Donde `colonies` = número de colonias del jugador, `population` = población total, `technologies` = techs investigadas, `BC` = créditos actuales, `turns` = turno actual.

**Recompensa por victoria:**
- 3 tecnologías aleatorias no investigadas
- 5000 BC
- Flag `antares_defeated = true` → condición de victoria (ver § 3.9)
- Puntuación guardada en colección `hall_of_fame` (MongoDB)
- Respuesta incluye `{ status: "victory", score: { colonies, population, techs, bc, turns, total }, player_power, antaran_power }`

**Endpoint:** `POST /api/game/{gameId}/combat/attack-antares`  
**Consulta Hall of Fame:** `GET /api/game/{gameId}/combat/hall-of-fame` → devuelve top-10 entradas por score desc.

**Ejemplo:** 14 Doom Stars = 14 × 6000 = 84 000 potencia vs 5350 → victoria garantizada.

#### Tecnologías Exóticas (MOO2 Wiki-accurate)

Las tecnologías exóticas son 8 techs únicas que NO se pueden investigar normalmente. Solo se obtienen conquistando Orión o defendiendo ataques Antaranos.

| # | Exotic Tech | Tipo | Efecto | Miniaturización |
|---|------------|------|--------|-----------------|
| 1 | **Death Ray** | Beam weapon | 50-100 dmg, mata 1 marine/5 dmg | No |
| 2 | **Particle Beam** | Beam weapon | 10-30 dmg, ignora escudos (shield-piercing) | No |
| 3 | **Black Hole Generator** | Special weapon | Inmoviliza + destruye objetivo en 2 turnos | No |
| 4 | **Spatial Compressor** | Bomb weapon | 4-32 × tamaño_clase dmg, radio AoE 2 casillas | No |
| 5 | **Damper Field** | Defense | Reduce TODO el daño recibido al 25% | No |
| 6 | **Xentronium Armor** | Armor | 25% más resistente que Adamantium, bloquea AP | No |
| 7 | **Quantum Detonator** | Special | Al morir la nave, explosión = 3× drive normal | No |
| 8 | **Reflection Field** | Defense | Probabilidad de reflejar beams = 10/(10+power) | No |

**Obtención:**
- **Conquistar Orión**: Death Ray + 3 exotic techs aleatorias + líder Loknar + nave Titan + acceso al planeta Gaia
- **Victoria defensiva vs Antaranos**: 1 tech aleatoria no investigada (exótica O regular). Si todas investigadas → 500 BC

Las exóticas **nunca se miniaturizan** — su tamaño es fijo.

#### Criaturas Espaciales (MOO2 Wiki-accurate)

Los sistemas estelares más valiosos están custodiados por criaturas espaciales. Deben ser derrotadas antes de colonizar.

Las criaturas tienen una **potencia de combate equivalente** expresada en la misma escala que las flotas (§ 3.6):

| Criatura | Potencia | Equivalente aprox. | Sistemas | Recompensa |
|----------|---------|---------------------|----------|------------|
| **Space Crystal** | 250 | ~5 Fragatas | Planetas buenos (Rich+) | 1 tech aleatoria |
| **Space Amoeba** | 600 | ~4 Destructores | Planetas raros (Artifacts) | 1 tech aleatoria |
| **Space Dragon** | 1500 | ~1 Acorazado | Planetas excelentes (Ultra Rich, Gaia) | 1 tech aleatoria |
| **Orion Guardian** | 8000 | ~1.3 Doom Stars | Solo Orión | Death Ray + 3 exóticas + líder + Titan |

**Referencia MOO2:** La Space Crystal aparece en la partida temprana y debe ser asequible para un crucero solo, pero no para fragatas. El Space Dragon requiere varios cruceros o un acorazado. El Guardián de Orión requiere una flota de endgame.

**Generación:** Durante la creación de la galaxia, se colocan criaturas en ~5-10% de los sistemas no-home y no-Orión. Las criaturas más fuertes custodian sistemas más valiosos.

**Combate:** Cuando una flota llega a un sistema con criatura:
1. Auto-resolve combate usando potencia hull-weighted (§ 3.6) con roll de dados
2. Si jugador gana: criatura eliminada, sistema accesible, recompensa otorgada
3. Si jugador pierde: flota destruida, criatura permanece

**Simulación de 5 rondas:** Se simula ronda a ronda reduciendo HP de ambos lados para mostrar progreso en el log de eventos, aunque el resultado final ya está determinado por el roll inicial de potencias.

**Estado en galaxia:**
```json
{
  "creature": {
    "type": "space_crystal|space_dragon|space_amoeba|orion_guardian",
    "hp": "number",
    "attack": "number",
    "shield": "number"
  }
}
```
Campo `creature` en cada star system — `null` si no hay criatura.

---

## 4. COMPONENTES FRONTEND

### 4.1. Estructura de Rutas

| Ruta | Componente | Descripción |
|------|-----------|-------------|
| `/` | LandingPage | Página de inicio con login/registro |
| `/login` | LoginPage | Formulario de login |
| `/register` | RegisterPage | Formulario de registro |
| `/dashboard` | Dashboard | Lista de partidas, crear nueva |
| `/game/:id` | GameView | Vista principal del juego |
| `/game/:id/galaxy` | GalaxyMap | Mapa galáctico |
| `/game/:id/system/:sysId` | SystemView | Vista de sistema estelar |
| `/game/:id/colony/:colId` | ColonyView | Gestión de colonia |
| `/game/:id/tech` | TechTree | Árbol tecnológico |
| `/game/:id/fleets` | FleetManager | Gestión de flotas |
| `/game/:id/combat/:combatId` | CombatResult | Resultado de combate |

### 4.2. Componentes Principales

#### GalaxyMap
- Renderizar estrellas en posiciones 2D con conexiones (líneas)
- Colores por tipo de estrella
- Iconos de colonias y flotas (propias y enemigas)
- Fog of war (sistemas no explorados oscurecidos)
- Click en estrella → navegar a SystemView
- Click en flota → panel de flota con opciones de movimiento
- Ctrl+Tab → abrir consola de cheats
- **Color de etiqueta por propietario:** el nombre de cada estrella explorada se colorea según `star.owner` o si existe una colonia del jugador (`hasPlayerColony`): verde `#44ee44` = jugador, rojo `#ee4444` = IA/enemigo, gris `#aaaacc` = neutro. La colonización actualiza inmediatamente el color en el siguiente render.
- **Spiral Galaxy Background**: Textura procedural de galaxia espiral Milky-Way (4 brazos, 900 partículas/brazo, núcleo brillante warmish, nebulosas) dibujada en offscreen canvas (2048px) y cacheada. Se mueve con zoom/pan alineada al campo de estrellas. Colores cálidos (amarillo→azul) a lo largo de los brazos.
- **Smooth Zoom**: Zoom suave con `requestAnimationFrame` + lerp (factor 0.18) hacia el punto del cursor. Zoom multiplicativo (×0.9/×1.1) en lugar de lineal. Rango 0.3×–6×.

#### SystemView
- Renderizar planetas orbitando la estrella
- Información de cada planeta (tipo, tamaño, minerales, gravedad, colonia)
- Click en planeta colonizado → navegar a ColonyView
- Botón colonizar (si hay nave colonizadora en el sistema)

#### ColonyView
- Sliders o selectores para asignar población (Farmers/Workers/Scientists)
- Barras de producción (comida, industria, investigación, BC)
- Lista de edificios construidos con iconos
- Cola de construcción con hasta 7 elementos
- Botones ▲/▼ por cada elemento de la cola para reordenar (swap con el vecino), botón ✕ para eliminar
- Selector de edificios/naves disponibles para construir

#### TechTree
- Visualización de 8 campos con niveles
- Estado visual por tech: available (verde), researched (azul), locked (gris), discarded (rojo tachado)
- Click en tech disponible → confirmar selección de investigación
- Tooltip con descripción, coste y desbloqueos

#### FleetManager
- Lista de flotas con composición
- Posición actual y destino (si en tránsito)
- Click en flota → opciones (mover, dividir, unir)
- Indicador de puntos de comando (usados/total)

#### FleetList (F)
- Tabla sortable con todas las flotas del jugador
- Columnas: Flota, Sistema, Naves, Destino, ETA
- Click en fila → navegar a FleetPanel de esa flota
- Botón "← Galaxy" para volver al mapa

#### FleetPanel (enhanced)
- Detalle de una flota: nombre, posición, naves con diseño
- Split: seleccionar naves a mover y crear nueva flota (POST /fleet/{id}/split)
- Colonize: si hay colony ship y estamos en sistema con planetas no colonizados
- Move: seleccionar destino en el mapa

#### CombatResult
- Resumen visual del combate
- Naves de cada bando antes y después
- Indicador de victoria/derrota
- Botón continuar

#### VictoryScreen
- Pantalla de fin de juego mostrada cuando `game.status === "victory"` (victoria al derrotar Antares)
- Muestra trofeo 🏆 y mensaje de victoria con tipo (`antares`)
- Tabla de desglose de puntuación: colonias × 500, población × 10, tecnologías × 100, BC × 0.1, turnos × −2, total
- Tabla Hall of Fame: top-10 entradas de la colección `hall_of_fame` (nombre, raza, puntuación, fecha)
- Botón "Menú Principal" que navega de vuelta al menú

#### AITurnViewer
- Dos modos: pantalla completa o pantalla dividida
- Controles de reproducción (play, pause, step, velocidad)
- Animación secuencial de acciones de la IA
- Panel de reasoning/explicación de la IA (opcional)

#### CheatConsole
- Aparece con Ctrl+Tab
- Input de texto para escribir código de cheat
- Selector de target (si aplica)
- Log de cheats aplicados
- Botón cerrar

#### EventLogPanel
- Modal bloqueante que aparece al inicio de cada turno del jugador (tras resolver turno de IA)
- Lista todos los eventos del turno anterior en orden cronológico
- Cada evento con icono según tipo: combate (⚔️), colonización (🏴), investigación (💡), alerta (⚠️), edificio (🏗️), nave (🚀), Antarano (👾), victoria (🏆), derrota (💠)
- Colores: rojo (ataques, pérdidas, derrota), verde (completados, victorias, colonización), amarillo (alertas, escasez)
- Botón "Continuar" o tecla Escape para cerrar y comenzar turno
- Si no hay eventos, no aparece

### 4.3. Atajos de Teclado (MOO2-faithful)

El frontend implementa los siguientes atajos de teclado, fieles al Master of Orion II original.
Referencia: https://strategywiki.org/wiki/Master_of_Orion_II:_Battle_at_Antares/Hotkeys

**Estado**: ✅ Implementados en `App.tsx` (handler global en `useEffect` + `keydown`).

#### Mapa Galáctico (GalaxyMap)

| Tecla | Acción |
|-------|--------|
| `T` | Fin de turno |
| `G` | Ir al mapa galáctico |
| `C` | Abrir pantalla de Colonias |
| `F` | Abrir pantalla de Flotas |
| `R` | Abrir pantalla de Investigación (Research) |
| `L` | Abrir pantalla de Líderes |
| `D` | Abrir pantalla de Diplomacia |
| `S` | Abrir Diseñador de Naves |
| `I` | Abrir pantalla de Espionaje (Intel) |
| `+` / `=` | Zoom in |
| `-` | Zoom out |
| `0` | Reset zoom y pan |
| `Ctrl+Tab` / `` ` `` | Abrir consola de cheats |

#### Diálogos y Modales

| Tecla | Acción |
|-------|--------|
| `Y` | Confirmar / Continuar (TurnSummary, Council) |
| `Escape` | Cerrar modal / volver al mapa galáctico |

#### General

| Tecla | Acción |
|-------|--------|
| `Escape` | Cerrar cheat console → cerrar event log → volver al mapa |

> **Nota**: Los atajos solo se activan cuando no hay un `<input>` o `<textarea>` con foco, para evitar conflictos con la escritura de texto.

### 4.4. Estado Global (Store)

El frontend debe mantener un store global con:
```typescript
interface GameStore {
  // Auth
  user: User | null;
  token: string | null;
  
  // Game
  currentGame: GameState | null;
  selectedSystem: string | null;
  selectedColony: string | null;
  selectedFleet: string | null;
  
  // UI
  isAITurnPlaying: boolean;
  aiTurnActions: AIAction[];
  cheatConsoleOpen: boolean;
  eventLogOpen: boolean;
  turnEvents: GameEvent[];   // eventos del último turno para el EventLogPanel
  visualizationMode: 'fullscreen' | 'split';
  playbackSpeed: 'normal' | 'fast' | 'instant';
  
  // Actions
  login(username: string, password: string): Promise<void>;
  register(username: string, email: string, password: string): Promise<void>;
  loadGame(gameId: string): Promise<void>;
  saveGame(): Promise<void>;
  manageColony(colonyId: string, data: ColonyManageData): Promise<void>;
  selectResearch(field: string, level: number, techId: string): Promise<void>;
  moveFleet(fleetId: string, destination: string): Promise<void>;
  colonize(fleetId: string, planetIndex: number): Promise<void>;
  endTurn(): Promise<void>;
  applyCheat(code: string, target?: CheatTarget): Promise<void>;
}
```

### 4.5. Criterios de Aceptación Frontend

- [ ] Todas las rutas navegables sin errores
- [ ] Mapa galáctico renderiza correctamente todas las estrellas y conexiones
- [ ] Fog of war funcional (sistemas no explorados oscurecidos)
- [ ] Gestión de colonia con asignación de población y cola de construcción
- [ ] Árbol tecnológico interactivo con estados visuales
- [ ] Gestión de flotas con movimiento
- [ ] Visualización del turno de la IA en al menos 1 modo
- [ ] Consola de cheats funcional con Ctrl+Tab
- [ ] Responsive (funcional en pantallas ≥1024px de ancho)
- [ ] Sin errores en consola del navegador durante gameplay normal

---

## 5. INTEGRACIÓN LLM (GroQ / GitHub Models)

### 5.1. Configuración

```python
# .env
GROQ_API_KEY=gsk_xxxxxxxxxxxx
GROQ_MODEL_PRIMARY=llama-3.3-70b-versatile
GROQ_MODEL_FALLBACK=llama-3.1-8b-instant

GITHUB_TOKEN=ghp_xxxxxxxxxxxx
GITHUB_MODEL_PRIMARY=gpt-4o
GITHUB_MODEL_FALLBACK=gpt-4o-mini

AI_PROVIDER=groq  # or github
AI_MAX_RETRIES=3
AI_TIMEOUT_SECONDS=30
```

### 5.2. Servicio de IA — Estructura

```python
class AIService:
    def __init__(self, config: AIConfig):
        self.providers = [primary_provider, fallback_provider]
        self.current_provider_index = 0
    
    async def get_ai_turn(self, game_state: dict, ai_player: dict) -> list[AIAction]:
        """
        1. Prepare visible game state (respecting fog of war)
        2. Build prompt with game state
        3. Call LLM provider
        4. Parse response as JSON
        5. Validate actions against game rules
        6. Return valid actions
        """
        pass
    
    async def call_llm(self, prompt: str) -> str:
        """
        Try primary model, fallback on 429/500, retry up to MAX_RETRIES.
        """
        pass
    
    def prepare_visible_state(self, full_state: dict, ai_player_id: str) -> dict:
        """
        Filter game state to only include what the AI can see
        based on its fog of war.
        """
        pass
    
    def validate_actions(self, actions: list[dict], game_state: dict, ai_player_id: str) -> list[dict]:
        """
        Validate each action against game rules.
        Discard invalid actions silently.
        """
        pass
```

### 5.3. Formato de Prompt

Ver sección 14 del documento de práctica (`MasterDeHostias_practica.md`) para el prompt completo.

**Resumen del flujo:**
1. Prompt del sistema con reglas del juego
2. Estado visible del juego en JSON
3. Instrucción para analizar, planificar y devolver acciones en JSON
4. Parse de la respuesta
5. Validación de acciones

### 5.4. Manejo de Errores

| Error | Acción |
|-------|--------|
| 429 (Rate Limit) | Switch a modelo fallback |
| 500 (Server Error) | Reintentar hasta MAX_RETRIES, luego fallback |
| Timeout | Reintentar una vez, luego acciones por defecto |
| JSON inválido | Reintentar con instrucción de formato más estricta |
| Acciones inválidas | Descartar acción, mantener el resto |
| Todos los modelos fallan | Turno de IA = endTurn (no hace nada) |

### 5.5. Criterios de Aceptación LLM

- [ ] La IA toma decisiones cada turno (colonización, construcción, investigación, movimiento)
- [ ] La IA respeta las reglas del juego (no puede hacer acciones inválidas)
- [ ] La IA respeta el fog of war (no usa información oculta)
- [ ] Fallback funcional cuando el modelo primario falla
- [ ] Tiempo de respuesta < 30 segundos por turno de IA
- [ ] La IA proporciona un desafío mínimo (no solo pasa turno)
- [ ] Las acciones de la IA se devuelven para visualización
- [ ] Reasoning de la IA se registra para debug

---

## 6. MÓDULOS ESPECÍFICOS POR GRUPO

### 6.1. Grupo 1: Combate Táctico Completo

**Endpoints adicionales:**

#### POST /api/game/{gameId}/tactical-combat/{combatId}/action
Ejecuta una acción en el combate táctico.

**Request Body:**
```json
{
  "ship_id": "string",
  "action_type": "string (move|fire|special|retreat|board)",
  "target": {
    "position": {"x": "number", "y": "number"},
    "ship_id": "string (for fire/board)"
  }
}
```

**Response 200:**
```json
{
  "combat_state": {
    "grid": "12x12 array",
    "turn_order": ["ship_ids in initiative order"],
    "current_ship": "string",
    "ships": [
      {
        "id": "string",
        "type": "string",
        "owner": "string",
        "position": {"x": "number", "y": "number"},
        "hp": "number",
        "shields": "number",
        "weapons_cooldown": {}
      }
    ],
    "round": "number",
    "phase": "string (player_turn|ai_turn|resolution)"
  },
  "action_result": {
    "damage_dealt": "number",
    "target_destroyed": "boolean",
    "boarding_result": "string|null"
  }
}
```

**Modelos adicionales:**

```json
// TacticalCombatState
{
  "combat_id": "string",
  "grid_size": 12,
  "ships": ["TacticalShip"],
  "turn_order": ["string"],
  "current_turn": "number",
  "round": "number",
  "planetary_defenses": [{"type": "missile_base", "position": {"x": 10, "y": 6}, "hp": 50}]
}

// TacticalShip
{
  "id": "string",
  "base_ship": "Ship",
  "position": {"x": "number", "y": "number"},
  "initiative": "number (determines turn order)",
  "movement_remaining": "number",
  "weapons": [
    {
      "id": "string",
      "cooldown": "number",
      "max_cooldown": "number",
      "ammo": "number|null (null = unlimited)"
    }
  ],
  "special_abilities": ["boarding_pods", "point_defense", "ecm"]
}
```

**Reglas de combate táctico:**
- Cuadrícula 12×12
- Iniciativa = ship.speed + random(1-6)
- Movimiento: hasta `ship.speed` casillas por turno
- Disparo: solo si el objetivo está en rango del arma, línea de visión libre
- Misiles: rango 6, daño alto, 1 turno cooldown
- Rayos: rango 3, daño medio, sin cooldown
- Torpedos: rango 5, daño muy alto, 2 turnos cooldown
- Abordaje: adyacente al enemigo, check de marines vs crew
- Retirada: mover nave al borde del mapa, pierde el turno

**Criterios de aceptación:**
- [ ] Cuadrícula de combate renderizable
- [ ] Orden de turnos por iniciativa
- [ ] Movimiento, disparo y habilidades especiales funcionales
- [ ] IA toma decisiones tácticas (no solo aleatoria)
- [ ] Combate termina cuando un bando es eliminado o se retira
- [ ] Resultado se integra con el estado del juego principal

---

### 6.2. Grupo 2: Sistema de Espionaje

**Endpoints adicionales:**

#### GET /api/game/{gameId}/spies
Lista espías del jugador.

**Response 200:**
```json
{
  "spies": [
    {
      "id": "string",
      "name": "string",
      "skill": "number (1-10)",
      "status": "string (idle|training|mission|captured|dead)",
      "mission": {
        "type": "string|null",
        "target_player": "string|null",
        "turns_remaining": "number|null"
      }
    }
  ],
  "max_spies": "number",
  "training_cost": "number (BC)"
}
```

#### POST /api/game/{gameId}/spies/recruit
Recluta un nuevo espía.

**Response 201:**
```json
{
  "spy": {"id": "string", "name": "string", "skill": 1, "status": "training"},
  "training_turns": 3,
  "cost": "number"
}
```

#### POST /api/game/{gameId}/spies/{spyId}/mission
Asigna misión a un espía.

**Request Body:**
```json
{
  "mission_type": "string (steal_tech|sabotage|assassinate|incite_rebellion|counter_espionage)",
  "target_player": "string (ai_0|ai_1|...)"
}
```

**Response 200:**
```json
{
  "spy": "Spy (updated with mission)",
  "estimated_success": "number (percentage)",
  "estimated_turns": "number"
}
```

**Modelo adicional:**
```json
// Spy
{
  "id": "string",
  "name": "string",
  "owner": "string",
  "skill": "number (1-10)",
  "status": "string",
  "experience": "number",
  "mission": "SpyMission|null"
}

// SpyMission
{
  "type": "string",
  "target_player": "string",
  "turns_remaining": "number",
  "success_chance": "number (0-100)"
}
```

**Reglas de espionaje:**
```
success_chance = base_chance + (spy.skill × 5) + race.spy_bonus - target.counter_espionage
  where base_chance varies by mission type:
    steal_tech: 40%
    sabotage: 50%
    assassinate: 20%
    incite_rebellion: 30%
    counter_espionage: 60%

capture_chance = (100 - success_chance) × 0.5
death_chance = (100 - success_chance) × 0.2
```

**Criterios de aceptación:**
- [ ] Reclutamiento de espías con coste y tiempo de entrenamiento
- [ ] Asignación de misiones ofensivas y defensivas
- [ ] Resolución de misiones con resultados basados en probabilidad
- [ ] Contra-espionaje funcional
- [ ] Efectos de misiones se aplican al estado del juego (robar tech, sabotear, etc.)
- [ ] IA usa espionaje ofensivo y defensivo

---

### 6.3. Grupo 3: Constructor de Razas Personalizado

**Endpoints adicionales:**

#### POST /api/races/custom
Crea una raza personalizada.

**Request Body:**
```json
{
  "name": "string",
  "description": "string",
  "portrait_id": "string",
  "government": "string",
  "home_planet": {
    "name": "string",
    "type": "string",
    "size": "string"
  },
  "picks": [
    {"trait_id": "string", "level": "number"}
  ]
}
```

**Response 201:**
```json
{
  "race": "Race (complete with computed traits)",
  "total_picks_used": "number",
  "validation": {"valid": true}
}
```

**Response 400:**
```json
{"error": "Exceeds 10 picks | Invalid trait combination | Negative picks exceed limit"}
```

#### GET /api/races/traits
Lista rasgos disponibles para constructor de razas.

**Response 200:**
```json
{
  "positive_traits": [
    {"id": "string", "name": "string", "cost": "number", "levels": "number", "effect": "string"}
  ],
  "negative_traits": [
    {"id": "string", "name": "string", "refund": "number", "levels": "number", "effect": "string"}
  ],
  "special_traits": [
    {"id": "string", "name": "string", "cost": "number", "effect": "string"}
  ],
  "governments": [
    {"id": "string", "name": "string", "cost": "number", "effects": {}}
  ]
}
```

**Tabla de rasgos:**

| trait_id | name | cost/level | max_levels | effect |
|----------|------|-----------|------------|--------|
| `food_bonus` | Granjeros eficientes | +1 pick | 2 | +1/+2 comida por granjero |
| `industry_bonus` | Industriosos | +1 pick | 2 | +1/+2 producción por trabajador |
| `research_bonus` | Intelectuales | +1 pick | 2 | +25%/+50% investigación |
| `pop_growth` | Crecimiento rápido | +2 picks | 2 | +50%/+100% crecimiento |
| `ground_combat` | Guerreros natos | +1 pick | 2 | +10/+20 combate terrestre |
| `ship_attack` | Pilotos expertos | +1 pick | 2 | +25%/+50% ataque espacial |
| `spy_bonus` | Infiltrados | +1 pick | 2 | +10/+20 espionaje |
| `money_bonus` | Comerciantes | +1 pick | 1 | +1 BC per cápita |
| `creative` | Creativo | 8 picks | 1 | Accede a TODAS las techs de cada nivel |
| `telepathic` | Telepático | 6 picks | 1 | Control mental en invasiones |
| `lithovore` | Litívoro | 4 picks | 1 | No necesita comida |
| `subterranean` | Subterráneo | 3 picks | 1 | +10 def subterránea |
| `food_penalty` | Granjeros ineficientes | -1 pick | 1 | -1 comida por granjero |
| `industry_penalty` | Perezosos | -1 pick | 1 | -1 producción por trabajador |
| `research_penalty` | Anti-intelectuales | -1 pick | 1 | -25% investigación |
| `pop_slow` | Crecimiento lento | -2 picks | 1 | -50% crecimiento |
| `ground_weak` | Pacifistas | -1 pick | 1 | -10 combate terrestre |

**Gobiernos:**

| government | cost | effects |
|-----------|------|---------|
| `dictatorship` | 0 | Base (sin bonus) |
| `democracy` | 7 | +morale, +trade, -puede declarar guerra solo cada 10 turnos |
| `unification` | 6 | +producción, +espionaje, -diplomacia |
| `feudalism` | -2 | +buques, -moral, -investigación |

**Reglas del constructor:**
- Total picks = 10 base
- Picks de rasgos positivos + coste de gobierno ≤ 10 + picks devueltos por negativos
- Máximo 10 picks en desventajas (no puede ganar más de 10 picks extra)
- Combinaciones prohibidas: creative + research_penalty

**Criterios de aceptación:**
- [ ] UI interactivo de creación de raza con contador de picks en tiempo real
- [ ] Validación de combinación de rasgos completa
- [ ] Los rasgos de la raza personalizada se aplican en toda la lógica del juego
- [ ] La IA ajusta su estrategia basándose en la raza personalizada del jugador
- [ ] Mínimo 3 razas predefinidas + opción de personalizada

---

### 6.4. Grupo 4: Motor de Diplomacia

**Endpoints adicionales:**

#### GET /api/game/{gameId}/diplomacy
Estado diplomático con todos los jugadores conocidos.

**Response 200:**
```json
{
  "relations": [
    {
      "player_id": "string",
      "race_name": "string",
      "relation_score": "number (-100 to +100)",
      "attitude": "string (hostile|cautious|neutral|friendly|allied)",
      "active_treaties": [
        {"type": "string", "turns_active": "number"}
      ],
      "contact_established": "boolean"
    }
  ],
  "council": {
    "next_vote_turn": "number",
    "last_result": {}
  }
}
```

#### POST /api/game/{gameId}/diplomacy/{targetPlayerId}/propose
Propone un tratado.

**Request Body:**
```json
{
  "treaty_type": "string (non_aggression|trade|alliance|tech_exchange)",
  "offer": {
    "bc": "number|null",
    "tech_id": "string|null",
    "system_id": "string|null"
  }
}
```

**Response 200:**
```json
{
  "accepted": "boolean",
  "counter_offer": {} | null,
  "reasoning": "string (AI explanation for accept/reject)"
}
```

#### POST /api/game/{gameId}/diplomacy/{targetPlayerId}/demand
Exige algo a otro jugador.

**Request Body:**
```json
{
  "demand_type": "string (tribute_bc|tribute_tech|leave_system)",
  "details": {}
}
```

#### GET /api/game/{gameId}/diplomacy/council
Estado del Consejo Galáctico.

**Response 200:**
```json
{
  "next_vote_turn": "number",
  "candidates": [
    {"player_id": "string", "race_name": "string", "population": "number", "votes": "number"}
  ],
  "total_votes": "number",
  "threshold": "number (2/3 of total)"
}
```

#### POST /api/game/{gameId}/diplomacy/council/vote
Vota en el Consejo.

**Request Body:**
```json
{
  "vote_for": "string (player_id)"
}
```

**Reglas de diplomacia:**
```
treaty_acceptance_chance = base + relation_score_modifier + personality_modifier + offer_value
  where:
    base: 30%
    relation > 50: +30%
    relation > 0: +10%
    relation < -50: -40%
    personality aggressive: -20% for peace treaties
    personality pacifist: +20% for peace treaties
    offer_value: BC/10 or tech_level × 5
```

**Relaciones — Modificadores:**

| Event | Relation Change |
|-------|----------------|
| Declare war | -50 |
| Break treaty | -30 |
| Win combat vs them | -10 |
| Trade treaty active | +2/turn |
| Gift (BC or tech) | +gift_value/10 |
| Alliance active | +3/turn |
| Demand tribute (accepted) | -5 |
| Demand tribute (refused) | -10 |

**Criterios de aceptación:**
- [ ] Pantalla de diplomacia con información de cada raza conocida
- [ ] Propuestas y contra-ofertas funcionales
- [ ] Tratados con efectos en el juego (comercio genera BC, alianza = defensa mutua)
- [ ] Consejo Galáctico con votaciones periódicas
- [ ] Victoria por Consejo funcional
- [ ] IA con personalidad diplomática diferenciada
- [ ] Relaciones numéricas que evolucionan según eventos

---

### 6.5. Grupo 5: Taller de Diseño de Naves

**Endpoints adicionales:**

#### GET /api/game/{gameId}/ship-designs
Lista diseños de naves activos.

**Response 200:**
```json
{
  "designs": [
    {
      "design_id": "string",
      "name": "string",
      "hull": "string (frigate|destroyer|cruiser|battleship|titan|doom_star)",
      "components": [
        {"slot": "string (weapon|shield|armor|engine|special)", "component_id": "string", "name": "string"}
      ],
      "stats": {
        "attack": "number",
        "defense": "number",
        "hp": "number",
        "speed": "number",
        "space_used": "number",
        "space_total": "number",
        "cost": "number",
        "command_points": "number"
      },
      "is_default": "boolean"
    }
  ],
  "max_active_designs": 5
}
```

#### POST /api/game/{gameId}/ship-designs
Crea un nuevo diseño de nave.

**Request Body:**
```json
{
  "name": "string",
  "hull": "string",
  "components": [
    {"slot": "string", "component_id": "string"}
  ]
}
```

**Response 201:**
```json
{
  "design": "ShipDesign",
  "validation": {"valid": true, "space_remaining": "number"}
}
```

**Response 400:**
```json
{"error": "Exceeds space limit | Component requires tech not researched | Max designs reached"}
```

#### POST /api/game/{gameId}/ship-designs/{designId}/refit
Reequipa naves existentes a un nuevo diseño.

**Request Body:**
```json
{
  "fleet_id": "string",
  "ship_type": "string",
  "new_design_id": "string"
}
```

**Response 200:**
```json
{
  "refit_cost": "number (50% of new design cost)",
  "turns_required": "number",
  "fleet": "Fleet (updated)"
}
```

**Modelo de componentes:**

| component_id | slot | space | effect | tech_req |
|--------------|------|-------|--------|----------|
| `laser_cannon` | weapon | 3 | dmg: 1-4, range: 3, beam | physics_1 |
| `fusion_beam` | weapon | 5 | dmg: 2-6, range: 4, beam | physics_2 |
| `phasor` | weapon | 8 | dmg: 5-15, range: 5, beam | physics_3 |
| `nuclear_missile` | weapon | 4 | dmg: 4-8, range: 8, missile | chemistry_1 |
| `merculite_missile` | weapon | 6 | dmg: 6-14, range: 10, missile | chemistry_2 |
| `nuclear_bomb` | weapon | 4 | colony damage: 1, range: 0 | power_1 |
| `class_i_shield` | shield | 3 | absorb: 1 | force_fields_1 |
| `class_iii_shield` | shield | 5 | absorb: 3 | force_fields_2 |
| `class_v_shield` | shield | 8 | absorb: 5 | force_fields_3 |
| `titanium_armor` | armor | 3 | +5 hp | chemistry_1 |
| `zortrium_armor` | armor | 5 | +15 hp | chemistry_2 |
| `nuclear_engine` | engine | 4 | speed: 2 | power_1 |
| `fusion_engine` | engine | 5 | speed: 3 | power_2 |
| `ion_engine` | engine | 6 | speed: 4 | power_3 |
| `battle_scanner` | special | 2 | +50% to-hit | computers_3 |
| `ecm_jammer` | special | 3 | -30% enemy to-hit | computers_2 |

**Espacio por casco:**

| hull | base_space | miniaturization_per_level |
|------|-----------|--------------------------|
| `frigate` | 15 | +2 |
| `destroyer` | 30 | +3 |
| `cruiser` | 60 | +5 |
| `battleship` | 120 | +8 |
| `titan` | 200 | +12 |
| `doom_star` | 400 | +20 |

Miniaturización: `available_space = base_space + (num_researched_techs × miniaturization_per_level)`

**Criterios de aceptación:**
- [ ] UI de diseño de naves con drag-and-drop de componentes
- [ ] Validación de espacio/peso en tiempo real
- [ ] Componentes filtrados por nivel tecnológico del jugador
- [ ] Preview de estadísticas finales
- [ ] Reequipamiento de naves existentes con coste reducido
- [ ] La IA genera diseños optimizados
- [ ] Los diseños personalizados se usan en combate (auto-resolve o táctico)

---

### 6.6. Grupo 6: Soporte de Galaxia Grande

**Endpoints adicionales:**

#### POST /api/games (modificado)
Acepta sizes adicionales.

**Request Body additions:**
```json
{
  "scenario_config": {
    "galaxy_size": "string (small|medium|large)",
    "num_opponents": "number (1|2|3)"
  }
}
```

**Tamaños de galaxia:**

| size | num_systems | num_opponents | special_features |
|------|-----------|--------------|-----------------|
| `small` | 20-30 | 1 | Core |
| `medium` | 40-50 | 2 | +wormholes, star types |
| `large` | 60-80 | 3 | +clusters, spiral arms |

**Endpoints adicionales:**

#### GET /api/game/{gameId}/galaxy?page={n}&viewport={x1,y1,x2,y2}
Devuelve sistemas estelares paginados o filtrados por viewport.

**Response 200:**
```json
{
  "star_systems": ["StarSystem (within viewport)"],
  "total_systems": "number",
  "viewport": {"x1": 0, "y1": 0, "x2": 800, "y2": 600}
}
```

**Modelo adicional — Wormhole:**
```json
{
  "id": "string",
  "system_a": "string (system_id)",
  "system_b": "string (system_id)",
  "bidirectional": true,
  "travel_time": 1
}
```

**Generación de galaxia:**
```python
def generate_galaxy(size: str) -> GalaxyState:
    """
    Algorithm:
    1. Generate N star systems with random positions
    2. Use Delaunay triangulation for connections (ensures connectivity)
    3. Prune connections to max 4 per system
    4. For medium+: add 1-3 wormholes between distant systems
    5. For large: create 2-3 clusters with sparse inter-cluster connections
    6. Assign star types based on position (blue in center, red at edges)
    7. Generate planets per system based on star type
    8. Place Orion system near center
    9. Place home systems for players at maximum distance from each other
    10. Add Antares hidden star (is_antares=true, x=-999, y=-999, owner="antaran")
        - Solo accesible via Dimensional Portal; NO aparece en el mapa galáctico
        - Filtrado en galaxyRenderer.ts: excluido de bounds, render, hit-test y wormholes
    """
```

**Estrella especial: Antares**

```json
{
  "name": "Antares",
  "x": -999, "y": -999,
  "color": "red",
  "owner": "antaran",
  "is_antares": true,
  "index": <last_index>
}
```

Esta estrella existe en la base de datos pero **nunca se renderiza** en el cliente. El `galaxyRenderer.ts` la filtra en los 4 bucles (bounds, wormholes, estrellas, hit-test) comprobando `is_antares || x < 0 || y < 0`.

**Multi-IA:**
```python
async def process_ai_turns(game_state: dict, ai_players: list) -> list:
    """
    Process multiple AI turns sequentially.
    Each AI has its own personality and fog of war.
    Actions visible to player are aggregated.
    """
    all_actions = []
    for ai in ai_players:
        visible_state = prepare_visible_state(game_state, ai.id)
        personality_prompt = get_personality_prompt(ai.personality)
        actions = await get_ai_turn(visible_state, personality_prompt)
        apply_actions(game_state, actions)
        all_actions.extend(filter_visible(actions, player_fog))
    return all_actions
```

**Personalidades de IA:**

| personality | behavior |
|------------|----------|
| `aggressive` | Prioriza militar, declara guerra pronto, invade rápido |
| `defensive` | Construye defensas, investiga escudos, negocia paz |
| `expansionist` | Coloniza agresivamente, prefiere planetas grandes |
| `researcher` | Prioriza investigación, tech rush, usa superioridad tech |
| `balanced` | Equilibra todas las áreas, adaptable |

**Criterios de aceptación:**
- [ ] Galaxias medianas y grandes generadas correctamente
- [ ] Hasta 3 IAs simultáneas con personalidades diferentes
- [ ] Agujeros de gusano funcionales
- [ ] Mapa escalable con minimapa y/o zoom
- [ ] Rendimiento aceptable (< 2s para cargar mapa completo)
- [ ] Turno de múltiples IAs procesado correctamente
- [ ] Tipos de estrellas afectan a la generación de planetas

---

## 7. DOCKER & DEPLOYMENT

### 7.1. Estructura de Contenedores

```yaml
# docker-compose.yml
version: '3.8'

services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://localhost:8000
    depends_on:
      - backend

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - MONGODB_URI=mongodb://mongodb:27017/masterdeHostias
      - JWT_SECRET=${JWT_SECRET}
      - AI_SERVICE_URL=http://ai-service:8001
    depends_on:
      - mongodb
      - ai-service

  mongodb:
    image: mongo:7
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db

  ai-service:
    build: ./ai-service
    ports:
      - "8001:8001"
    environment:
      - GROQ_API_KEY=${GROQ_API_KEY}
      - GROQ_MODEL_PRIMARY=${GROQ_MODEL_PRIMARY}
      - GROQ_MODEL_FALLBACK=${GROQ_MODEL_FALLBACK}
      - GITHUB_TOKEN=${GITHUB_TOKEN}
      - GITHUB_MODEL_PRIMARY=${GITHUB_MODEL_PRIMARY}
      - GITHUB_MODEL_FALLBACK=${GITHUB_MODEL_FALLBACK}
      - AI_PROVIDER=${AI_PROVIDER}

volumes:
  mongo_data:
```

### 7.2. Variables de Entorno (.env)

```env
# JWT
JWT_SECRET=your-secret-key-here

# AI Provider (groq or github)
AI_PROVIDER=groq

# GroQ
GROQ_API_KEY=gsk_xxxxxxxxxxxx
GROQ_MODEL_PRIMARY=llama-3.3-70b-versatile
GROQ_MODEL_FALLBACK=llama-3.1-8b-instant

# GitHub Models
GITHUB_TOKEN=ghp_xxxxxxxxxxxx
GITHUB_MODEL_PRIMARY=gpt-4o
GITHUB_MODEL_FALLBACK=gpt-4o-mini
```

### 7.3. Criterios de Aceptación Deployment

- [ ] `docker compose up --build` arranca los 4 contenedores sin errores
- [ ] Frontend accesible en `http://localhost:3000`
- [ ] Backend responde en `http://localhost:8000/api/`
- [ ] MongoDB persiste datos entre reinicios (volumen)
- [ ] Variables de entorno correctamente propagadas
- [ ] Healthcheck funcional en cada servicio

### 7.4. Regla de Deployment — Siempre Rebuild

> **CRÍTICO:** `docker compose restart` reutiliza la imagen antigua del contenedor. Los cambios de código NO se aplican.

Para que los cambios lleguen a los contenedores en ejecución, **siempre** seguir este procedimiento:

```bash
# Opción A — rebuild completo (recomendado tras cambios en Dockerfile o dependencias)
docker compose build --no-cache <servicio>
docker compose up -d --no-deps --force-recreate <servicio>

# Opción B — rebuild incremental (solo fuente Python/backend)
docker cp backend/app/routes/combat.py mmoh-backend:/app/app/routes/combat.py
docker compose restart backend   # válido solo si el .py ya está en el contenedor

# Verificar que el código correcto está en el contenedor ANTES de reiniciar:
docker exec mmoh-backend grep -n "from bson" /app/app/routes/combat.py
```

| ¿Qué cambió? | Comando |
|---|---|
| Código Python (ruta) | `docker cp <archivo> mmoh-backend:/app/... && docker compose restart backend` |
| Dependencias Python (`requirements.txt`) | `docker compose build --no-cache backend && docker compose up -d --no-deps --force-recreate backend` |
| Código TypeScript/React | `docker compose build --no-cache frontend && docker compose up -d --no-deps --force-recreate frontend` |
| Dockerfile modificado | `docker compose build --no-cache <servicio> && docker compose up -d --no-deps --force-recreate <servicio>` |

---

## 8. CRITERIOS DE ACEPTACIÓN GLOBALES

### 8.1. Funcionalidad Core (todos los grupos)

- [ ] **Registro/Login**: Usuarios pueden registrarse y loguearse
- [ ] **Crear partida**: Se genera galaxia con estrellas, planetas y conexiones
- [ ] **Guardar/Cargar**: Partidas se guardan y cargan correctamente
- [ ] **Mapa galáctico**: Estrellas renderizadas con fog of war
- [ ] **Exploración**: Flotas revelan sistemas al visitarlos
- [ ] **Colonización**: Nave colonizadora → nueva colonia con 1 pop
- [ ] **Gestión colonia**: Asignar población, construir edificios/naves
- [ ] **Investigación**: Seleccionar tech, progreso por turno, desbloqueos
- [ ] **Naves/Flotas**: Construir naves, formar flotas, mover entre sistemas
- [ ] **Combate auto**: Resolución automática con bajas y resultado
- [ ] **Invasión terrestre**: Captura de colonias
- [ ] **Turno IA**: IA toma decisiones vía LLM, acciones visualizadas
- [ ] **Cheats**: Consola Ctrl+Tab con códigos funcionales
- [ ] **Victoria/Derrota**: Detección de condiciones de fin de juego
- [ ] **Deployment**: 4 contenedores Docker funcionando con `docker compose up`

### 8.2. Calidad de Código

- [ ] Sin secretos hardcodeados (usar .env)
- [ ] Manejo de errores en endpoints (4xx, 5xx apropiados)
- [ ] Input validation en todos los endpoints
- [ ] Código organizado en módulos/carpetas lógicas
- [ ] README con instrucciones claras de setup y ejecución

### 8.3. Integración LLM

- [ ] IA toma decisiones coherentes (coloniza, construye, investiga, ataca)
- [ ] Fallback funcional entre modelos
- [ ] Fog of war respetado por la IA
- [ ] Tiempo de respuesta razonable (< 30s por turno)

### 8.4. Interfaz

- [ ] Estética coherente sci-fi
- [ ] Navegación fluida entre vistas
- [ ] Información claramente presentada
- [ ] Sin errores JavaScript en consola durante uso normal

---

## 9. Changelog — Auditoría y Mejoras

### 9.1. Bug Fixes (Auditoría)

| Bug | Descripción | Corrección |
|-----|------------|------------|
| **tech_req mismatch** | `buildings.json` usa `tech_req` como `construction_1` (campo+nivel) pero los IDs reales de tech son `colony_base`, `star_base_tech`, etc. Ningún edificio aparecía en la cola de construcción | Añadido `_FIELD_LEVEL_TECHS` lookup y helper `_has_tech_req()` en `colony_service.py` |
| **Cloning center flat vs multiplicative** | El bonus de cloning center se sumaba como flat en vez de multiplicar | Cambiado a multiplicativo (ej. +50% = ×1.5) |
| **Morale threshold** | El umbral de overpop usaba `pop > max × 0.9` | Corregido a `pop > max_population` |
| **Research overflow lost** | El overflow de investigación se perdía al completar una tech | Se almacena `research_overflow` y se aplica al siguiente turno |
| **3 propulsion techs missing** | `nuclear_engines`, `fusion_drive`, `ion_drive` faltaban del árbol | Añadidos a `tech_tree.json` |
| **Ship HP double-count** | La armadura se contaba dos veces en HP de naves | Corregido cálculo de HP |
| **Spy training never completing** | Los espías nunca terminaban su entrenamiento | Corregido tick de entrenamiento en `turn_engine.py` |
| **Combat ignoring diplomacy** | El combate se ejecutaba sin verificar estado diplomático | Añadida verificación de diplomacia antes de combate |
| **max_pop display bug** | Backend envía `max_population` pero frontend usaba `max_pop` → mostraba `8/undefined` | Renombrado `max_pop` → `max_population` en `colony.ts` y todos los componentes |

### 9.2. Nuevas Features

| Feature | Descripción |
|---------|------------|
| **Autobuild** | Cuando la cola de construcción está vacía y `autobuild=true`, selecciona automáticamente el edificio más barato disponible. Si no hay edificios, produce trade goods |
| **Trade goods fallback** | Trade goods convierte producción a BC, nunca se completa |
| **Game Menu (ESC)** | Menú in-game accesible con ESC o botón ☰: Resume, Save, Colony List, Quit to Main Menu |
| **Colony List (C)** | Tabla sortable con todas las colonias del jugador: Planeta, Pop, Morale, Food, Prod, Research, BC, Cola. Click en fila abre colonia |
| **Game Speed** | Selector en New Game: Fast (0.5× costes), Normal (1×), Slow (2×). Afecta producción efectiva e investigación |
| **Settings Persistence** | Los ajustes de New Game (tamaño, dificultad, IA, raza, velocidad) se guardan en localStorage |
| **Spiral Galaxy Background** | Fondo de galaxia espiral procedural con 4 brazos, 900 partículas/brazo, núcleo brillante warm, nebulosas y polvo estelar. Textura 2048px cacheada, colores cálidos amarillo→azul. Mucho más visible que la versión original |
| **Smooth Zoom** | Zoom suave con `requestAnimationFrame` + lerp (factor 0.18) hacia cursor, rango 0.3×–6×, multiplicativo |
| **Fleet Split** | `POST /fleet/{id}/split` — dividir flota seleccionando naves a mover a nueva flota |
| **Fleet List (F)** | Pantalla FleetList con tabla sortable de todas las flotas del jugador, accesible con tecla F |
| **Build Queue Reorder** | Botones ▲/▼ en cada elemento de la cola de construcción para reordenar prioridades |
| **Planet max_pop** | La ruta `/galaxy` ahora incluye `max_pop` en cada planeta (derivado del tamaño: tiny=8, small=12, medium=16, large=22, huge=28), visible en SystemView |
| **RUSHBUY Cheat** | Completa inmediatamente el primer elemento de la cola de todas las colonias |
| **CRUNCH Cheat** | Completa inmediatamente TODA la cola de construcción de todas las colonias |
| **Antares guard** | `POST /combat/attack-antares` devuelve HTTP 400 si `game.antares_defeated == true`. Imposible atacar Antares dos veces |
| **Victoria al derrotar Antares** | Derrotar Antares termina la partida: `game.status="victory"`, `game.victory_type="antares"`, puntuación calculada e insertada en `hall_of_fame`, respuesta incluye `status="victory"` y `score` breakdown |
| **Fórmula de puntuación** | `colonias×500 + pop×10 + techs×100 + BC×0.1 − turnos×2` |
| **Hall of Fame** | Nueva colección MongoDB `hall_of_fame`. `GET /game/{id}/combat/hall-of-fame` devuelve top-10 por score desc |
| **VictoryScreen** | Nuevo componente `VictoryScreen.tsx`. Muestra desglose de puntuación + tabla Hall of Fame. Activado con `uiStore.screen === "victory"` |
| **Star label color** | La etiqueta del nombre de estrella se colorea en verde cuando el jugador coloniza ese sistema. `galaxyRenderer.ts` comprueba `star.owner === "player" \|\| hasPlayerColony` |
| **Star owner on colonize** | `fleet.py` colonize route ahora establece `star["owner"] = "player"` y llama `GalaxyModel.update_star` para persistir el cambio |

### 9.3. Cambios en Modelo de Datos

- `games` collection: nuevo campo `game_speed` (string: `"fast"` | `"normal"` | `"slow"`, default `"normal"`)
- `POST /api/game/new` acepta parámetro `speed` opcional
- `NewGameOptions` tipo frontend: campo `speed` opcional
- `Colony` tipo frontend: `max_pop` renombrado a `max_population`
- `games` collection: campos `status` ("active"|"victory"|"defeat"), `victory_type` ("antares"|null), `antares_defeated` (bool, default false)
- Nueva colección `hall_of_fame`: `{ game_id, username, race, score, colonies, population, techs, bc, turns, date }`
- `Screen` type en `uiStore.ts`: añadido `"victory"`
- `GameStore.attackAntares()`: si response contiene `status === "victory"`, establece `game.status = "victory"` y navega a pantalla `"victory"`
