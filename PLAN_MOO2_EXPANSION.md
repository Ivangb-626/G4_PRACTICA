# Plan de Implementación de Mecánicas Avanzadas (MOO2)

Este documento detalla las modificaciones y adiciones necesarias en el backend (Flask) y frontend (Vue 3) del proyecto para dar soporte a las mecánicas avanzadas descritas en el texto "GAMEPLAY" de Master of Orion II.

## 1. Anomalías y Planetas Especiales
**Objetivo:** Permitir que los recursos especiales no sean solo visuales, sino que otorguen bonificaciones tangibles y eventos únicos.

* **Backend (`colony_service.py` / `game_service.py`):**
  * Modificar la lógica de colonización para comprobar si el planeta tiene el rasgo `special: "artifacts"`. Si es así, otorgar un progreso masivo de investigación ("breakthrough") o una tecnología gratuita a la facción.
  * Implementar la raza/entidad "Nativos": Si un planeta tiene nativos, habilitar un modificador automático a la producción de comida (por ej. +2/+3 por granjero en ese bioma) y asignarles automáticamente granjas.
  * *Splinter Colonies:* Lógica en la exploración (`movement` / `sensor check`) de naves para que si se detecta un sistema con colonia escindida, se anexe instantáneamente al imperio con X población inicial.
* **Frontend (`SystemView.vue` / `ColonyView.vue`):**
  * Mostrar avisos interactivos alertando de los eventos (ej. "¡Artefactos descubiertos!" o "¡Colonia unificada!").
  * Ícono de "Nativos" en el resumen de granjeros de la colonia.

## 2. Sistema de Comida Global, Freighters y Bloqueos
**Objetivo:** Transicionar de una comida puramente local a una red civil interplanetaria.

* **Backend (`colony_service.py` / motor de turnos):**
  * Agregar la entidad "Cargueros" (Freighters) en la variable global del imperio, deduciendo 0.5 BC por cada carguero activo.
  * Cuando se procese el fin de turno, las colonias con deficit de comida no morirán inmediatamente si el Imperio total está en superávit Y existen suficientes freighters disponibles.
  * **Bloqueos Navales (`combat_service.py` / exploración):** Si una flota enemiga está orbitando y no hay flota defensora, marcar el sistema como `blockaded: true`. Un planeta bloqueado no puede enviar ni recibir comida de la red de flete.

## 3. Puntos de Comando de la Flota (Command Points)
**Objetivo:** Limitar el spam de naves tempranas castigando la economía.

* **Backend (Resolución de turno):**
  * Recalcular "Command Points Máximos" del jugador: (Base Inicial + Modificadores por Starbases / Battlestations).
  * Calcular "Command Points Usados" (Frigate = 1, Destroyer = 2, Cruiser = 3, Battleship = 4, Titan = 5, Doom Star = 6).
  * Si `Usados > Máximos`, cada punto de excedente cuesta 10 BC (o 20 BC dependiendo de la dificultad). Si el BC llega a < 0, entrar en déficit (forzando chatarra/scrap de naves automáticas).
* **Frontend (`Dashboard.vue` / `FleetManager.vue`):**
  * Añadir el contador de Puntos de Comando (ej. `Command Points: 15 / 20`) en la barra de recursos superior, advirtiendo en rojo si se está en sobrecoste.

## 4. Telepatía, Combate y Rebeliones
**Objetivo:** Dinamizar las postrimerías del asalto planetario.

* **Backend (`combat_service.py`):**
  * Crear la acción `mind_control()`: Accesible si la raza atacante tiene el rasgo *Telepathic*. Captura instantáneamente el planeta sin invasión terrestre.
  * **Motor de Rebelión (`colony_service.py`):** Los planetas invadidos militarmente reciben un `rebellion_timer` (ej. 5 turnos). Durante esto, toda la producción y ciencia disminuye un 50%.
  * Si el atacante es *Telepathic*, el timer se establece en 0 (asimilación instantánea).
