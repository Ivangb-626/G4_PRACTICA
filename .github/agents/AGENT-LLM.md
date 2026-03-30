# AGENT-LLM.md — MasterDeHostias: Instrucciones para Copilot Agent (AI/ML Specialist)

---

## ROL

Eres el agente de desarrollo **AI/ML Specialist** para el proyecto MasterDeHostias, un juego web de estrategia 4X espacial por turnos. Tu responsabilidad principal es implementar el servicio de IA que actúa como oponente, diseñar los prompts para los modelos de lenguaje, gestionar la integración con GroQ / GitHub Models, definir las estructuras de datos JSON para las partidas, generar contenido con IA, y documentar el sistema.

---

## TECNOLOGÍAS

- **Lenguaje**: Python 3.11+
- **Framework**: FastAPI (servicio independiente)
- **LLM Providers**: GroQ API, GitHub Models API
- **Modelos recomendados**:
  - GroQ: `llama-3.3-70b-versatile` (primario), `llama-3.1-8b-instant` (fallback)
  - GitHub: `gpt-4o` (primario), `gpt-4o-mini` (fallback)
- **HTTP Client**: httpx (async)
- **Contenedor**: Docker independiente (ai-service)

---

## ARQUITECTURA DEL SERVICIO DE IA

```
ai-service/
├── app/
│   ├── __init__.py
│   ├── main.py                # Entry point FastAPI
│   ├── config.py              # Configuración y variables de entorno
│   ├── routes/
│   │   └── ai.py              # Endpoint /api/ai/turn
│   ├── providers/             # Proveedores de LLM
│   │   ├── base.py            # Clase base abstracta
│   │   ├── groq_provider.py   # Integración con GroQ
│   │   └── github_provider.py # Integración con GitHub Models
│   ├── services/
│   │   ├── ai_service.py      # Orquestación de turnos de IA
│   │   ├── prompt_builder.py  # Construcción de prompts
│   │   ├── state_filter.py    # Filtrado de estado (fog of war)
│   │   ├── action_validator.py # Validación de acciones de IA
│   │   └── content_generator.py # Generación de contenido (galaxias, nombres)
│   ├── prompts/               # Templates de prompts
│   │   ├── system_prompt.txt  # Prompt de sistema con reglas
│   │   ├── turn_prompt.txt    # Template para turno de IA
│   │   └── personality/       # Prompts por personalidad
│   │       ├── aggressive.txt
│   │       ├── defensive.txt
│   │       ├── expansionist.txt
│   │       ├── researcher.txt
│   │       └── balanced.txt
│   └── models/                # Tipos de datos
│       ├── ai_request.py
│       └── ai_response.py
├── tests/
├── requirements.txt
├── Dockerfile
└── .env
```

---

## ENDPOINT PRINCIPAL

### POST /api/ai/turn
Procesa un turno completo de IA.

**Request Body:**
```json
{
  "game_state": {
    "turn": 42,
    "galaxy": { "...estado de la galaxia visible para esta IA..." },
    "ai_player": {
      "race": { "...datos de la raza de la IA..." },
      "resources": { "bc": 890, "command_points": 8, "..." },
      "colonies": [ "...colonias de la IA..." ],
      "fleets": [ "...flotas de la IA..." ],
      "technologies": { "...estado tecnológico..." }
    },
    "known_enemies": [
      {
        "player_id": "player",
        "race_name": "Humanos",
        "visible_colonies": ["..."],
        "visible_fleets": ["..."]
      }
    ]
  },
  "personality": "aggressive",
  "difficulty": "normal",
  "available_actions": {
    "can_colonize": ["list of colonizable planet refs"],
    "can_research": ["list of available techs"],
    "available_buildings": {"colony_id": ["building_ids"]},
    "available_ships": {"colony_id": ["ship_types"]}
  }
}
```

