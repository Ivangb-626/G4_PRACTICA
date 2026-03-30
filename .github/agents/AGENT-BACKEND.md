# AGENT-BACKEND.md — MasterDeHostias: Instrucciones para Copilot Agent (Backend Developer)

---

## ROL

Eres el agente de desarrollo **Backend** para el proyecto MasterDeHostias, un juego web de estrategia 4X espacial por turnos. Tu responsabilidad principal es implementar la API REST, la lógica del juego, la interacción con MongoDB, la mecánica de turnos, el sistema de combate, y la configuración de deployment con Docker.

---

## TECNOLOGÍAS

- **Framework**: Consulta la tabla de asignación en MasterDeHostias_practica.md § 4.1 para saber si usas Flask o FastAPI
- **Lenguaje**: Python 3.11+
- **Base de datos**: MongoDB (pymongo o motor para async)
- **Auth**: JWT (PyJWT), bcrypt para hashing de passwords
- **Contenedores**: Docker, Docker Compose
- **Variables de entorno**: python-dotenv
- **Validación**: pydantic (FastAPI nativo) o marshmallow/cerberus (Flask)

---

## ARQUITECTURA BACKEND

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                # Entry point (FastAPI app o Flask app)
│   ├── config.py              # Configuración y variables de entorno
│   ├── models/                # Modelos de datos (pydantic/dataclass)
│   │   ├── user.py
│   │   ├── game.py
│   │   ├── colony.py
│   │   ├── fleet.py
│   │   ├── technology.py
│   │   └── combat.py
│   ├── routes/                # Endpoints de la API
│   │   ├── auth.py            # /api/auth/*
│   │   ├── games.py           # /api/games/*
│   │   ├── colony.py          # /api/games/{id}/colony/*
│   │   ├── research.py        # /api/games/{id}/research
│   │   ├── fleet.py           # /api/games/{id}/fleet/*
│   │   ├── combat.py          # /api/games/{id}/combat/*
│   │   └── cheat.py           # /api/games/{id}/cheat
│   ├── services/              # Lógica de negocio
│   │   ├── game_service.py    # Orquestación de turnos
│   │   ├── colony_service.py  # Lógica de colonias
│   │   ├── combat_service.py  # Resolución de combates
│   │   ├── research_service.py # Lógica de investigación
│   │   ├── fleet_service.py   # Movimiento de flotas
│   │   ├── galaxy_service.py  # Generación de galaxias
│   │   ├── economy_service.py # Cálculos económicos
│   │   └── cheat_service.py   # Lógica de cheats
│   ├── db/                    # Interacción con MongoDB
│   │   ├── database.py        # Conexión a MongoDB
│   │   ├── user_repo.py
│   │   └── game_repo.py
│   ├── auth/                  # Autenticación
│   │   ├── jwt_handler.py     # Crear y verificar JWT tokens
│   │   └── password.py        # Hash y verify con bcrypt
│   ├── data/                  # Datos estáticos del juego
│   │   ├── races.json         # Definición de las 3 razas asignadas al grupo
│   │   ├── buildings.json     # Definición de edificios
│   │   ├── technologies.json  # Árbol tecnológico completo
│   │   └── ships.json         # Tipos de naves
│   └── middleware/            # Middleware (CORS, auth, logging)
├── tests/
├── requirements.txt
├── Dockerfile
└── .env
```

---

## ENDPOINTS — RESUMEN

Consultar SPECS.md § 2 para detalles completos. Aquí el resumen:

### Auth (`/api/auth/`)
| Método | Ruta | Función |
|--------|------|---------|
| POST | `/api/auth/register` | Registrar usuario |
| POST | `/api/auth/login` | Login, devolver JWT |
| GET | `/api/auth/profile` | Perfil del usuario autenticado |

### Games (`/api/games/`)
| Método | Ruta | Función |
|--------|------|---------|
| GET | `/api/games` | Listar partidas del usuario |
| POST | `/api/games` | Crear nueva partida |
| GET | `/api/games/{gameId}` | Cargar partida |
| POST | `/api/games/{gameId}/save` | Guardar partida |
| DELETE | `/api/games/{gameId}` | Eliminar partida |

### Acciones en partida
| Método | Ruta | Función |
|--------|------|---------|
| POST | `/api/games/{gameId}/colony/{colonyId}/manage` | Gestionar colonia |
| POST | `/api/games/{gameId}/research` | Seleccionar investigación |
| POST | `/api/games/{gameId}/fleet/{fleetId}/move` | Mover flota |
| POST | `/api/games/{gameId}/colonize` | Colonizar planeta |
| POST | `/api/games/{gameId}/endTurn` | Fin de turno + turno IA |
| POST | `/api/games/{gameId}/cheat` | Aplicar cheat |

### Consultas
| Método | Ruta | Función |
|--------|------|---------|
| GET | `/api/games/{gameId}/galaxy` | Mapa galáctico (con fog of war) |
| GET | `/api/games/{gameId}/tech-tree` | Árbol tecnológico |
| GET | `/api/games/{gameId}/colony/{colonyId}` | Detalle de colonia |
| GET | `/api/scenarios` | Escenarios disponibles |

---

## LÓGICA DEL JUEGO — QUÉ IMPLEMENTAR

### 1. Generación de Galaxia (`galaxy_service.py`)

```python
def generate_galaxy(size: str, num_opponents: int, player_race_id: str) -> dict:
    """
    1. Generar N sistemas estelares con posiciones aleatorias (20-30 para small)
    2. Asignar tipo de estrella (red, orange, yellow, white, blue)
    3. Generar planetas por sistema (1-5, influenciados por tipo de estrella)
    4. Conectar sistemas (cada sistema con 2-4 conexiones, grafo conexo)
    5. Colocar sistema Orion con Guardián (planeta Gaia ultra-rich)
    6. Asignar planetas natales: jugador y cada IA lo más lejos posible entre sí
    7. Cada planeta natal es Terran, Large, Abundant, Normal gravity
    8. Inicializar fog of war: solo sistema natal visible
    """
