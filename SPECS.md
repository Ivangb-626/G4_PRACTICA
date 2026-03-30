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
  "field": "string",
  "level": "number (1-3+)",
  "name": "string",
  "description": "string",
  "research_cost": "number",
  "alternative_group": "number (technologies in same group are mutually exclusive)",
  "unlocks": {
    "buildings": ["string"],
    "ship_components": ["string"],
    "abilities": ["string"]
  }
}
```

**Árbol Tecnológico Simplificado (Core — mínimo 3 niveles × 8 campos = 24 techs):**

| field | level | options (choose 1) | research_cost |
|-------|-------|-------------------|---------------|
| construction | 1 | automated_factory, reinforced_hull | 50 |
| construction | 2 | star_base, pollution_processor | 150 |
| construction | 3 | robotic_factory, advanced_city_planning | 400 |
| power | 1 | nuclear_engine, nuclear_bomb | 50 |
| power | 2 | fusion_engine, augmented_engine | 150 |
| power | 3 | ion_engine, high_energy_focus | 400 |
| chemistry | 1 | nuclear_missile, titanium_armor | 50 |
| chemistry | 2 | merculite_missile, zortrium_armor | 150 |
| chemistry | 3 | pulson_missile, adamantium_armor | 400 |
| sociology | 1 | trade_center, morale_boost | 50 |
| sociology | 2 | planetary_supercomputer, advanced_government | 150 |
| sociology | 3 | galactic_unification, telepathic_training | 400 |
| computers | 1 | electronic_computer, scanner | 50 |
| computers | 2 | positronic_computer, deep_scanner | 150 |
| computers | 3 | cybertronic_computer, battle_scanner | 400 |
| biology | 1 | hydroponic_farm, biosphere | 50 |
| biology | 2 | soil_enrichment, cloning_center | 150 |
| biology | 3 | terraforming, evolutionary_mutation | 400 |
| physics | 1 | laser_cannon, laser_rifle | 50 |
| physics | 2 | fusion_beam, ion_cannon | 150 |
| physics | 3 | phasor, plasma_cannon | 400 |
| force_fields | 1 | class_i_shield, mass_driver | 50 |
| force_fields | 2 | class_iii_shield, personal_shield | 150 |
| force_fields | 3 | class_v_shield, planetary_barrier | 400 |

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

#### GET /api/games/{gameId}
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

#### POST /api/games/{gameId}/save
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

#### DELETE /api/games/{gameId}
Elimina una partida guardada.

**Headers:** `Authorization: Bearer <JWT>`

**Response 200:**
```json
{"success": true}
```

---

### 2.3. Acciones en Partida

Todos los endpoints de esta sección requieren `Authorization: Bearer <JWT>` y validan que la partida pertenece al usuario.

#### POST /api/games/{gameId}/colony/{colonyId}/manage
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

#### POST /api/games/{gameId}/research
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

#### POST /api/games/{gameId}/fleet/{fleetId}/move
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

#### POST /api/games/{gameId}/colonize
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

#### POST /api/games/{gameId}/endTurn
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
- [ ] Procesa fin de turno del jugador: recursos, crecimiento, investigación, producción, combates
- [ ] Ejecuta turno de la IA (llamada a LLM)
- [ ] Devuelve lista de acciones de IA para visualización (solo las visibles al jugador)
- [ ] Incluye eventos generados (combates, investigaciones completadas, etc.)
- [ ] Autoguarda la partida
- [ ] Detecta condiciones de victoria/derrota
- [ ] Incrementa contador de turno

---

#### POST /api/games/{gameId}/cheat
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

| code | requires_target | effect |
|------|----------------|--------|
| `recursos_infinitos` | No | BC = 99999, comida máxima en todas las colonias |
| `revelar_galaxia` | No | Toda la galaxia visible (elimina fog of war) |
| `tecnologia_total` | No | Investiga todas las tecnologías |
| `flota_invencible` | star_system | Añade 10 acorazados al sistema |
| `victoria_inmediata` | No | Gana la partida |
| `derrota_inmediata` | No | Pierde la partida |
| `colonizar_todo` | star_system | Coloniza todos los planetas del sistema |
| `poblacion_maxima` | colony | Maximiza población de la colonia |
| `naves_gratis` | No | Coste 0 para naves este turno |
| `guardian_eliminado` | No | Elimina Guardián de Orion |
| `antaranos_desactivados` | No | Desactiva ataques de los Antaranos |

**Criterios de aceptación:**
- [ ] Cada cheat produce el efecto descrito
- [ ] Cheats que requieren target devuelven error si no se proporciona
- [ ] Los cheats se registran en `cheats_used` del estado de juego
- [ ] Los cheats se loguean en el servidor para debug

---

### 2.4. Consultas de Estado

#### GET /api/games/{gameId}/galaxy
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

#### GET /api/games/{gameId}/tech-tree
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

#### GET /api/games/{gameId}/colony/{colonyId}
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

### 3.1. Economía de Colonia

#### Producción de Comida
```
food_per_farmer = 1 + planet.food_modifier + race.food_bonus + tech_bonuses
food_produced = farmers × food_per_farmer
food_consumed = total_population × 1
food_surplus = food_produced - food_consumed
```
- Si `food_surplus < 0`: la colonia pierde 1 de población por turno
- Si `food_surplus > 0`: la colonia gana población según tasa de crecimiento

#### Producción Industrial
```
base_production = workers × 2
mineral_modifier = planet.minerals_modifier  // 0.33 to 2.0
building_bonuses = sum(building.production_bonus)
race_bonus = race.industry_bonus × workers
production_output = (base_production + building_bonuses + race_bonus) × mineral_modifier
```

#### Producción Científica
```
base_research = scientists × 2
building_bonuses = sum(building.research_bonus)
race_bonus = total_research × (race.research_bonus / 100)
research_output = base_research + building_bonuses + race_bonus
```

#### Recaudación de BC
```
colony_bc = building_bc_bonuses + (race.trade_bonus × total_population)
total_bc = sum(all_colonies.colony_bc) - sum(all_maintenance)
```

### 3.2. Crecimiento de Población

```
base_growth_rate = 0.5 per turn (if food_surplus > 0)
race_modifier = 1 + (race.population_growth_bonus / 100)
max_pop = planet.max_pop_base + tech_bonuses
growth = base_growth_rate × race_modifier × (1 - current_pop / max_pop)
new_population = min(current_pop + growth, max_pop)
```

### 3.3. Investigación

```
total_empire_research = sum(all_colonies.research_output)
research_progress += total_empire_research
if research_progress >= tech.research_cost:
    tech is completed
    unlock tech effects
    prompt for next research selection