* **Frontend (`CombatResult.vue` / `ColonyView.vue`):**
  * Botón especial en ataque orbital "Control Mental" si aplica.
  * Mostrar el debuff de rebelión en el panel de colonias (Ej: ícono de "Población Descontenta").

## 5. Edificios, Contaminación y Bombardeo Orbital
**Objetivo:** Reglas físicas del planeta y exterminio definitivo.

* **Backend (`colony_service.py`):**
  * Implementar el cálculo de "Contaminación" (Pollution) basado en la industria (Worker production). Todo punto que exceda la "Tolerancia del bioma" resta directamente unidades a la producción base antes de aplicarse a las colas de construcción. 
  * Construir el "Pollution Processor" mitigará esto. Rasgos como *Tolerant* o *Lithovore* modificarán el cálculo.
* **Backend (`combat_service.py`):**
  * Expandir el combate añadiendo la ruta `POST /combat/bombard`. Requiere flotas en órbita. Tira un dado por arma pesada/misil para erradicar colonizadores y edificios (Population y Buildings), pudiendo dejar el planeta vacío o transformarlo a *Barren/Radiated* si se excede.
* **Frontend (`ColonyView.vue` / `CombatResult.vue`):**
  * Indicador de contaminación visual en la grilla industrial.
  * Botón de `"Bombardear"` en la interfaz de flota atacante.

## 6. Sistema de Razas Customizables (Race Design)
**Objetivo:** Permitir que los jugadores diseñen razas personalizadas con sistema de puntos (picks).

* **Backend (`game_repo.py` / `leader_service.py`):**
  * Crear la tabla/schema `race_customization` con campos: `race_id`, `traits`, `picks_used`, `picks_max` (10 por defecto), `government_type`.
  * Implementar validación de picks: Un rasgo ventajoso (advantage) reduce picks disponibles, una desventaja (disadvantage) aumenta picks. Máximo 10 picks de desventajas.
  * Rasgos disponibles en categorías: Farming, Industry, Research, Population Growth, Money, Space Combat, Espionage, Ground Combat.
  * Cada rasgo tiene propiedades booleanas (o modificadores numéricos): `farming_bonus`, `industry_bonus`, `research_bonus`, `population_growth_bonus`, `money_bonus`, `combat_bonus`, `espionage_bonus`, `ground_combat_bonus`.
  * Habilidades especiales (Special Abilities): Telepathic, Lithovore, Subterranean, Aquatic, etc., con efectos globales en la raza.
* **Frontend (`DashboardView.vue` / Nueva vista `RaceDesigner.vue`):**
  * Interfaz interactiva de diseño de razas con selector de traits y visualización de picks en tiempo real.
  * Resumen visual: "Picks Used: 8/10", con advertencia si se excede.
  * Panel de previsualización con todas las bonificaciones/penalizaciones de la raza diseñada.

## 7. Sistema de Gobiernos
**Objetivo:** Cada imperio elige una forma de gobierno que determina ventajas, desventajas y costos de picks.

* **Backend (`game_repo.py` / `game_service.py`):**
  * Crear tabla `government_types` con: `name`, `picks_cost`, `research_bonus`, `wealth_bonus`, `farming_bonus`, `industry_bonus`, `construction_cost_reduction`, `espionage_vulnerability`, `spy_efficiency`, `assimilation_rate`, `assimilation_cooldown`.
  * **Dictadura** (0 picks): Bonificadores menores, es la base.
  * **Democracia** (alto costo de picks): +Major research, +Major wealth, pero -Defense vs espionage, -Cannot annihilate conquered aliens, +Fastest assimilation rate.
  * **Unificación/Unification** (costo moderado): +Farming, +Industrial output, +Defense vs espionage, -No morale benefit, -Slowest assimilation rate.
  * **Feudalismo** (costo significativo): -Large reduction in spaceship construction costs, pero -Very slow research.
  * Los gobiernos pueden investigarse y mejorarse (upgrade) con tecnología.