```

### 2. Gestión de Turnos (`game_service.py`)

```python
def end_turn(game_id: str) -> dict:
    """
    Secuencia de fin de turno del jugador:
    1. Resolver combates pendientes (flotas enemigas en mismo sistema)
    2. Procesar colas de construcción (aplicar producción a primer elemento)
    3. Actualizar recursos (BC, comida, producción, investigación)
    4. Crecimiento de población en colonias con excedente de comida
    5. Pérdida de población en colonias con déficit de comida
    6. Progreso de investigación (acumular puntos, completar si suficiente)
    7. Mover flotas en tránsito (reducir ETA, resolver llegadas)
    8. Actualizar fog of war
    9. Verificar condiciones de victoria/derrota
    9.5. Verificar ataque Antarano: si turn >= antaran_next_attack_turn,
         generar flota según escalada (ver SPECS.md § 3.11), seleccionar colonia
         aleatoria, auto-resolver combate, bombardear si no hay defensas,
         otorgar recompensa si defensor gana, programar siguiente ataque.
    10. Autoguardar
    11. Ejecutar turno de IA (llamar al servicio de IA)
    12. Resolver combates de la IA
    13. Incrementar turno
    14. Devolver estado actualizado + acciones de IA para visualización
    """
```

> **Eventos**: Cada sub-fase (economía, combate, investigación, crecimiento, construcción, Antaranos) debe generar objetos de evento y agregarlos al array `events` de la respuesta. Ver SPECS.md § 2.3 para el enum de tipos de evento.
```

### 3. Economía de Colonia (`economy_service.py`)

Implementar las fórmulas exactas de SPECS.md § 3.1-3.4:

- **Comida**: food_per_farmer × farmers - total_pop (con modificadores de planeta y raza)
- **Producción**: workers × 2 × minerals_mod + building_bonuses + race_bonuses
- **Investigación**: scientists × 2 + building_bonuses + (total × race.research_bonus/100)
- **BC**: building_bc + (trade_bonus × pop) - maintenance
- **Crecimiento**: base_rate × race_mod × (1 - pop/max_pop)
- **Moral**: gobierno + conquista + sobrepoblación + edificios

### 4. Colonización (`colony_service.py`)

```python
def colonize_planet(game_state: dict, fleet_id: str, planet_index: int) -> dict:
    """
    1. Verificar flota contiene colony_ship
    2. Verificar planeta no colonizado
    3. Verificar planeta colonizable (habitable, o tech permite tóxico/estéril)
    4. Consumir colony_ship de la flota
    5. Crear colonia con 1 de población (1 farmer)
    6. Retornar colonia nueva y flota actualizada
    """
```

### 5. Investigación (`research_service.py`)

```python
def select_research(game_state: dict, field: str, level: int, tech_id: str) -> dict:
    """
    1. Verificar nivel anterior completado en este campo
    2. Verificar tech_id es opción válida para este nivel/campo
    3. Verificar tech no descartada previamente
    4. Establecer como investigación actual
    5. Si ya había investigación en curso en otro campo, el progreso se pierde
    """

def apply_research_progress(game_state: dict) -> dict:
    """
    1. Sumar total_empire_research a current_research.progress
    2. Si progress >= total_cost:
       - Marcar tech como researched
       - Aplicar efectos (desbloquear edificios, componentes, etc.)
       - Marcar otras opciones del mismo nivel como discarded
       - Limpiar current_research
    """
```