```

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

### 3.6. Combate Automático (Core)

```
attacker_strength = sum(ship.attack × ship.count for each ship type)
defender_strength = sum(ship.attack × ship.count for each ship type) + orbital_defense

rounds = 5
for each round:
    attacker_damage = attacker_strength × random(0.8, 1.2) - defender.total_shields
    defender_damage = defender_strength × random(0.8, 1.2) - attacker.total_shields
    
    // Remove destroyed ships (weakest first)
    remove_ships(defender, attacker_damage)
    remove_ships(attacker, defender_damage)
    
    // Recalculate strengths
    recalculate_strengths()

if attacker has ships remaining and defender doesn't: attacker wins
elif defender has ships remaining and attacker doesn't: defender wins
elif both have ships: stalemate (attacker retreats)
```

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
- **Derrota**: `count(player_colonies) == 0 AND count(player_fleets) == 0`

### 3.10. Moral

| morale | production_modifier | description |
|--------|-------------------|-------------|
| `jubilant` | +20% | Felicidad máxima |
| `happy` | +10% | Contentos |
| `stable` | 0% | Normal |
| `unrest` | -20% | Descontentos |
| `revolt` | -50%, no growth | Sublevación |

Factores que afectan moral:
- Gobierno tipo (Unificación +2, Democracia +1, Dictadura 0, Feudalismo -1)
- Conquista reciente de la colonia: -2 durante 5 turnos
- Sobrepoblación (pop > max\_pop × 0.9): -1
- Edificios de moral (ej. Virtual Reality Center): +1

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

**Cheat:** `antaranos_desactivados` establece `antaran_next_attack_turn = null` e impide futuros ataques.

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

#### SystemView
- Renderizar planetas orbitando la estrella
- Información de cada planeta (tipo, tamaño, minerales, gravedad, colonia)
- Click en planeta colonizado → navegar a ColonyView
- Botón colonizar (si hay nave colonizadora en el sistema)

#### ColonyView
- Sliders o selectores para asignar población (Farmers/Workers/Scientists)
- Barras de producción (comida, industria, investigación, BC)
- Lista de edificios construidos con iconos
- Cola de construcción drag-and-drop (hasta 7 elementos)
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

#### CombatResult
- Resumen visual del combate
- Naves de cada bando antes y después
- Indicador de victoria/derrota
- Botón continuar

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

El frontend debe implementar los siguientes atajos de teclado, fieles al Master of Orion II original.

#### Mapa Galáctico (GalaxyMap)

| Tecla | Acción |
|-------|--------|
| `T` | Fin de turno |
| `C` | Abrir pantalla de Colonias |
| `F` | Abrir pantalla de Flotas |
| `P` | Abrir pantalla de Planetas |
| `R` | Abrir pantalla de Razas |
| `G` | Abrir menú de Juego (guardar, cargar, opciones) |
| `I` | Abrir pantalla de Información |
| `L` | Abrir pantalla de Líderes |
| `F1` | Ir a siguiente colonia |
| `F2` | Ir a anterior colonia |
| `F4` | Reubicar colonos |
| `F7` | Ciclar flotas enemigas detectadas |
| `F8` | Ciclar colonias enemigas detectadas |
| `F9` | Herramienta de medición de parsecs |
| `F10` | Guardar partida rápido |
| `Alt+F` | Alternar visibilidad de rutas de flotas |
| `+` / `Shift+=` / `Num+` | Zoom in |
| `-` / `Num-` | Zoom out |
| `Ctrl+Tab` | Abrir consola de cheats |

#### Diálogos y Modales

| Tecla | Acción |
|-------|--------|
| `Y` | Confirmar (equivale a botón "Sí") |
| `N` | Cancelar (equivale a botón "No") |
| `Escape` | Cerrar modal / volver atrás |
| `Enter` | Aceptar opción por defecto |

#### ColonyView

| Tecla | Acción |
|-------|--------|
| `F1` | Siguiente colonia |
| `F2` | Anterior colonia |
| `Escape` | Volver al mapa galáctico |

#### General

| Tecla | Acción |
|-------|--------|
| `Q` | Salir / Cerrar ventana actual |

> **Nota**: Los atajos solo deben activarse cuando no hay un `<input>` o `<textarea>` con foco, para evitar conflictos con la escritura de texto.

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

#### POST /api/games/{gameId}/tactical-combat/{combatId}/action
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

#### GET /api/games/{gameId}/spies
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

#### POST /api/games/{gameId}/spies/recruit
Recluta un nuevo espía.

**Response 201:**
```json
{
  "spy": {"id": "string", "name": "string", "skill": 1, "status": "training"},
  "training_turns": 3,
  "cost": "number"
}
```

#### POST /api/games/{gameId}/spies/{spyId}/mission
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

#### GET /api/games/{gameId}/diplomacy
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

#### POST /api/games/{gameId}/diplomacy/{targetPlayerId}/propose
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

#### POST /api/games/{gameId}/diplomacy/{targetPlayerId}/demand
Exige algo a otro jugador.

**Request Body:**
```json
{
  "demand_type": "string (tribute_bc|tribute_tech|leave_system)",
  "details": {}
}
```

#### GET /api/games/{gameId}/diplomacy/council
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

#### POST /api/games/{gameId}/diplomacy/council/vote
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

#### GET /api/games/{gameId}/ship-designs
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

#### POST /api/games/{gameId}/ship-designs
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

#### POST /api/games/{gameId}/ship-designs/{designId}/refit
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

#### GET /api/games/{gameId}/galaxy?page={n}&viewport={x1,y1,x2,y2}
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
    """
```

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
