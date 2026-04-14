# AGENT-BACKEND.md — MyMasterOfHostias: Backend Developer Instructions

---

## ROLE

You are the **Backend** developer agent for MyMasterOfHostias, a MOO2-faithful 4X space strategy game. You maintain the Flask REST API, game logic services, MongoDB interaction, turn processing, combat systems, and Docker deployment.

---

## TECH STACK

- **Framework**: Flask 3.x + Gunicorn (4 workers)
- **Language**: Python 3.11+
- **Database**: MongoDB 7 (pymongo, synchronous)
- **Auth**: JWT (PyJWT) + bcrypt password hashing
- **Containers**: Docker + Docker Compose v3.9
- **Config**: python-dotenv, env vars
- **AI Communication**: `requests` to call FastAPI AI service at `http://mmoh-ai-service:8000`

---

## ACTUAL PROJECT STRUCTURE

```
backend/
├── app/
│   ├── __init__.py              # Flask app factory, MongoDB setup, registers 12 blueprints
│   ├── models/                  # MongoDB document models (create/find/update/delete)
│   │   ├── user.py              # User: register, login, JWT auth
│   │   ├── game.py              # Game: CRUD, player/AI state, turn counter
│   │   ├── galaxy.py            # Galaxy: star generation, planets, wormholes, creatures
│   │   ├── colony.py            # Colony: population, buildings, build queue
│   │   ├── fleet.py             # Fleet: ships, transit state, ETA tracking
│   │   ├── ship.py              # ShipDesign: hull, weapons, specials, computed stats
│   │   ├── tech.py              # TechState: per-player research progress
│   │   ├── combat.py            # CombatLog: battle records
│   │   ├── diplomacy.py         # DiplomacyRelation: treaties, war state
│   │   └── leader.py            # Leader: hired leaders with traits
│   ├── routes/                  # API endpoints (12 Flask Blueprints)
│   │   ├── auth.py              # /api/auth/register, /api/auth/login + @require_auth decorator
│   │   ├── game.py              # /api/game/new, /<id>, /list, /<id>/end-turn, DELETE /<id>
│   │   ├── galaxy.py            # /api/game/<id>/galaxy, /galaxy/star/<idx>
│   │   ├── colony.py            # /api/game/<id>/colony (list, get, assign, build-queue)
│   │   ├── fleet.py             # /api/game/<id>/fleet (list, move, range, split, colonize)
│   │   ├── ship_design.py       # /api/game/<id>/ship-design (list, create)
│   │   ├── research.py          # /api/game/<id>/research (get, select)
│   │   ├── diplomacy.py         # /api/game/<id>/diplomacy (list, propose, accept, reject, cancel, war)
│   │   ├── combat.py            # /api/game/<id>/combat (auto, tactical/start, action, auto, state, log)
│   │   ├── espionage.py         # /api/game/<id>/espionage (list, recruit, mission)
│   │   ├── leaders.py           # /api/game/<id>/leaders (list, available, hire, assign, unassign)
│   │   └── cheat.py             # /api/game/<id>/cheat (apply, codes)
│   ├── services/                # Business logic (15 service modules)
│   │   ├── turn_engine.py       # Main turn orchestrator: economy→growth→builds→fleets→creatures→combat→Antarans→council→events→victory→AI
│   │   ├── colony_service.py    # MOO2-accurate formulas (FP/PP/RP/BC), 8 government types, GOV_EFFECTS
│   │   ├── research_service.py  # 148+ techs, 8 fields, breakthrough, miniaturization, future techs
│   │   ├── fleet_service.py     # Movement, ETA, range, wormholes, merge at star
│   │   ├── combat_service.py    # 5-round auto-resolve with shield/armor pipeline
│   │   ├── tactical_combat.py   # 12×12 grid tactical combat
│   │   ├── ground_combat.py     # 3-round ground invasion
│   │   ├── diplomacy_service.py # Treaties, personality modifiers, relation scoring
│   │   ├── espionage_service.py # 5 mission types, spy skill progression
│   │   ├── antaran_service.py   # Escalating attacks (fleet composition table by turn)
│   │   ├── creature_service.py  # 4 types (crystal/dragon/amoeba/guardian), placement, combat, rewards
│   │   ├── council_service.py   # Pop-weighted voting every 25 turns, 2/3 threshold
│   │   ├── event_service.py     # Random events with probability rolls
│   │   ├── leader_service.py    # Hire/assign/unassign, upkeep costs
│   │   └── __init__.py
│   └── data/                    # Static game data (9 JSON files)
│       ├── races.json           # 18 playable races with traits and bonuses
│       ├── tech_tree.json       # 148 techs across 8 fields + 8 exotic
│       ├── buildings.json       # 14 building types with costs and effects
│       ├── weapons.json         # 9 weapon types
│       ├── ship_hulls.json      # 6 combat hulls + colony_ship + transport
│       ├── leaders.json         # Leader templates with traits
│       ├── planet_types.json    # Planet habitability and attributes
│       ├── random_events.json   # Random event definitions
│       └── specials.json        # Ship special components
├── tests/
├── requirements.txt
├── Dockerfile
└── .env
```

