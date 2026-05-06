# 03 — Razas jugables (Alkari, Meklar, Trilarian)

El proyecto solo necesita dar soporte a **3 razas**: Alkari, Meklar y Trilarian. Las demás razas listadas en la guía no son objetivo de implementación.

## Lo que ya está implementado

- 3 razas en [backend/app/data/races.json](../backend/app/data/races.json): Alkari, Meklar, Trilarian.
- Atributos numéricos por raza: `ship_attack_bonus`, `ship_defense_bonus`, `ground_combat_bonus`, `research_bonus`, etc.
- Selección de raza en `_initial_empire()` y validación en escenarios.
- Cada raza tiene `default_government` definido.

## Cambios necesarios

### Características clave a verificar/asegurar

#### Alkari
- [ ] Rasgo principal: **+20 Defensa de nave** → confirmar que `ship_defense_bonus: 20` está leído por [tactical_combat.py](../backend/app/services/tactical_combat.py) cuando se implemente el combate.
- [ ] Homeworld de clima estándar (continental/templado), riqueza abundante.
- [ ] Gobierno por defecto: **Dictadura**.
- [ ] Personalidad de IA militarista y honorable: tendencia moderada a declarar guerra, respeta tratados firmados.

#### Meklar
- [ ] Rasgo principal: **Cibernético** + **+2 Producción**.
- [ ] Añadir flag `cybernetic: true` en `traits` y aplicar en [colony_service.py](../backend/app/services/colony_service.py):
  - Cada colono cibernético consume **0.5 comida** (en lugar de 1).
  - Consume **1 PP/turno** por colono adicional (energía).
  - Reparación de naves en combate: 10% armadura por turno (cuando se implemente combate táctico).
- [ ] Cada worker produce **+2 PP** adicionales.
- [ ] Homeworld estándar.
- [ ] Gobierno: **Dictadura**.
- [ ] Personalidad IA pragmática-industrial.

#### Trilarian
- [ ] Rasgo principal: **Acuático** + **Transdimensional** + **+1 Investigación**.
- [ ] Añadir flag `aquatic: true`: planetas oceánicos cuentan como Templados/ideales en `colony_service.py`.
- [ ] Añadir flag `transdimensional: true`:
  - +2 a la velocidad base de todas las naves del imperio.
  - Pueden moverse entre estrellas sin tecnología de propulsión warp inicial.
- [ ] Cada scientist produce **+1 RP** adicional.
- [ ] Homeworld preferentemente oceánico.
- [ ] Gobierno: **Dictadura** (o el que ya tenga asignado en `races.json`).
- [ ] Personalidad IA exploradora.

### Aplicación de los rasgos en servicios

- [ ] [colony_service.py](../backend/app/services/colony_service.py) → leer flags `cybernetic` (Meklar) y `aquatic` (Trilarian) al calcular producción y consumo.
- [ ] [tactical_combat.py](../backend/app/services/tactical_combat.py) (cuando se implemente) → leer `ship_attack_bonus` y `ship_defense_bonus` para todas las razas, en especial `+20 defense` de Alkari.
- [ ] [fleet_service.py](../backend/app/services/fleet_service.py) → leer flag `transdimensional` (Trilarian) para sumar +2 a la velocidad calculada.
- [ ] [research_service.py](../backend/app/services/research_service.py) → respetar `research_bonus` (Trilarian +1 por scientist).

### Personalidades de IA

- [ ] Cada raza necesita una `ai_personality` que [ai_service.py](../backend/app/services/ai_service.py) consulte para sesgar:
  - Frecuencia de declaración de guerra.
  - Aceptación de tratados.
  - Prioridad de investigación (militar / económica / científica).
  - Agresividad de expansión.
- [ ] Sugerencia: `alkari = militarist_honorable`, `meklar = industrial_pragmatic`, `trilarian = explorer_scholar`.

### Frontend

- [ ] Pantalla de selección de raza ([Dashboard.vue](../frontend/src/views/Dashboard.vue)) con las 3 razas, descripción, rasgos clave y un retrato/icono.
- [ ] Vista de razas contactadas en partida con su líder, gobierno, relación diplomática actual.
- [ ] Tooltip explicativo al pasar el ratón sobre cada rasgo.
