# Plan de Mejoras y Correcciones - MasterDeHostias

Este documento detalla las tareas pendientes y errores detectados durante la auditoría de QA para alcanzar un estado de producción estable.

## 1. Errores Críticos (Prioridad Máxima) 🚨

- [ ] **Corrección del borrado de flotas**: Modificar `resolve_space_combats` en `game_service.py` para que las naves restantes se distribuyan entre las flotas originales en lugar de consolidarlas en una sola y borrar las demás.
- [ ] **Arreglo de lectura de población en IA**: Corregir `_summarize_state` en `ai-service/ai/strategic.py` para acceder a la población mediante `c["population"]["farmers"]`, etc.
- [ ] **Metadatos de Tecnología Robada**: Actualizar `espionage_service.py` para que al robar una tecnología se hereden correctamente los campos `field` y `level` de la definición original en `technologies.json`.

## 2. Gameplay y Mecánicas Core 🎮

- [ ] **Implementar Bloqueo Planetario**: Añadir validación en `colonize_planet` y `ground_assault` para impedir acciones si hay flotas hostiles en el sistema.
- [ ] **Acarreo de Producción (Overflow)**: Modificar `process_colony_construction` en `colony_service.py` para que el exceso de producción de un turno se aplique al siguiente objeto en la cola.
- [ ] **Escalado de Penalización por Clima**: Cambiar el cálculo de comida para que la penalización por clima sea por cada agricultor (`farmers * (base + mod)`) en lugar de un valor plano por colonia.
- [ ] **Validación de Diseños de Naves**: Añadir comprobaciones en el backend para asegurar que los diseños de naves no excedan el espacio disponible del casco y que los costes sean positivos.

## 3. IA y Diplomacia 🤖

- [ ] **Optimización de Llamadas a IA**: Implementar un sistema de timeout o procesamiento asíncrono real para las decisiones de la IA, evitando bloquear el hilo principal del backend.
- [ ] **Mejora de Reglas Deterministas**: Ampliar el fallback `_rule_based_turn` para que la IA sea competitiva incluso si el LLM no responde (gestión de flotas básica, expansión).
- [ ] **IA de Combate Táctico**: Desarrollar la lógica en `ai-service/ai/tactical.py` para que la IA tome decisiones de movimiento y ataque coherentes en lugar de simples esperas.

## 4. UI/UX y Experiencia de Usuario ✨

- [ ] **Cálculo Reactivo de Recursos**: Añadir lógica en `ColonyView.vue` para previsualizar el impacto de los cambios de población en la producción antes de pulsar "Aplicar".
- [ ] **Sistema de Notificaciones Detallado**: Mejorar el feed de eventos para que incluya detalles sobre qué edificio se construyó, qué tecnología se terminó o los resultados numéricos del combate.
- [ ] **Tooltips y Descripciones**: Asegurar que todos los edificios y componentes de naves tengan descripciones claras en la UI, extrayendo la información de los archivos de datos JSON.
- [ ] **Confirmación de Acciones Críticas**: Añadir modales de confirmación para acciones como desguazar naves o abandonar colonias.

## 5. Economía y Balance ⚖️

- [ ] **Revisión de Costes de Mantenimiento**: Ajustar el mantenimiento de edificios y naves para evitar que el jugador entre en bancarrota inevitable en el mid-game.
- [ ] **Equilibrio de Traits Raciales**: Revisar los bonus de razas como los Silicoid (Lithovore) o los Psilons para asegurar que no sean excesivamente superiores a las demás.

## 6. Seguridad y Estabilidad 🛡️

- [ ] **Protección de Endpoints de Cheats**: Implementar una comprobación de permisos o una flag de configuración para habilitar/deshabilitar los cheats en producción.
- [ ] **Manejo de Errores Robusto**: Añadir try/except en los pasos críticos del `end_turn` para que un fallo en un módulo (ej. espionaje) no detenga el avance del turno de todo el juego.

---
*Documento generado automáticamente por el asistente de QA.*