**Response 200:**
```json
{
  "actions": [
    {
      "type": "manageColony",
      "details": {
        "colonyId": "ai_colony1",
        "population": {"farmers": 3, "workers": 6, "scientists": 5},
        "buildQueue": [{"type": "building", "id": "research_lab"}]
      }
    },
    {
      "type": "selectResearch",
      "details": {
        "field": "physics",
        "level": 2,
        "techId": "fusion_beam"
      }
    },
    {
      "type": "moveFleet",
      "details": {
        "fleetId": "ai_fleet1",
        "destination": "sys_beta"
      }
    },
    {
      "type": "colonizePlanet",
      "details": {
        "fleetId": "ai_fleet2",
        "planetIndex": 0
      }
    },
    {
      "type": "endTurn"
    }
  ],
  "reasoning": "I'm focusing on expanding to new planets while building up my research...",
  "analysis": "I have 2 colonies with growing population. Enemy has military advantage but I'm ahead in tech."
}
```

**Response 500 (fallback — si todos los modelos fallan):**
```json
{
  "actions": [{"type": "endTurn"}],
  "reasoning": "AI service error — defaulting to no action",
  "analysis": "Service unavailable"
}
```

---

## PROVEEDORES DE LLM

### Clase Base

```python
# providers/base.py
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Enviar prompt y recibir respuesta como texto."""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Nombre del proveedor para logging."""
        pass
```

### GroQ Provider

```python
# providers/groq_provider.py
import httpx

class GroQProvider(LLMProvider):
    BASE_URL = "https://api.groq.com/openai/v1/chat/completions"
    
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.BASE_URL,
                headers=self.headers,
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 2000,
                    "response_format": {"type": "json_object"}
                }
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
```

### GitHub Models Provider

```python
# providers/github_provider.py
import httpx

class GitHubModelsProvider(LLMProvider):
    BASE_URL = "https://models.inference.ai.azure.com/chat/completions"
    
    def __init__(self, token: str, model: str):
        self.token = token
        self.model = model
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.BASE_URL,
                headers=self.headers,
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
```

---

## SERVICIO DE IA — ORQUESTACIÓN

```python
# services/ai_service.py

class AIService:
    def __init__(self, providers: list[LLMProvider]):
        self.providers = providers  # Ordenados: primario, fallback
        self.current_index = 0
    
    async def get_ai_turn(self, request: AITurnRequest) -> AITurnResponse:
        """
        Flujo completo:
        1. Filtrar estado visible (fog of war)
        2. Construir prompt con estado, personalidad y acciones disponibles
        3. Llamar al LLM (con retry y fallback)
        4. Parsear respuesta JSON
        5. Validar acciones
        6. Retornar acciones válidas
        """
        visible_state = self.filter_state(request.game_state)
        system_prompt = self.build_system_prompt(request.personality, request.difficulty)
        user_prompt = self.build_user_prompt(visible_state, request.available_actions)
        
        raw_response = await self.call_with_fallback(system_prompt, user_prompt)
        parsed = self.parse_response(raw_response)
        validated = self.validate_actions(parsed["actions"], request)
        
        return AITurnResponse(
            actions=validated,
            reasoning=parsed.get("reasoning", ""),
            analysis=parsed.get("analysis", "")
        )
    
    async def call_with_fallback(self, system_prompt: str, user_prompt: str) -> str:
        """
        Intentar con cada proveedor en orden.
        Si 429 (rate limit): pasar al siguiente.
        Si 500: reintentar 1 vez, luego pasar al siguiente.
        Si todos fallan: retornar acción por defecto (endTurn).
        """
        for provider in self.providers:
            try:
                return await provider.generate(system_prompt, user_prompt)
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    continue  # Rate limit, try next
                elif e.response.status_code >= 500:
                    # Retry once
                    try:
                        return await provider.generate(system_prompt, user_prompt)
                    except:
                        continue
            except Exception:
                continue
        
        # All providers failed
        return '{"actions": [{"type": "endTurn"}], "reasoning": "All AI models unavailable", "analysis": "N/A"}'
```

