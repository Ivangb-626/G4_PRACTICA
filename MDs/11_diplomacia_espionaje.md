# 11 — Diplomacia e Inteligencia / Espionaje

## Lo que ya está implementado

- Estructura `diplomacy` inicializada en `initialize_diplomacy()` (relations tracking).
- Rutas: `/propose`, `/accept`, `/war` en [diplomacy.py](../backend/app/routes/diplomacy.py).
- `get_relation_key()` y `_factions_hostile()` en `game_service.py`.
- Rutas de espionaje: `/recruit`, `/mission` en [espionage.py](../backend/app/routes/espionage.py) — stubs.
- Servicios [diplomacy_service.py](../backend/app/services/diplomacy_service.py) y [espionage_service.py](../backend/app/services/espionage_service.py) — lógica stub.

## Cambios necesarios

## A. Diplomacia

### Tipos de tratado
- [ ] Crear modelo de `Treaty` con: `id`, `type`, `parties`, `terms`, `signed_at_turn`, `expires_at_turn` (si aplica), `active`.
- [ ] Tipos a soportar: `non_aggression_pact`, `trade_treaty`, `research_pact`, `alliance`, `war`, `surrender`, `tribute`.
- [ ] Persistir en `game_state["diplomacy"]["treaties"]`.

### Acciones diplomáticas
Implementar en [diplomacy_service.py](../backend/app/services/diplomacy_service.py):
- [ ] `propose_treaty(empire_a, empire_b, treaty_type, terms)`:
  - Calcula la propensión de la IA a aceptar según: relación actual, balance de poder, rasgos (`charismatic` da bonus, `repulsive` cancela todo).
- [ ] `accept_treaty(treaty_id)` / `reject_treaty(treaty_id)`.
- [ ] `gift(from, to, payload)` con `payload`: BC, tech_id o colony_id. Mejora la relación.
- [ ] `demand(from, to, payload)`: si se rechaza, empeora la relación o desencadena guerra.
- [ ] `propose_tech_trade(from, to, offered_tech, requested_tech)`: intercambio único.
- [ ] `declare_war(from, to)`: rompe todos los tratados con esa raza.
- [ ] `offer_surrender(from, to)`: termina la guerra; el perdedor entrega colonias o tecs.
- [ ] `blackmail(from, to, secret)`: si se posee información comprometedora, extorsiona BC/tecs. La info se obtiene mediante operaciones de espionaje.

### Tratado Comercial
- [ ] Cada turno, mientras `trade_treaty` esté activo, ambos imperios reciben BC proporcionales a la suma de población de las colonias en rango comercial.
- [ ] El edificio `galactic_currency_exchange` y la habilidad de líder **Trader** multiplican estos ingresos.

### Alianza
- [ ] Una alianza implica:
  - No agresión mutua automática.
  - Visión compartida de mapa.
  - Acceso a las flotas del aliado para soporte (sin control directo).
  - La IA aliada interviene en combates si la flota está en rango.
  - Rotura: penalización fuerte de relación con todas las civilizaciones.

### Personalidad de IA
- [ ] Cada raza tiene perfil (ver [03_razas.md](03_razas.md)) que afecta a:
  - Tendencia a ofrecer tratados.
  - Aceptación de propuestas humanas.
  - Probabilidad de declarar guerra.
- [ ] Razas con `repulsive` solo pueden declarar guerra o rendirse.

### Senado Galáctico
Detallado en [15_condiciones_victoria.md](15_condiciones_victoria.md), pero relacionado: cada N turnos, cuando hay 3+ imperios contactados, se convoca el Senado y se vota un Líder Supremo.

## B. Espionaje

### Modelo de espía
- [ ] `Spy` con: `id`, `owner`, `assignment` (target empire id o "defense"), `mission` (steal_tech | sabotage | incite_rebellion | frame), `experience`, `cost_per_turn`.
- [ ] Persistir en `empire["spies"]`.

### Reclutamiento
- [ ] `recruit_spy(empire)` — coste BC + asigna disponible.
- [ ] Sin límite duro, pero coste creciente exponencial.

### Asignación
- [ ] `assign_spy(spy_id, target_empire | "defense", mission)`.
- [ ] Endpoint `POST /api/espionage/assign`.

### Operaciones
Implementar en [espionage_service.py](../backend/app/services/espionage_service.py) con resolución cada turno:

- [ ] **Steal Tech**:
  - `success_chance = base_attack + spy_exp + race_bonus + leader_spy_bonus - target_counter_intel`.
  - Si éxito, copia 1 tech aleatoria del rival a `empire.tech.researched`.
  - Si captura: empeora relación, posible declaración de guerra.

- [ ] **Sabotage**:
  - Apunta a un edificio aleatorio o específico (Star Base, Marine Barracks).
  - Si éxito: destruye el edificio en una colonia.
  - Si captura: empeora relación.

- [ ] **Incite Rebellion**:
  - Solo válido contra colonias recién conquistadas (assimilation_progress < 100%).
  - Si éxito: la colonia retorna al imperio original.

- [ ] **Frame** (Darlok specialty):
  - Realiza la operación bajo bandera falsa.
  - Si captura, la culpa va a otro imperio (penalizando relación con el imperio víctima en lugar del propio).

### Contrainteligencia
- [ ] Si `assignment == "defense"`, el espía aumenta `counter_intelligence` total del imperio.
- [ ] Modificadores:
  - **Dictadura**: +10% counter.
  - **Democracia**: -10% counter.
  - **Líder Counter-Spy**: +bonus.
  - Edificios: añadir `cyber_security_link` que da +counter.

### Rasgos raciales
- [ ] **Darloks**: +20 al ataque y defensa de espionaje, +probabilidad de framing exitoso.
- [ ] Razas con `-10 espionaje`: penalización equivalente.

### Resolución
- [ ] Al final de cada turno, [turn_engine.py](../backend/app/services/turn_engine.py) llama a `espionage_service.resolve_missions()` que itera todos los espías ofensivos y resuelve operaciones según la fórmula.

### Frontend
- [ ] [DiplomacyView.vue](../frontend/src/views/DiplomacyView.vue): pantalla con lista de imperios contactados, relación actual, opciones de propuesta, historial de tratados.
- [ ] [EspionageView.vue](../frontend/src/views/EspionageView.vue): lista de espías, asignaciones, rivales con su `counter_intelligence` estimado, log de operaciones.
- [ ] Notificaciones: "Espía capturado", "Tech robada con éxito", "Sabotaje en X colonia".
