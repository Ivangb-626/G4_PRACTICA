# AGENT-LLM.md — MyMasterOfHostias: AI/LLM Service Developer Instructions

---

## ROLE

You are the **AI/LLM Specialist** agent for MyMasterOfHostias, a MOO2-faithful 4X space strategy game. You maintain the FastAPI AI service that drives AI opponents via LLM prompts (Groq + GitHub Models) with rule-based fallback, and manage diplomacy/tactical AI endpoints.

---

## TECH STACK

- **Framework**: FastAPI + uvicorn
- **Language**: Python 3.11+
- **LLM Providers**:
  - Primary: **Groq** (`llama-3.3-70b-versatile`) via OpenAI-compatible API
  - Fallback: **GitHub Models** (`gpt-4o-mini`) via Azure inference endpoint
  - Final fallback: Rule-based (no LLM)
- **HTTP Client**: `httpx` (synchronous in `__init__.py`, async not used)
- **Containerization**: Docker (container name: `mmoh-ai-service`, port 8000)
- **Config**: Environment variables (`GROQ_API_KEY`, `GITHUB_TOKEN`)

---

## ACTUAL PROJECT STRUCTURE

```
ai-service/
├── main.py                  # FastAPI app with 3 endpoints
├── ai/
│   ├── __init__.py          # LLM provider abstraction: _groq_complete(), _github_complete(), ai_complete()
│   ├── strategic.py         # Strategic AI turn logic: decide_turn(), _summarize_state(), _rule_based_turn()
│   ├── tactical.py          # Tactical combat AI
│   └── diplomacy_ai.py     # Diplomacy AI decisions
├── requirements.txt
├── Dockerfile
└── .env
```

**Note**: The service is flat (no `app/` package, no `routes/`, no `providers/`, no `prompts/` folders). All logic is in `main.py` + `ai/` package.

---

## ENDPOINTS (3 total)

### POST `/ai/turn` — Strategic AI Turn

Called by the backend's `turn_engine.py` during `_execute_ai_turns()`.

**Request Body:**
```json
{
  "game_id": "string",
  "ai_player_id": "string",
  "personality": "aggressive|defensive|expansionist|researcher|balanced",
  "difficulty": "easy|normal|hard",
  "state": {
    "turn": 42,
    "colonies": [],
    "fleets": [],
    "tech_state": {},
    "available_techs": [],
    "galaxy": {},
    "bc": 500,
    "relations": []
  }
}
```

**Response 200:**
```json
{
  "actions": [
    {"type": "manage_colony", "colony_id": "...", "farmers": 3, "workers": 4, "scientists": 2, "build_queue": []},
    {"type": "select_research", "tech_id": "fusion_beam"},
    {"type": "move_fleet", "fleet_id": "...", "destination": 5},
    {"type": "colonize", "fleet_id": "..."}
  ]
}
```

### POST `/ai/diplomacy` — Diplomacy Response

**Request Body:**
```json
{
  "game_id": "string",
  "ai_player_id": "string",
  "proposal": {},
  "relations": [],
  "personality": "string"
}
```

**Response 200:**
```json
{
  "accept": true,
  "reason": "Alliance is strategically beneficial"
}
```

**Error fallback:** Returns `{"accept": false, "reason": "Error processing proposal"}` on any exception.

### POST `/ai/tactical` — Tactical Combat

**Request Body:**
```json
{
  "game_id": "string",
  "session_id": "string",
  "ai_player_id": "string",
  "state": {}
}
```

**Response 200:**
```json
{
  "action": {"type": "move", "ship_id": "...", "x": 5, "y": 3}
}
```

**Error fallback:** Returns `{"action": {"type": "wait"}}` on any exception.

---

## LLM PROVIDER CHAIN (`ai/__init__.py`)

The module provides a single function `ai_complete(prompt: str) -> str` that tries providers in order:

```python
def ai_complete(prompt: str) -> str:
    """Try Groq -> GitHub Models -> return empty string."""

    # 1. Try Groq (if GROQ_API_KEY set)
    result = _groq_complete(prompt)
    if result:
        return result

    # 2. Try GitHub Models (if GITHUB_TOKEN set)
    result = _github_complete(prompt)
    if result:
        return result

    # 3. All failed
    return ""
```

### `_groq_complete(prompt)`:
- URL: `https://api.groq.com/openai/v1/chat/completions`
- Model: `llama-3.3-70b-versatile`
- Sends `[{"role": "user", "content": prompt}]`
- Returns `choices[0].message.content` or empty string on error

### `_github_complete(prompt)`:
- URL: `https://models.inference.ai.azure.com/chat/completions`
- Model: `gpt-4o-mini`
- **Retry logic**: 3 attempts with exponential backoff (1s, 2s, 4s)
- Catches: `HTTPStatusError` (5xx retries), `TimeoutException`, `ConnectError`
- Returns content or empty string after all retries exhausted

---

## STRATEGIC AI (`ai/strategic.py`)

### `decide_turn(state, personality, difficulty) -> list[dict]`

Main entry point called by `/ai/turn` endpoint:

