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
