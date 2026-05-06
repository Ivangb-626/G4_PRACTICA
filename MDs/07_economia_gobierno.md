# 07 — Economía y gobierno

## Lo que ya está implementado

- BC tracked en `empire["resources"]["bc"]`, incrementado por turno.
- Cálculo de food/consumo y starvation en `_compute_empire_economy()`.
- 3 gobiernos definidos en el sistema de razas (democracy, dictatorship, unification).
- Campo `morale` en colonia (`"stable"`) — sin efecto computable.

## Cambios necesarios

### Catálogo completo de gobiernos
- [ ] Añadir todos los tipos en un nuevo archivo [backend/app/data/governments.json](../backend/app/data/governments.json):
  ```json
  [
    {
      "id": "dictatorship",
      "name": "Dictatorship",
      "modifiers": {"counter_espionage": 0.10, "morale_bonus": 0},
      "available": "default"
    },
    {
      "id": "democracy",
      "name": "Democracy",
      "modifiers": {"research": 0.50, "bc": 0.50, "counter_espionage": -0.10, "ground_combat": -0.20},
      "available": "default"
    },
    {
      "id": "unification",
      "name": "Unification",
      "modifiers": {"morale_immune": true, "production": 0.10},
      "available": "default"
    },
    {
      "id": "monarchy",
      "name": "Monarchy",
      "modifiers": {"morale_bonus": 0.10},
      "available": "default"
    },
    {
      "id": "oligarchy",
      "name": "Oligarchy",
      "modifiers": {"bc": 0.20},
      "available": "default"
    },
    {
      "id": "republic",
      "name": "Republic",
      "modifiers": {"research": 0.20, "bc": 0.20, "counter_espionage": -0.05},
      "available": "default"
    },
    {
      "id": "feudal",
      "name": "Feudal",
      "modifiers": {"morale_bonus": 0.10, "ship_cost_reduction": 0.30, "research": -0.50},
      "available": "tech:feudal_state"
    },
    {
      "id": "technocracy",
      "name": "Technocracy",
      "modifiers": {"research": 0.30, "counter_espionage": 0.05},
      "available": "tech:technocracy"
    }
  ]
  ```

### Aplicación de los modificadores
- [ ] `colony_service.calculate_colony_production()` debe leer el `government_modifiers` del empire y aplicar:
  - `+research` a RP totales.
  - `+bc` a ingresos totales.
  - `+production` a PP.
- [ ] `espionage_service` debe aplicar `counter_espionage` (positivo o negativo) al cálculo defensivo.
- [ ] `ground_combat` debe restar `ground_combat` modifier (Democracia tiene -20%).

### Sistema de moral funcional
- [ ] Cambiar `colony["morale"]` de string a número (-100 a +100).
- [ ] Multiplicador efectivo: `production *= 1 + (morale / 100)`.
- [ ] Fuentes de moral:
  - **Barracones Marinos**: +20.
  - **Imperial Palace**: +10 a la colonia capital, +5 a las demás.
  - **Pleasure Dome**: +30.
  - **Holo-Simulator**: +20.
  - **Tipo de gobierno**: Monarchy +10, Feudal +10.
  - **Conquista reciente**: -50 los primeros 5 turnos, recuperación gradual.
  - **Pérdida del Imperial Palace**: -30 a todas las colonias durante 10 turnos.
  - **Líder espiritual asignado**: +bonus.
- [ ] Las razas con gobierno **Unificación** ignoran el cálculo de moral (`morale_immune: true`).
- [ ] Las razas **Cibernéticas** (Meklars) también son inmunes a moral.

### Cambio de gobierno
- [ ] Endpoint `POST /api/empire/change_government` con coste: revuelta de transición de 3-5 turnos en los que la moral cae a -50.
- [ ] Algunos gobiernos requieren tecnología (Feudal, Technocracy, Confederation, Imperium, Galactic Unification).
- [ ] Las razas marcadas con gobierno fijo (e.g. Klackons → Unification) no pueden cambiar.

### Impuestos
- [ ] Añadir `tax_rate` configurable (0% a 50%) en el empire.
- [ ] Más impuestos → más BC pero -moral en todas las colonias.
- [ ] UI con slider en pantalla del imperio.

### Comercio
- [ ] Tratados comerciales en [diplomacy_service.py](../backend/app/services/diplomacy_service.py) generan BC ambos lados según el tamaño de los imperios.
- [ ] El edificio `galactic_currency_exchange` aumenta los ingresos de comercio.

### Colonias recién conquistadas
- [ ] Inicializar `morale: -50` y `assimilation_progress: 0` al ser conquistadas.
- [ ] Cada turno asimilación progresa: +5 sin centro de gestión, +10 con `alien_management_center`.
- [ ] A 100% asimilación, los pobladores cuentan como propios.
- [ ] Hasta entonces, riesgo de **rebelión** que devuelve la colonia al imperio original (probabilidad inversa a moral).

### Frontend
- [ ] Pantalla del imperio con: BC, ingresos/turno, gastos/turno, gobierno actual, moral promedio, lista de colonias con su moral individual.
- [ ] Botón cambiar gobierno con confirmación de coste.
- [ ] Slider de impuestos.