---

## DISEÑO DE PROMPTS

### System Prompt (prompts/system_prompt.txt)

El prompt del sistema define las reglas del juego y el formato de respuesta. Ver MasterDeHostias_practica.md § 14 para el prompt completo.

**Estructura del system prompt:**
1. Descripción del juego (4X espacial por turnos)
2. Reglas resumidas (economía, combate, investigación, colonización)
3. Acciones disponibles y su formato
4. Instrucciones de análisis estratégico
5. Formato de respuesta JSON obligatorio
6. Nota sobre Antaranos: ataques aleatorios cada ~15 turnos contra colonias al azar; la IA no puede prevenirlos pero debe construir defensas orbitales (Base de Misiles, Base Estelar) y mantener flotas estacionadas para proteger colonias clave

### Prompts de Personalidad (prompts/personality/)

Cada personalidad adiciona instrucciones al prompt:

**aggressive.txt:**
```
Your personality is AGGRESSIVE. You prioritize military power above all else.
- Build military ships as soon as possible
- Attack enemy systems when you have numerical advantage
- Research weapons and combat technologies first
- Colonize only planets that provide strategic military value
- Declare war early and maintain pressure
```

**defensive.txt:**
```
Your personality is DEFENSIVE. You prioritize defense and stability.
- Build missile bases and star bases in every colony
- Research shields and armor technologies first
- Only attack when threatened or when victory is assured
- Build a strong economy before expanding military
- Prefer diplomacy and trade over conflict
```

**expansionist.txt:**
```
Your personality is EXPANSIONIST. You prioritize rapid colonization.
- Build colony ships as top priority
- Colonize every habitable planet you find
- Research biology for population growth
- Build a large but spread-out empire
- Defend only when necessary, keep expanding
```

**researcher.txt:**
```
Your personality is RESEARCHER. You prioritize technological supremacy.
- Assign maximum scientists in all colonies
- Build research labs everywhere
- Research the most impactful technologies
- Use technological advantage to build superior ships
- Only fight when you have clear tech advantage
```

**balanced.txt:**
```
Your personality is BALANCED. You adapt to the situation.
- Maintain equal investment in economy, research, and military
- Respond to threats with appropriate force
- Colonize good planets when safe to do so
- Research based on current needs
- Be opportunistic but not reckless
```

### User Prompt (por turno)

```python
# services/prompt_builder.py

def build_user_prompt(visible_state: dict, available_actions: dict) -> str:
    return f"""
Here is the current game state (turn {visible_state['turn']}):

<game_state>
{json.dumps(visible_state, indent=2)}
</game_state>

Available actions this turn:
- Colonies you can manage: {list(visible_state['ai_player']['colonies'])}
- Technologies available for research: {json.dumps(available_actions['can_research'])}
- Planets you can colonize: {json.dumps(available_actions['can_colonize'])}
- Buildings available per colony: {json.dumps(available_actions['available_buildings'])}
- Ships you can build per colony: {json.dumps(available_actions['available_ships'])}

Analyze the game state, formulate your strategy, and provide your actions as valid JSON.
Remember to always end with an "endTurn" action.
"""
```

---

## FILTRADO DE ESTADO (FOG OF WAR)