* **Frontend (`Dashboard.vue` / `LeadersView.vue`):**
  * Mostrar el tipo de gobierno actual con sus bonificaciones/penalizaciones.
  * Sección de actualización de gobierno si la tecnología está disponible.

## 8. Sistemas Estelares Multi-Planeta y Viajes Interestelares
**Objetivo:** Sistemas con múltiples planetas colonizables y viajes sin restricciones de wormholes.

* **Backend (`game_repo.py` / `game_service.py`):**
  * Modificar schema de sistemas para permitir `planets: [...]` array con hasta 5 planetas colonizables por sistema.
  * Añadir lógica de generación: Algunos sistemas tienen 0 planetas, otros 1-5.
  * Gas Giants y Asteroids pueden hacerse habitables con tecnología "Planet Construction".
  * **Viajes Interestelares:** Las naves pueden viajar a cualquier sistema dentro de su rango (`ship.range`), sin restricción de wormholes. Modificadores de tecnología aumentan rango y velocidad de forma global.
  * Los "space monsters" guardan sistemas deseables pero son más débiles que el Orion Guardian.
* **Frontend (`GalaxyMap.vue` / `SystemView.vue`):**
  * Visualizar múltiples planetas por sistema.
  * Mostrar indicador de rango de viaje en las naves seleccionadas.
  * Mostrar advertencia de "Space Monster" en sistemas guarnecidos.

## 9. Investigación y Árbol de Tecnologías
**Objetivo:** Sistema de 8 áreas de investigación con niveles progresivos.

* **Backend (`ai_service.py` / `services/`):**
  * Crear tabla `technologies` con campos: `id`, `name`, `research_area` (1-8), `level`, `research_cost`, `prerequisites`, `effects`.
  * **8 Áreas de Investigación**: (definidas según MOO2 estándar: Biology, Physics, Sociology, Ecology, Metallurgy, Computers, Force Fields, Astronomy).
  * Cada área tiene múltiples niveles; cada nivel contiene 1-4 tecnologías.
  * Antes de investigar un tech de nivel N+1, debe completarse nivel N.
  * Adquisición alternativa de tecnologías: Intercambio diplomático, espionaje, contratación de líderes con conocimiento, conquista de planetas (reverse engineering), eventos aleatorios, derelicts orbiting newly discovered planets.
  * **Miniaturización:** Avances en ciertos techs reducen tamaño y costo de producción de armas y componentes.
  * **Modificaciones de Armas:** Techs adicionales pueden modificar armas (mayor coste/tamaño pero mayor efectividad).
* **Frontend (`TechTree.vue` / `Dashboard.vue`):**
  * Árbol visual de tecnologías con dependencias.
  * Panel de investigación actual y progreso (ej: "Physics Level 3: 45% complete").
  * Botón de cambio de investigación activa (cola de tamaño 1 por ahora, extensible).

## 10. Líderes (Leaders)
**Objetivo:** Contratar líderes coloniales y navales para mejorar performance.

* **Backend (`leader_service.py` / `game_service.py`):**
  * Crear tabla `leaders` con campos: `id`, `name`, `type` (Colony/Ship), `skills`, `cost`, `salary`, `faction_id`, `system_id` (si es asignado), `fleet_id` (si está asignado).
  * **Líderes Coloniales:** Mejoran farming/industry/research/money de una colonia o sistema. Algunos especiales: Espionage Defenders, Offensive Spies.
  * **Líderes Navales:** Mejoran combat effectiveness de flota, velocidad de viaje. Algunos: Commando skill (mejora combate terrestre).
  * Sistema de "Hiring Events": De vez en cuando, aparecer oportunidad de contratar líder aleatorio (costo de contratación + salario anual).
  * Algunos líderes atraen otros líderes con descuento en fee.
  * Random leader pool generado con variables: nivel de tech, performance del imperio, dificultad.