### 6. Movimiento de Flotas (`fleet_service.py`)

```python
def move_fleet(game_state: dict, fleet_id: str, destination: str) -> dict:
    """
    1. Verificar flota pertenece al jugador
    2. Verificar destino es sistema conectado o alcanzable
    3. Verificar flota no está ya en tránsito
    4. Calcular ETA: ceil(distance / min_ship_speed)
    5. Actualizar flota con destino y ETA
    """

def process_fleet_movements(game_state: dict) -> list:
    """
    Para cada flota en tránsito:
    1. Reducir eta_turns en 1
    2. Si eta_turns == 0:
       - Mover flota al destino
       - Revelar sistema en fog of war
       - Si hay flota enemiga: marcar combate pendiente
       - Limpiar destino y ETA
    Retornar lista de eventos (llegada, combate, exploración)
    """
```

### 7. Combate Automático (`combat_service.py`)

Implementar exactamente las fórmulas de SPECS.md § 3.6:

```python
def resolve_combat(attacker_fleet: dict, defender_fleet: dict, 
                   defender_orbital_defense: int = 0) -> dict:
    """
    1. Calcular fuerza de ataque y defensa
    2. Simular 5 rondas de combate
    3. Cada ronda: daño proporcional con factor aleatorio (0.8-1.2) - escudos
    4. Eliminar naves empezando por las más débiles
    5. Determinar ganador
    6. Retornar resultado con bajas por bando
    """

def resolve_ground_combat(num_transports: int, race_bonus_attacker: int,
                          colony: dict, race_bonus_defender: int) -> dict:
    """
    Implementar fórmula de SPECS.md § 3.7
    """
```

### 8. Cheats (`cheat_service.py`)

```python
def apply_cheat(game_state: dict, cheat_code: str, target: dict = None) -> dict:
    """
    Implementar cada cheat código de SPECS.md § 2.3 (POST /cheat).
    Registrar cheat aplicado en game_state.cheats_used.
    Loguear en server para debug.
    """
```

### 9. Fog of War

```python
def get_visible_systems(game_state: dict, player_id: str) -> list[str]:
    """
    Un sistema es visible si:
    - El jugador tiene colonia en ese sistema
    - El jugador tiene flota en ese sistema
    - El sistema es adyacente a un sistema con colonia del jugador
    - Scanner techs extienden el rango
    Retornar lista de system_ids visibles.
    """

def filter_galaxy_for_player(galaxy: dict, visible_systems: list[str]) -> dict:
    """
    Para sistemas no visibles: ocultar planetas, flotas enemigas, colonias enemigas.
    Solo incluir: id, name, position, connections, explored (si fue explorado alguna vez).
    """
```

---

## AUTENTICACIÓN

### JWT

```python
# auth/jwt_handler.py
import jwt
from datetime import datetime, timedelta

SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"
EXPIRATION_HOURS = 24

def create_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(hours=EXPIRATION_HOURS),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
```

### Password Hashing

```python
# auth/password.py
import bcrypt

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())
```

### Middleware de Autenticación

Cada endpoint protegido debe:
1. Extraer token del header `Authorization: Bearer <token>`
2. Verificar token con `verify_token()`
3. Extraer `user_id` del payload
4. Inyectar user_id en el handler

---

## INTEGRACIÓN CON SERVICIO DE IA

El backend se comunica con el servicio de IA (contenedor separado) vía HTTP:

```python
async def get_ai_decisions(game_state: dict, ai_player_id: str) -> list[dict]:
    """
    1. Preparar estado visible para la IA (fog of war)
    2. Llamar a servicio de IA: POST http://ai-service:8001/api/ai/turn
    3. Recibir lista de acciones en JSON
    4. Validar cada acción contra las reglas del juego
    5. Descartar acciones inválidas
    6. Ejecutar acciones válidas en orden
    7. Registrar acciones para visualización en frontend
    """
```

**Endpoint que llama al servicio de IA:**
```
POST http://ai-service:8001/api/ai/turn
Body: {
    "game_state": <estado visible>,
    "ai_player": <datos del jugador IA>,
    "personality": <personalidad>,
    "difficulty": <dificultad>
}
Response: {
    "actions": [...],
    "reasoning": "...",
    "analysis": "..."
}
```

---

## MONGODB — COLECCIONES

### users
```python
# Esquema
{
    "_id": ObjectId,
    "username": str,        # unique index
    "email": str,           # unique index
    "password_hash": str,
    "created_at": datetime,
    "last_login": datetime,
    "games_played": int,
    "games_won": int
}
```

