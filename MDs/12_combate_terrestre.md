# 12 — Combate terrestre

## Lo que ya está implementado

- Archivo [ground_combat.py](../backend/app/services/ground_combat.py) existe pero está **vacío**.
- Campo `ground_defense` en estructura de colonia — sin lógica.

## Cambios necesarios

### Modelo
- [ ] Tipo de nave `transport` en [ships.json](../backend/app/data/ships.json) (existe). Verificar que tiene capacidad `marine_capacity` (e.g. 6 marines por transporte).
- [ ] La colonia debe trackear `marines` (ataque defensivo). Cada `marine_barracks` da +X marines automáticamente; entrenamiento en cola de construcción para más.
- [ ] Definir `marine_tech_level` por imperio según las técnicas de armamento terrestre investigadas: `Soldiers` → `Tank` → `Marine Tank` → `Battleoids` → `Microlite Construction` etc.

### Servicio de combate terrestre
Implementar [ground_combat.py](../backend/app/services/ground_combat.py):
- [ ] `prepare_invasion(fleet, target_colony)`:
  - Verifica que la flota orbita el sistema y tiene transports con marines.
  - Si tiene bombas, puede ejecutar fase de bombardeo previo.
- [ ] `bombard(fleet, target_colony, intensity)`:
  - Por cada bomba, daño aleatorio a marines defensores, población, edificios (no Imperial Palace).
  - Las razas Telepáticas pueden saltarse esta fase.
- [ ] `resolve_invasion(fleet, target_colony)`:
  - Calcula fuerza atacante: `marines * (1 + tech_level_diff*0.1) * (1 + race_ground_bonus/100) * (1 + experience/100)`.
  - Calcula fuerza defensora: igual con sus bonos + bonus por `marine_barracks` + planeta natal +50%.
  - Resolución por rondas: ambos bandos pierden marines proporcionalmente. El que llegue a 0 pierde.
  - Si los atacantes ganan: la colonia cambia de owner.
  - Si los defensores ganan: la flota pierde sus transports.

### Mind Control (Telepáticos)
- [ ] `mind_control(empire, target_colony)`:
  - Solo si `empire.race.telepathic == true`.
  - Solo si la flota está en órbita y la colonia no tiene `mind_shield` (líder Protector Mental).
  - Calcula chance vs `target_colony.population * (1 + government_morale_bonus)`.
  - Si éxito: la colonia cambia de owner sin combate ni daño.
  - Si fracaso: la colonia recibe -25 moral, atacante puede reintentar el siguiente turno.

### Asimilación y conquista
- [ ] Tras conquista, marcar la colonia con:
  - `morale = -50`.
  - `assimilation_progress = 0`.
  - `original_owner = previous_owner`.
- [ ] Cada turno, `assimilation_progress += 5` (sin centro) o `+ 10` (con `alien_management_center`).
- [ ] Mientras `assimilation_progress < 100`:
  - La colonia tiene -50% productividad.
  - Probabilidad de **rebelión** cada turno: `(100 - assimilation_progress) * 0.5%`. Si ocurre, la colonia retorna a `original_owner`.
  - Susceptible a `incite_rebellion` espionaje (ver [11_diplomacia_espionaje.md](11_diplomacia_espionaje.md)).
- [ ] A 100%, los pobladores cuentan como propios (productividad y leva normales).

### Exterminio
- [ ] Al ganar combate terrestre, mostrar opción "Asimilar / Exterminar":
  - **Asimilar**: comportamiento por defecto.
  - **Exterminar**: la colonia pierde toda la población alienígena (queda una colonia "vacía" lista para repoblar). Aplica penalización diplomática global (todas las razas que conozcan al imperio empeoran su relación, especialmente la víctima).

### Captura de tecnología
- [ ] Probabilidad `0.3` por colonia conquistada de obtener 1 tech aleatoria del enemigo entre las que el atacante no posee.

### Frontend
- [ ] Modal de invasión: muestra fuerza estimada de cada bando, opciones (bombardear primero / asaltar / Mind Control si aplica).
- [ ] Animación / log de la batalla por rondas.
- [ ] Tras conquista: diálogo "Asimilar / Exterminar".
- [ ] Indicadores de asimilación en [ColonyView.vue](../frontend/src/views/ColonyView.vue) para colonias conquistadas.
