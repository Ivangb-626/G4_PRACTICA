# 04 — Diseño de raza personalizada

## Lo que ya está implementado

- **Nada.** El sistema no existe en el proyecto. Las razas son fijas vía `races.json`.

## Cambios necesarios

### Modelo de datos
- [ ] Crear nuevo archivo [backend/app/data/race_picks.json](../backend/app/data/race_picks.json) con la lista completa de ventajas y desventajas, cada una con `id`, `name`, `cost` (positivo o negativo), `description` y `effect_flags`:
  ```json
  {
    "advantages": [
      {"id": "creative", "name": "Creative", "cost": 4, "description": "...", "flags": {"creative": true}},
      {"id": "tolerant", "name": "Tolerant", "cost": 10, "description": "...", "flags": {"tolerant": true}},
      ...
    ],
    "disadvantages": [
      {"id": "repulsive", "name": "Repulsive", "cost": -6, "description": "...", "flags": {"repulsive": true}},
      ...
    ]
  }
  ```

### Backend
- [ ] Endpoint `GET /api/race-design/options` que devuelva el catálogo completo de picks.
- [ ] Endpoint `POST /api/race-design/validate` que reciba `{name, picks: [...], homeworld_traits, government}` y valide:
  - Suma total ≤ 10 picks.
  - Conflictos: no se pueden combinar `creative` + `uncreative`, `+1 production` + `-1 production`, etc.
  - `tolerant` (10 picks) excluye casi todo lo demás (1 punto restante).
  - Government válido para los flags elegidos (ej. `unification` ya cuesta picks aparte).
- [ ] Endpoint `POST /api/race-design/save` que persista la raza personalizada en la sesión del jugador antes de iniciar partida.
- [ ] Al iniciar partida, si el jugador eligió raza custom, fusionar los flags de `picks` en el bloque de raza del imperio.

### Aplicación de los flags en servicios
Reutilizar los mismos flags que las razas predefinidas (ver [03_razas.md](03_razas.md)). Asegurarse de que TODOS los servicios consultan los flags genéricos, no nombres de raza:
- [ ] `colony_service.py` → `tolerant`, `lithovore`, `subterranean`, `aquatic`, `+production`, `+science`, `artifacts_homeworld`, `rich_homeworld`.
- [ ] `research_service.py` → `creative`, `uncreative`.
- [ ] `tactical_combat.py` → `warlord`, `-20 ship defense`.
- [ ] `ground_combat.py` → `-10 ground combat`.
- [ ] `diplomacy_service.py` → `charismatic`, `repulsive`, `telepathic`.
- [ ] `espionage_service.py` → `-10 espionage`, `telepathic`.
- [ ] `leader_service.py` → `charismatic` (precio reducido y +1 al máximo).

### Multiplicador de puntuación
- [ ] El PDF indica que la puntuación final se multiplica por el porcentaje de raza custom (100% sin bonus, 110% con +10% extra). Calcular el porcentaje en función de los picks gastados:
  - Más picks gastados (más ventajas) → mayor dificultad → mayor multiplicador.
  - Implementar fórmula en [16_puntuacion.md](16_puntuacion.md).

### Frontend
- [ ] Nueva vista `RaceDesignView.vue` con:
  - Campo de nombre de raza y elección de retrato/icono.
  - Selector de homeworld (clima, riqueza, gravedad, tamaño) — algunos ya cuestan picks.
  - Selector de gobierno inicial (los gobiernos especiales como Unificación cuestan picks).
  - Lista de ventajas (checkboxes con coste mostrado).
  - Lista de desventajas (checkboxes con picks ganados).
  - Contador en vivo: "Picks restantes: X / 10".
  - Validación frontend antes de enviar al backend.
  - Botón "Guardar como plantilla" para reutilizar.
- [ ] Integrar en el flujo de creación de partida del [Dashboard.vue](../frontend/src/views/Dashboard.vue).