* **Frontend (`LeadersView.vue` / `ColonyView.vue` / `FleetManager.vue`):**
  * Pantalla de gestión de líderes con filtrado por tipo.
  * Botón de "Hire Leader" con modal mostrando disponibles y sus stats.
  * Visualización en colonias y flotas del líder asignado y sus efectos.

## 11. Eventos Aleatorios
**Objetivo:** Inyectar oportunidades, desastres y emergencias en el juego.

* **Backend (`game_service.py` / motor de turnos):**
  * Crear tabla `random_events` con tipos: Lucky Breaks, Disasters, Emergencies.
  * Generar evento al azar al inicio de cada turno (probabilidad configurable, desactivable en Game Setup).
  * Eventos pueden afectar: colonias (produce bonus/malus de resources), flotas (damage/repair/speed), imperio (tech gain/loss, morale boost/penalty).
  * Ejemplo de eventos: "Ancient Artifact discovered", "Solar Flare", "Plague Outbreak", "Spy Discovered", etc.
* **Frontend (`Dashboard.vue` / `GameView.vue`):**
  * Notificación visual/sonora al inicio del turno si hay evento.
  * Modal con descripción del evento y sus efectos.

## 12. Diplomacia
**Objetivo:** Negociaciones, tratados y relaciones interplanetarias.

* **Backend (`diplomacy_service.py`):**
  * Endpoints para: gift money, gift technology, gift entire star system colonies, demand concessions, technology trades.
  * Tratados: Trade Routes, Non-Aggression Pacts, Alliance.
  * Seguimiento de relaciones: `faction_relations` tabla con fields `faction_a`, `faction_b`, `relationship_level`, `active_treaties`, `treaties_history`.
  * Sistema de votos para elección de líder supremo: 2/3 de votos requeridos; votos basados en población controlada.
  * **Espionaje y Sabotaje:** Asignar espías a tareas defensivas o ofensivas. Espías defensivos detectan sabotaje enemigo.
* **Frontend (`DiplomacyView.vue`):**
  * "Races" button -> Pantalla de relaciones mostrando: tech progress de enemigos, relaciones diplomáticas, tratados activos.
  * Panel de espionaje: Sliders para asignar espías entre defensa/ofensiva.
  * Interfaz de negociación con otros imperios: Offers y Demands.

## 13. Diseño de Naves
**Objetivo:** Permitir que jugadores diseñen warships personalizadas (si se elige "tactical combat").

* **Backend (`combat_service.py` / `game_service.py`):**
  * 5 slots de diseño de warship.
  * Diseños fijos para: Colony Ships, Outpost Ships, Troop Transports.
  * Estos 3 tipos de transporte son destruidos instantáneamente por cualquier combatant si viajan desescoltados.
  * **Alcance y Velocidad Global:** Techs pueden mejorar rango y velocidad de TODAS las naves del imperio sin costo.
  * **Retrofitting:** Warships pueden ser refitados por costo para aprovechar mejoras techs no disponibles en upgrade global.
  * Selección de armas, shields, engines, módulos especiales para cada diseño.
* **Frontend (`FleetManager.vue` / Nueva vista `ShipDesigner.vue`):**
  * Interfaz drag-and-drop para seleccionar componentes.
  * Visualización en tiempo real de stats: costo, tamaño, poder de combate.
  * Historial de diseños guardados.

## 14. Sistema de Construcción en Cola y Gestión de Colonias
**Objetivo:** Permitir queue de construcción y control granular de output colonial.

* **Backend (`colony_service.py`):**
  * Cola de construcción: Hasta 7 items pueden queued en una colonia.
  * Cambio de output colonial: Desplazar colonos entre Farmers, Workers, Scientists.
  * **Impuestos:** Todos los colonos pagan tax estándar al tesoro. Tax imperial adicional configurable reduce output industrial.
  * Acelerar producción industrial con dinero (pero NO agricultura ni research).
  * Mantenimiento de edificios y flotas cuesta dinero.
  * **Bloqueos/Hambruna:** Un warship enemigo puede bloquear sistema entero, previniendo entrega de comida y reduciendo 50% farming/industry outputs.