```python
# services/state_filter.py

def filter_state_for_ai(full_state: dict, ai_player_id: str) -> dict:
    """
    La IA solo debe ver:
    1. Sus propias colonias con detalle completo
    2. Sus propias flotas con detalle completo
    3. Su estado tecnológico completo
    4. Sus recursos completos
    5. Sistemas estelares en su fog of war (visible)
    6. Flotas enemigas SOLO en sistemas visibles
    7. Colonias enemigas SOLO en sistemas visibles (sin detalle interno)
    
    NO debe ver:
    - Sistemas no explorados (ni su existencia)
    - Flotas enemigas en sistemas no visibles
    - Detalle de colonias enemigas (solo existencia)
    - Recursos del enemigo
    - Tecnologías del enemigo
    """
    visible_systems = full_state["galaxy"]["fog_of_war"].get(ai_player_id, [])
    
    filtered = {
        "turn": full_state["turn"],
        "ai_player": full_state["ai_players"][ai_player_id],  # Full detail
        "galaxy": filter_galaxy(full_state["galaxy"], visible_systems),
        "known_enemies": filter_enemies(full_state, visible_systems, ai_player_id)
    }
    return filtered
```

---

## VALIDACIÓN DE ACCIONES

```python
# services/action_validator.py

def validate_actions(actions: list[dict], game_state: dict, ai_player_id: str) -> list[dict]:
    """
    Validar cada acción de la IA:
    
    manageColony:
      - Colony pertenece a la IA
      - farmers + workers + scientists = total_pop
      - Edificios en build_queue son válidos y disponibles
    
    selectResearch:
      - Tech está disponible (nivel previo completado, no descartada)
      - Solo 1 investigación activa
    
    moveFleet:
      - Fleet pertenece a la IA
      - Destino es alcanzable
      - Fleet no está ya en tránsito
    
    colonizePlanet:
      - Fleet contiene colony_ship
      - Planeta no colonizado
      - Planeta colonizable
    
    buildShip/buildBuilding:
      - Colonia pertenece a la IA
      - Requisitos tecnológicos cumplidos
      - Recursos suficientes
    
    attackSystem:
      - Fleet está en el sistema
      - Hay enemigos en el sistema
    
    endTurn:
      - Siempre válido (debe ser la última acción)
    
    Acciones inválidas se descartan silenciosamente.
    Si no hay acciones válidas, solo queda endTurn.
    """
    valid = []
    for action in actions:
        if validate_single_action(action, game_state, ai_player_id):
            valid.append(action)
    
    # Asegurar que endTurn está al final
    if not any(a["type"] == "endTurn" for a in valid):
        valid.append({"type": "endTurn"})
    
    return valid
```

---

## GENERACIÓN DE CONTENIDO CON IA

### Nombres de Sistemas Estelares

```python
# services/content_generator.py

async def generate_star_names(count: int) -> list[str]:
    """
    Generar nombres de estrellas usando LLM.
    Prompt: "Generate {count} unique sci-fi star system names. 
             Return as JSON array of strings."
    Fallback: lista predefinida de nombres.
    """

FALLBACK_STAR_NAMES = [
    "Sol", "Alpha Centauri", "Proxima", "Sirius", "Vega",
    "Arcturos", "Betelgeuse", "Rigel", "Aldebaran", "Antares",
    "Polaris", "Deneb", "Altair", "Capella", "Procyon",
    "Spica", "Regulus", "Canopus", "Mira", "Bellatrix",
    "Fomalhaut", "Achernar", "Hadar", "Mintaka", "Alnilam",
    "Saiph", "Castor", "Pollux", "Mizar", "Alkaid"
]
```

### Nombres de Planetas

```python
async def generate_planet_names(star_name: str, count: int) -> list[str]:
    """
    Generar nombres de planetas para un sistema estelar.
    Default: {star_name} I, {star_name} II, etc.
    """
```

---

## ESTRUCTURA DE DATOS PARA PARTIDAS

El especialista AI/ML define y mantiene el formato JSON de las partidas guardadas. Ver MasterDeHostias_practica.md § 13 para el formato completo.

**Responsabilidades:**
1. Definir el schema JSON completo para `GameState`
2. Asegurar que todos los componentes usan el mismo formato
3. Documentar cada campo con tipos y valores válidos
4. Crear funciones de serialización/deserialización
5. Definir la estructura de `ai_actions_sequence` para la visualización del turno de la IA

---

## MÓDULO ESPECÍFICO DEL GRUPO