---

## API ROUTES (40 endpoints across 12 blueprints)

**IMPORTANT**: The URL prefix is `/api/game/` (singular), NOT `/api/games/` (plural).

### Auth (`/api/auth`)
| Method | Route | Handler |
|--------|-------|---------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login, returns JWT |

### Game (`/api/game`)
| Method | Route | Handler |
|--------|-------|---------|
| POST | `/api/game/new` | Create game (race, AI races, galaxy size, difficulty) |
| GET | `/api/game/<id>` | Get game state |
| GET | `/api/game/list` | List user's games |
| DELETE | `/api/game/<id>` | Delete game (cascade) |
| POST | `/api/game/<id>/end-turn` | Process full turn + AI |

### Galaxy (`/api/game/<id>/galaxy`)
| Method | Route | Handler |
|--------|-------|---------|
| GET | `/galaxy` | Full galaxy (fog of war filtered) |
| GET | `/galaxy/star/<idx>` | Single star details |

### Colony (`/api/game/<id>/colony`)
| Method | Route | Handler |
|--------|-------|---------|
| GET | `/colony` | List player colonies |
| GET | `/colony/<cid>` | Get colony detail |
| POST | `/colony/<cid>/assign` | Set farmers/workers/scientists |
| POST | `/colony/<cid>/build-queue` | Set build queue |

### Fleet (`/api/game/<id>/fleet`)
| Method | Route | Handler |
|--------|-------|---------|
| GET | `/fleet` | List player fleets |
| POST | `/fleet/<fid>/move` | Move fleet to star |
| GET | `/fleet/range` | Get fleet range |
| POST | `/fleet/<fid>/split` | Split fleet (move ships to new fleet) |
| POST | `/fleet/<fid>/colonize` | Colonize planet |

### Ship Design (`/api/game/<id>/ship-design`)
| Method | Route | Handler |
|--------|-------|---------|
| GET | `/ship-design` | List designs |
| POST | `/ship-design` | Create new design |

### Research (`/api/game/<id>/research`)
| Method | Route | Handler |
|--------|-------|---------|
| GET | `/research` | Get tech state + available techs |
| POST | `/research/select` | Select research |

### Diplomacy (`/api/game/<id>/diplomacy`)
| Method | Route | Handler |
|--------|-------|---------|
| GET | `/diplomacy` | List relations |
| POST | `/diplomacy/propose` | Propose treaty |
| POST | `/diplomacy/accept` | Accept treaty |
| POST | `/diplomacy/reject` | Reject treaty |
| POST | `/diplomacy/cancel` | Cancel treaty |
| POST | `/diplomacy/war` | Declare war |

### Combat (`/api/game/<id>/combat`)
| Method | Route | Handler |
|--------|-------|---------|
| POST | `/combat/auto` | Auto-resolve combat |
| POST | `/combat/tactical/start` | Start tactical session |
| POST | `/combat/tactical/<sid>/action` | Submit tactical action |
| POST | `/combat/tactical/<sid>/auto` | Auto-resolve tactical |
| GET | `/combat/tactical/<sid>/state` | Get tactical state |
| GET | `/combat/log` | Get combat logs |

### Espionage (`/api/game/<id>/espionage`)
| Method | Route | Handler |
|--------|-------|---------|
| GET | `/espionage` | List spies |
| POST | `/espionage/recruit` | Recruit spy |
| POST | `/espionage/mission` | Assign mission |