* **Frontend (`ColonyView.vue` / `Dashboard.vue`):**
  * Pantalla de colonias: Acceso a Build screen de cualquier colonia.
  * Sliders para redistribuir colonos (Farmers/Workers/Scientists).
  * Queue visual de construcción.
  * Indicador de mantenimiento/dinero necesario.
  * Alertas de hambruna inminente.

## 15. Combate Táctico y Asalto Planetario
**Objetivo:** Combate espacial avanzado con invasión terrestre e invasión de IA.

* **Backend (`combat_service.py`):**
  * Combate espacial ocurre SOLO dentro de sistemas estelares (sobre planeta atacado o en afueras si se defiende bloqueador).
  * Defensores con warships y colonias se defienden automáticamente.
  * Colonias tomadas SOLO después destruir defensas orbitales Y naves defensoras.
  * **Mind Control:** Razas telepáticas pueden capturar colonia psíquicamente (a menos que defensores también tengan telepaths).
  * **Invasión Terrestre:** Atacante debe incluir Troop Transports. Se pierden si invasión falla, 1+ permanece si éxito.
  * Resultado depende de: números, tech de combate terrestre, bonificadores raciales, líderes con skill Commando.
  * Colonias conquistas por telepaths son instamente loyal. No-telepaths: colonias disconformes, baja producción, riesgo de rebelión.
  * **Destrucción Planetaria:** Alternativa a invasión: destruir colonia directamente por varios medios.
* **Frontend (`CombatResult.vue` / `GalaxyMap.vue`):**
  * Animaciones de combate (si tactical combat habilitado).
  * Botones post-combate: Mind Control (si aplica), Invade, Bombard, Retreat.
  * Reportes detallados de resultado y daños.

## 16. Reportes de Turno y Sistema de Turnos
**Objetivo:** Resumen automático de eventos y cambios cada turno.

* **Backend (Motor de Turnos):**
  * Al inicio de cada turno, compilar reporte con: 
    * Items completados en construcción (links a Build screen de colonia).
    * Eventos especiales ocurridos.
    * Cambios en relaciones diplomáticas.
    * Compleción de investigaciones.
    * Oportunidades de contratar líderes.
    * Avistamientos de space monsters u anomalías.
  * Reporte persistente en BD para histórico.
* **Frontend (`Dashboard.vue` / Nueva vista `TurnReportView.vue`):**
  * Mostrar reporte de turno con items clickeables.
  * Navbar con botón "Next Turn" que valida estado antes de aceptar.
  * Histórico de reportes accesible.

## 17. Rutas de Victoria
**Objetivo:** Tres caminos para ganar el juego.

* **Backend (`game_service.py` / resolución de victoria):**
  * **Ruta 1 - Conquista Militar:** Conquistar todos los imperios enemigos (aniquilación o asimilación total).
  * **Ruta 2 - Elección Diplomática:** Ganar elección de Supremo Líder de la Galaxia. Requiere 2/3 de votos totales. Votos = Población controlada de cada imperio.
  * **Ruta 3 - Ataque Antaran:** Localizar Dimensional Portal, viajar al Antaran Homeworld y conquistarlo.
    * Conquista del Sistema Orion NO otorga victoria automática pero sí proporciona Avenger Starship poderoso y múltiples tech Antaran no-investigables que facilitan victoria.
  * Sistema de chequeo de victoria al final de cada turno.
  * Modo singleplayer vs multiplayer (hasta 8 jugadores).
* **Frontend (`GameView.vue` / `Dashboard.vue`):**
  * Progreso visual hacia cada ruta de victoria.
  * Indicador de votos para elección.
  * Alerta cuando Dimensional Portal se descubre.
  * Pantalla de fin de juego con razón de victoria.