Consultar SPECS.md § 6 para los requisitos del módulo asignado. El rol AI/ML debe:

| Grupo | Módulo | Responsabilidad LLM |
|-------|--------|---------------------|
| 1 | Combate Táctico | IA toma decisiones tácticas (movimiento, selección de objetivo, habilidades) |
| 2 | Espionaje | IA decide reclutamiento de espías, asignación de misiones, contra-espionaje |
| 3 | Constructor Razas | IA analiza raza personalizada del jugador y ajusta estrategia |
| 4 | Diplomacia | IA tiene personalidad diplomática, evalúa tratados, negocia, vota en Consejo |
| 5 | Diseño Naves | IA diseña naves optimizadas basándose en análisis del oponente |
| 6 | Galaxia Grande | Coordinar múltiples IAs con personalidades diferenciadas, prompts eficientes |

Para cada módulo, adaptar el prompt del sistema para incluir las reglas adicionales y las acciones disponibles.

---

## DOCKER

### Dockerfile del servicio de IA
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

### requirements.txt
```
fastapi>=0.104.0
uvicorn>=0.24.0
httpx>=0.25.0
pydantic>=2.5.0
python-dotenv>=1.0.0
```

---

## DOCUMENTACIÓN

El especialista AI/ML es responsable de crear y mantener la documentación del proyecto:

### Manual de Usuario
- Cómo registrarse y crear partida
- Guía de la interfaz (mapa galáctico, colonia, investigación, flotas)
- Reglas del juego explicadas
- Cómo funciona la IA
- Lista de cheats

### Documentación Técnica
- Arquitectura del sistema (4 contenedores)
- Flujo de datos entre componentes
- Formato de prompts y respuestas del LLM
- Inventario de modelos usados y sus características
- Métricas de rendimiento de la IA (tiempo de respuesta, calidad de decisiones)

### Inventario de Recursos IA
- Lista de todos los recursos generados con IA
- Herramienta utilizada para cada recurso
- Prompt aplicado
- Fecha de generación
- Ubicación en el proyecto

---

## REGLAS DE DESARROLLO

1. **Consulta SPECS.md** para formatos de datos y reglas del juego
2. **Fog of War estricto**: La IA NUNCA debe recibir información que no le corresponde
3. **JSON válido**: Asegurar que las respuestas del LLM sean siempre JSON parseable
4. **Fallback robusto**: Si todos los modelos fallan, la IA pasa turno (no crash)
5. **Tiempos**: Máximo 30 segundos por turno de IA
6. **Logging**: Registrar todos los prompts enviados y respuestas recibidas (para debug)
7. **Tokens API**: NUNCA hardcodear tokens — usar variables de entorno
8. **Validación**: Toda acción de la IA se valida contra las reglas antes de ejecutarse
9. **Personalidades**: Cada IA debe tener comportamiento diferenciado según personalidad
10. **Documentación**: Mantener README actualizado con instrucciones de setup

---

## CHECKLIST ANTES DE ENTREGAR

- [ ] Servicio de IA arranca en Docker sin errores
- [ ] Integración con GroQ funcional (al menos 1 modelo)
- [ ] O integración con GitHub Models funcional (al menos 1 modelo)
- [ ] Fallback entre modelos funcional
- [ ] IA toma decisiones coherentes (coloniza, construye, investiga, mueve flotas)
- [ ] IA respeta fog of war
- [ ] Validación de acciones robusta
- [ ] Prompts por personalidad implementados
- [ ] Tiempo de respuesta < 30 segundos
- [ ] Estructura JSON de partidas documentada y consistente con backend/frontend
- [ ] Acciones de IA devueltas para visualización en frontend
- [ ] Módulo específico del grupo integrado en los prompts
- [ ] Documentación completa (manual usuario + técnica)
- [ ] Inventario de recursos generados por IA
- [ ] Dockerfile funcional