```python
def decide_turn(state, personality, difficulty):
    summary = _summarize_state(state)       # Compact JSON (no truncation)
    prompt = f"You are an AI player in a 4X space game..."
    prompt += f"\nPersonality: {personality}, Difficulty: {difficulty}"
    prompt += f"\nGame state:\n{json.dumps(summary)}"
    prompt += "\nReturn JSON array of actions..."

    raw = ai_complete(prompt)               # Try LLM
    if raw:
        actions = json.loads(raw)           # Parse JSON
        return actions if isinstance(actions, list) else actions.get("actions", [])

    return _rule_based_turn(state)          # Fallback: no LLM
```

### `_summarize_state(state) -> dict`

Builds a compact summary instead of truncating raw JSON:

- **Colonies**: Only `id, star_index, pop, workers, farmers, scientists, morale, buildings, build_queue[:3]`
- **Fleets**: Only `id, star_index, in_transit, destination, eta, ships`
- **Tech**: Only `current_research` + `researched` list
- **Available techs**: IDs only, max 20
- **Explored stars**: Only stars with useful info (`name, x, y, owner, planets[type, size, minerals, colonized_by]`)
- **Unexplored stars**: Just a count
- **BC, turn, relations**: Passed through

### `_rule_based_turn(state) -> list[dict]`

Deterministic fallback when all LLMs fail:
1. For each colony: balance workers/farmers/scientists, queue research_lab if not built
2. Select cheapest available tech
3. Move idle fleets toward nearest unexplored star
4. Colonize if colony ship at habitable planet

---

## ERROR HANDLING

1. **`/ai/diplomacy`**: Full try/except with safe default `{accept: false}`
2. **`/ai/tactical`**: Full try/except with safe default `{action: {type: "wait"}}`
3. **`_github_complete`**: 3 retries with exponential backoff for 5xx errors
4. **`_groq_complete`**: Single attempt, catches all exceptions, returns empty string
5. **`ai_complete`**: Chain guarantees a return value (at worst empty string)
6. **`decide_turn`**: Falls back to `_rule_based_turn()` when LLM returns empty/invalid
7. **No crash path**: Every endpoint has a safe default response

---

## DOCKER

### Dockerfile
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose (relevant section)
```yaml
mmoh-ai-service:
  build: ./ai-service
  container_name: mmoh-ai-service
  ports:
    - "8000:8000"
  environment:
    - GROQ_API_KEY=${GROQ_API_KEY}
    - GITHUB_TOKEN=${GITHUB_TOKEN}
```

### Environment Variables
| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | At least one | Groq API key for llama-3.3-70b |
| `GITHUB_TOKEN` | At least one | GitHub token for gpt-4o-mini |

At least one provider must be configured, or the service falls back to rule-based AI.

---

## BACKEND INTEGRATION

The backend calls this service from `turn_engine.py`:

```python
# turn_engine.py -> _execute_ai_turns()
response = requests.post(
    "http://mmoh-ai-service:8000/ai/turn",
    json={
        "game_id": game_id,
        "ai_player_id": ai_id,
        "personality": ai_player["personality"],
        "difficulty": game["difficulty"],
        "state": _prepare_ai_state(game, galaxy, ai_id)
    },
    timeout=30
)
actions = response.json().get("actions", [])
# Each action validated by _validate_and_execute_ai_action()
```

**Key point**: The backend validates and executes each AI action — the AI service only suggests actions.

---

## PROMPT ENGINEERING NOTES

### Personality Mapping

Each AI personality affects the system prompt:
- **Aggressive**: Prioritize military, attack early, declare war
- **Defensive**: Build defenses, research shields, prefer diplomacy
- **Expansionist**: Colony ships first, colonize everything
- **Researcher**: Maximize scientists, research labs everywhere
- **Balanced**: Adapt to situation, maintain balance

### Prompt Structure

The prompt sent to the LLM includes:
1. Role definition ("You are an AI player in a 4X space game")
2. Personality and difficulty
3. Compacted game state (from `_summarize_state()`)
4. Available action types and their JSON format
5. Request for JSON array response

### JSON Parsing

The LLM response is parsed with `json.loads()`. Common issues:
- LLM wraps response in markdown code blocks — strip before parsing
- LLM returns `{"actions": [...]}` instead of `[...]` — handle both
- LLM returns invalid JSON — fall back to rule-based

---

## KEY CONVENTIONS

1. **Flat structure**: No `app/` package — `main.py` is directly in `ai-service/`
2. **Synchronous HTTP**: `httpx` used synchronously (not async), despite FastAPI being async
3. **No prompt files**: Prompts are built inline in `strategic.py`, not loaded from templates
4. **Fog of war**: Backend filters state before sending — AI service receives only visible data
5. **Action validation**: Done by backend, not AI service
6. **Secrets**: From environment variables — never hardcoded
7. **Container name**: `mmoh-ai-service` (used for inter-container HTTP calls)

---

## CHECKLIST

- [x] FastAPI service with 3 endpoints (/ai/turn, /ai/diplomacy, /ai/tactical)
- [x] Groq integration (llama-3.3-70b-versatile)
- [x] GitHub Models integration (gpt-4o-mini) with retry/backoff
- [x] Automatic fallback chain (Groq -> GitHub -> rule-based)
- [x] Intelligent state summarization (no truncation)
- [x] Rule-based fallback for all endpoints
- [x] Error handling with safe defaults on all endpoints
- [x] Personality-aware prompts
- [x] Docker deployment (port 8000)
- [x] AI actions returned for frontend visualization
