# 06 — Colonización y gestión de planetas

## Lo que ya está implementado

- 9 climas en `game_service.py` constantes (toxic, barren, desert, tundra, arid, swamp, ocean, terran, gaia).
- 5 niveles de riqueza mineral con modificadores 0.33→2.0.
- 5 tamaños (tiny→huge) con `max_pop` y `build_slots`.
- 8 edificios en [buildings.json](../backend/app/data/buildings.json): marine_barracks, automated_factory, research_lab, hydroponic_farm, star_base, missile_base, spaceport, trade_center.
- `calculate_colony_production()` suma `production_bonus`, `research_bonus`, `food_bonus`, `bc_bonus` por edificio.
- Estructura de colonia con asignación farmer/worker/scientist y `morale`.

## Cambios necesarios

### Climas faltantes
- [ ] El PDF lista **Radiactivo** como tipo separado de tóxico/árido. Verificar en `game_service.py` si existe `radiated`; si no, añadirlo con habitabilidad similar a tóxico (requiere `radiation_shielding` para colonizar).
- [ ] Añadir efectos diferenciales reales:
  - Tóxico: -50% pop max, requiere tech.
  - Radiactivo: igual.
  - Árido / Desierto / Tundra: -alimentos.
  - Oceánico: bonus para razas Aquatic, sin penalización para otras.
  - Continental / Templado: estándar.
  - Gaia: +alimento, +pop max, +moral.

### Tamaños y planetas especiales
- [ ] Añadir tamaño `tiny` y `huge` si no están alineados con los del PDF (Pequeño/Mediano/Grande/Enorme).
- [ ] **Gigantes de Gas**: añadir como tipo de planeta no colonizable (`type: "gas_giant"`). Solo tras investigar `artificial_planet_construction` se pueden convertir gastando 800 PP en una fábrica especial.
- [ ] **Cinturones de Asteroides**: tipo `asteroid_belt`, mismas reglas (convertibles a planeta artificial).

### Edificios faltantes
Añadir a [buildings.json](../backend/app/data/buildings.json):
- [ ] `imperial_palace` — único por imperio; bonus de moral global; si se pierde, -moral.
- [ ] `robotic_factory` — `pp_per_worker` escalado por `mineral_richness`.
- [ ] `soil_enrichment` — +1 alimento por farmer.
- [ ] `terraforming_facility` — proyecto que mejora un nivel el clima cada N turnos (consume PP continuamente o paga coste único).
- [ ] `gaia_transformation` — caso terminal de terraforming a Gaia (necesita la tech).
- [ ] `alien_management_center` — duplica la velocidad de asimilación de pobladores extranjeros.
- [ ] `artificial_planet_construction` — fábrica que convierte gas giant/asteroide en mundo colonizable (800 PP).
- [ ] `autolab` — 30 RP fijos.
- [ ] `weather_controller` — anula penalizaciones climáticas en ese planeta.
- [ ] `holo_simulator` — +moral.
- [ ] `pleasure_dome` — +moral mayor.
- [ ] `astro_university` — bonifica RP por scientist.
- [ ] `galactic_currency_exchange` — bonifica BC.
- [ ] `subterranean_farms` — +alimento adicional.
- [ ] `cloning_center` — acelera crecimiento de población.
- [ ] `androids` — consume 1 PP/turno, produce como trabajador, no necesita comida (representado como tipo de población especial).

### Edificios "gratis al inicio"
- [ ] Marcar `marine_barracks` y `star_base` como `auto_built: true` en cada colonia nueva (el PDF dice que son gratis al inicio).
- [ ] El homeworld debería empezar con: marine_barracks, star_base, imperial_palace.

### Riqueza mineral exacta
- [ ] Ajustar la fórmula de la `robotic_factory` a los valores del PDF: +5/+8/+10/+15/+20 PP según ultra_poor/poor/abundant/rich/ultra_rich.

### Asignación de población
- [ ] Verificar que la pantalla de colonia muestra los efectos exactos de cada slider (food/PP/RP) en función de los edificios construidos.
- [ ] Mostrar pop max, contaminación, moral, comida neta, PP neto, RP neto y BC neto.
- [ ] Soporte para androides como tipo separado (no consume comida, cuesta 1 PP/turno).

### Terraformación progresiva
- [ ] Implementar como cola de proyectos: cada `terraforming_facility` construido eleva el clima un nivel cada X turnos.
- [ ] La tech `gaia_transformation` permite saltar a Gaia desde Terran.

### Contaminación
- [ ] Añadir `pollution` al estado de colonia, calculado por las fábricas activas.
- [ ] Penaliza alimentos (cosechas envenenadas) y moral.
- [ ] Edificios `pollution_processor` la mitigan.
- [ ] El rasgo `tolerant` la ignora.

### Frontend
- [ ] [ColonyView.vue](../frontend/src/views/ColonyView.vue) debe mostrar:
  - Clima, tamaño, riqueza, gravedad del planeta.
  - Slots de construcción ocupados / disponibles.
  - Lista de edificios con icono y descripción.
  - Cola de construcción ordenable.
  - Indicadores de moral, contaminación, asimilación (si es colonia conquistada).
  - Botón terraform si la tech está investigada.