### Leaders (`/api/game/<id>/leaders`)
| Method | Route | Handler |
|--------|-------|---------|
| GET | `/leaders` | List hired leaders |
| GET | `/leaders/available` | Available templates |
| POST | `/leaders/hire` | Hire leader |
| POST | `/leaders/<lid>/assign` | Assign to target |
| POST | `/leaders/<lid>/unassign` | Unassign |

### Cheat (`/api/game/<id>/cheat`)
| Method | Route | Handler |
|--------|-------|---------|
| POST | `/cheat` | Apply cheat code |
| GET | `/cheat/codes` | List available codes |

---

## TURN ENGINE FLOW (`turn_engine.py`)

```
end_turn(game_id) → dict {turn, events, combat_results, ai_actions}
  │
  ├─ For each player (player + alive AIs):
  │   ├─ Process colonies: morale → food → pop growth → production → build queue → research → BC
  │   ├─ Process empire research (breakthrough check)
  │   ├─ Update empire BC
  │   └─ Update diplomacy relations
  │
  ├─ Advance fleets (reduce ETA, handle arrivals)
  ├─ Explore stars on arrival
  ├─ Creature combat at arrival
  ├─ Fleet-vs-fleet combat resolution
  ├─ Antaran attack check (escalating by turn)
  ├─ Council vote check (every 25 turns)
  ├─ Random events
  ├─ Victory/defeat check
  ├─ AI turns (_execute_ai_turns → calls AI service)
  └─ Increment turn
```

---

## AI SERVICE INTEGRATION

The backend calls the AI service (FastAPI, separate container) via HTTP:

```python
# In turn_engine.py → _execute_ai_turns()
POST http://mmoh-ai-service:8000/ai/turn
Body: {game_id, ai_player_id, personality, difficulty, state}
Response: {actions: [...]}
```

`_prepare_ai_state()` filters galaxy to only visible stars (fog of war).
`_validate_and_execute_ai_action()` validates and executes each AI action.

---

## KEY CONVENTIONS

1. **All API paths use `/api/game/` (singular)** — not `/api/games/`
2. **Auth**: `@require_auth` decorator sets `g.user_id` from JWT
3. **ObjectId handling**: Always convert to `str()` before returning JSON
4. **Fog of war**: `_prepare_ai_state()` and galaxy routes filter by `explored_by` list
5. **MOO2-accurate formulas**: All in `colony_service.py` with GOV_EFFECTS dict for 8 government types
6. **Tech tree**: 148+ regular techs + 8 exotic, field-dependent future tech costs
7. **Events**: Every sub-phase appends typed event dicts to the `events` list
8. **CORS**: Configured in `__init__.py` via flask-cors
9. **Secrets**: JWT_SECRET, MONGO_URI from env vars — never hardcoded

---

## CHECKLIST

- [x] Register/Login with JWT
- [x] Game CRUD (create, load, list, delete)
- [x] Galaxy generation with stars, planets, wormholes, creatures
- [x] Colony management (population, buildings, build queue)
- [x] Research with 148+ techs, breakthrough, miniaturization
- [x] Fleet movement with ETA tracking
- [x] Colonization (colony ship consumed)
- [x] Auto-combat (5-round with shields/armor)
- [x] Tactical combat (12×12 grid)
- [x] Ground invasion (3-round)
- [x] AI turn via AI service (fog of war, validate actions)
- [x] Fog of war (explored_by tracking)
- [x] Cheat system (13 codes: 11 original + RUSHBUY + CRUNCH)
- [x] Antaran attacks (escalating)
- [x] Space creatures (4 types + rewards)
- [x] Galactic Council (pop-weighted voting)
- [x] Diplomacy (treaties, war, personality)
- [x] Espionage (5 mission types)
- [x] Leaders (hire, assign, upkeep)
- [x] Ship designer (6 hulls)
- [x] Victory/defeat detection
- [x] Docker deployment (4 containers)
- [x] CORS configured
- [x] Fleet split endpoint (POST /fleet/{id}/split)
- [x] Planet max_pop enrichment in galaxy route (derived from size)
- [x] Ships auto-assigned to fleet on build completion