### games
```python
# Esquema
{
    "_id": ObjectId,
    "user_id": ObjectId,    # index
    "name": str,
    "scenario_id": str,
    "created_at": datetime,
    "last_saved": datetime,
    "is_autosave": bool,
    "game_state": dict      # GameState completo embebido
}
```

### Índices recomendados:
```python
db.users.create_index("username", unique=True)
db.users.create_index("email", unique=True)
db.games.create_index("user_id")
db.games.create_index([("user_id", 1), ("last_saved", -1)])
```

---

## DATOS ESTÁTICOS DEL JUEGO

Crear JSONs de referencia en `app/data/`:

### races.json
Contiene las 3 razas asignadas al grupo con todos sus atributos (ver SPECS.md § 1.2 y MasterDeHostias_practica.md § 2 para la asignación grupo→razas).

### buildings.json
Contiene los 8 edificios core con costes, mantenimiento, efectos y prerequisitos (ver SPECS.md § 1.6).

### technologies.json
Contiene los 24+ tecnologías (8 campos × 3 niveles) con costes, opciones y desbloqueos (ver SPECS.md § 1.7).

### ships.json
Contiene los 6 tipos de nave con stats base (ver SPECS.md § 1.8).

---

## MÓDULO ESPECÍFICO DEL GRUPO

Consultar SPECS.md § 6 para los requisitos del módulo asignado. El backend debe implementar la lógica correspondiente:

| Grupo | Módulo | Backend adicional |
|-------|--------|-------------------|
| 1 | Combate Táctico | Motor de combate por cuadrícula, pathfinding, cálculo de daño por tipo de arma |
| 2 | Espionaje | Reclutamiento, misiones, probabilidades, efectos sobre estado del juego |
| 3 | Constructor Razas | Validación de picks, aplicación de rasgos en toda la lógica |
| 4 | Diplomacia | Tratados, relaciones numéricas, Consejo Galáctico, personalidades |
| 5 | Diseño Naves | Validación de diseños, miniaturización, reequipamiento |
| 6 | Galaxia Grande | Generación de galaxias grandes, multi-IA, optimización de queries |

---

## DOCKER

### Dockerfile del backend
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# FastAPI:
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Flask:
# CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app.main:app"]
```

### requirements.txt (FastAPI)
```
fastapi>=0.104.0
uvicorn>=0.24.0
pymongo>=4.6.0
motor>=3.3.0
pydantic>=2.5.0
PyJWT>=2.8.0
bcrypt>=4.1.0
python-dotenv>=1.0.0
httpx>=0.25.0
```

### requirements.txt (Flask)
```
flask>=3.0.0
gunicorn>=21.2.0
pymongo>=4.6.0
marshmallow>=3.20.0
flask-cors>=4.0.0
PyJWT>=2.8.0
bcrypt>=4.1.0
python-dotenv>=1.0.0
requests>=2.31.0
```

---

## REGLAS DE DESARROLLO

1. **Consulta SPECS.md** antes de implementar cualquier endpoint o lógica
2. **Validación de input** en TODOS los endpoints (tipos, rangos, pertenencia del recurso)
3. **Autorización**: Verificar que el recurso pertenece al usuario autenticado
4. **Fog of War**: NUNCA exponer información que el jugador no debería ver
5. **Fórmulas exactas**: Usar las fórmulas de SPECS.md § 3 para cálculos de juego
6. **Error handling**: Devolver códigos HTTP apropiados (400, 401, 403, 404, 500)
7. **Logging**: Loguear acciones de la IA y cheats para debug
8. **Secretos**: NUNCA hardcodear tokens o passwords — usar variables de entorno
9. **Transacciones**: Las operaciones de fin de turno deben ser atómicas (si falla algo, rollback)
10. **CORS**: Configurar para permitir requests del frontend

---

## CHECKLIST ANTES DE ENTREGAR

- [ ] Registro/Login con JWT funcional
- [ ] CRUD de partidas (crear, cargar, guardar, eliminar)
- [ ] Generación de galaxia con estrellas, planetas y conexiones
- [ ] Gestión de colonias (población, construcción)
- [ ] Investigación tecnológica con progreso y desbloqueos
- [ ] Movimiento de flotas entre sistemas
- [ ] Colonización de planetas
- [ ] Combate automático con bajas
- [ ] Invasión terrestre
- [ ] Turno de IA integrado (llamada al servicio de IA)
- [ ] Fog of war funcional
- [ ] Sistema de cheats completo
- [ ] Condiciones de victoria/derrota
- [ ] Autoguardado al final de cada turno
- [ ] Todos los endpoints devuelven errores apropiados
- [ ] Módulo específico del grupo implementado
- [ ] Dockerfile funcional
- [ ] Docker Compose con los 4 contenedores
- [ ] CORS configurado para el frontend
