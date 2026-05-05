# Plan de Implementación de Diplomacia Avanzada (MOO2)

Este documento detalla las modificaciones y adiciones necesarias en el backend (Flask) y frontend (Vue 3) del proyecto para dar soporte a las mecánicas avanzadas de diplomacia descritas en el diseño de Master of Orion II.

## 1. Sistema de Contacto ("First Contact")
**Objetivo:** Las facciones no se conocen automáticamente desde el inicio; la diplomacia solo se habilita cuando los dominios y rangos navales se cruzan.

* **Backend (`diplomacy_service.py` / `game_service.py`):**
  * Eliminar la creación automática de relaciones de `initialize_diplomacy()`.
  * Añadir lógica en el motor de turnos o movimientos: al colonizar, construir un Outpost o descubrir tecnología de celdas de combustible, calcular si el rango de salto sin tanques extendidos llega al territorio de otra facción. Si es así, disparar el evento "First Contact".
  * Si una facción pierde todas sus colonias/outposts en un rango, se puede perder el contacto.
* **Frontend (`DiplomacyView.vue` / `Dashboard.vue`):**
  * Pop-up de evento especial "Primer Contacto" con la cara del líder de la nueva raza.
  * La lista de diplomacia solo debe mostrar razas conocidas.

## 2. Interfaz de Diálogo, Paciencia y Personalidad IA
**Objetivo:** El jugador interactúa de forma más dinámica con la IA, la cual puede enfadarse si se abusa de la diplomacia.

* **Backend (`ai_service.py` / `diplomacy_service.py`):**
  * Integrar las personalidades de la IA (`aggressive.txt`, `balanced.txt`, etc., en `ai-service/app/prompts/personality/`) a las decisiones de aceptar/rechazar tratados.
  * Añadir en el objeto de relación un campo `patience` o `pester_penalty`. Esto aumenta si el jugador abre diálogo y no hace nada, o repite la misma oferta rechazada múltiples veces. Si la paciencia se agota, la IA se niega a hablar por X turnos.
* **Frontend (`DiplomacyView.vue`):**
  * Mostrar el "Mood" (Estado de ánimo) o texto de bienvenida basado en la relación y la personalidad de la IA.
  * Bloquear u oscurecer opciones si la IA se niega a hablar.

## 3. Intercambio de Tecnología (Tech Trades)
**Objetivo:** Permitir el trueque de ciencia descubierta entre imperios para ponerse al día en el árbol tecnológico.

* **Backend (`diplomacy_service.py` / `game_service.py`):**
  * Crear ruta `POST /diplomacy/trade_tech`.
  * Lógica de valoración en la IA: La IA solo pondrá en oferta tecnologías cuyo valor ("tier") sea inferior o equitativo a la que están recibiendo a cambio.
  * Transferencia inmediata del tech al array de tecnologías aprendidas de cada imperio.
* **Frontend (`DiplomacyView.vue`):**
  * Ventana modal de intercambio: Mostrar "Nuestras tecnologías" vs "Tecnologías de ellos".
  * Sistema de selección y confirmación para formalizar el trueque.

## 4. Impacto Económico de Tratados (Comercio e Investigación)
**Objetivo:** Que los tratados causen pérdidas a corto plazo y ganancias a largo plazo según el tamaño de las naciones involucradas y su gobierno.

* **Backend (`game_service.py` / motor de turnos):**
  * Añadir propiedad `turn_started` a los tratados activos.
  * En la resolución de turno, calcular economía: Los primeros 5 turnos penalizan el BC (Créditos) en Research Treaties y disminuyen ganancia en Trade Treaties. (Excepción si la raza es "Fantastic Traders").
  * A partir del turno 5, el tratado genera BCs o Research Points (RPs) adicionales escalando por la población combinada de ambas facciones.
  * Democracias reciben un multiplicador multiplicativo del 50%. Servidumbre/Feudalismo penaliza RPs en 50%.
* **Frontend (`Dashboard.vue` / `TechTree.vue`):**
  * Reflejar los ingresos (y las pérdidas) puntuales procedentes de "Treaties" en el desglose financiero del Dashboard.

## 5. Tratados de Paz y Pactos de No-Agresión
**Objetivo:** Ceses de fuego temporal y relaciones pacíficas no atadas a una alianza militar total.

* **Backend (`diplomacy_service.py` / `combat_service.py`):**
  * **Tratado de Paz:** Forzar paz limitándolo a X turnos. Si cualquiera de los dos lados ataca una colonia enemiga antes del fin del treaty, se destruye la reputación "global" del ofensor (-Diplomatic Value masivo con TODAS las facciones). Los AI pueden pedir dinero o tech como extorsión al firmarlo.
  * **Pacto de No-Agresión:** Indefinido. Proporciona una bonificación incremental (por turno) a la relación pasiva (relation value). La entrada de naves armadas en espacio enemigo sin alianza tiene alta probabilidad de forzar una declaración de guerra automática por parte de la IA.
* **Frontend (`DiplomacyView.vue`):**
  * Indicador de duración restante en el Tratado de Paz.

## 6. Alianzas
**Objetivo:** Cooperación militar total, compartiendo logística naval pero forzando involucramiento en guerras.

* **Backend (`diplomacy_service.py` / `combat_service.py`):**
  * **Extensión de Rango:** Al resolver el rango de viaje en el grid de la galaxia, las colonias de un Imperio A aliado actúan como puntos de respostaje para el Imperio B, permitiendo viajes interplanetarios extremadamente largos a flotas conjuntas.
  * Obligación bélica: Si tu aliado entra en guerra y tú declinas unirte, se desencadena una penalización grave que seguramente rompa la alianza.
* **Frontend (`GalaxyMap.vue` / `DiplomacyView.vue`):**
  * Actualizar visualmente los nodos del alcance de las flotas pintando los de color aliado como válidos.
  * Pop-up de emergencia "Call to Arms!" exigiendo unirse a la guerra.

## 7. Ultimátums (Make Demand)
**Objetivo:** Permitir robar tecnologías, sistemas enteros o imponer impuestos (tributo) mediante extorsión y amenazas.

* **Backend (`diplomacy_service.py`):**
  * Crear endpoints de Demands: `demand_tech`, `demand_system`, `demand_tribute_5`, `demand_tribute_10`, `stop_spying`, `remove_fleet`.
  * Algoritmo de decisión de la IA (¿Tienen miedo o declararán la guerra?): Comparar el Poder de Flota atacante vs el defensor.
  * Lógica Tributos: Extraer obligatoriamente % del Gross Income (no del sobrante) al inicio de cada turno.
* **Frontend (`DiplomacyView.vue`):**
  * Menú de exigencias organizando entre "Leves" (solicitar paz con terceros), "Moderadas" (detener espionaje/retirar barco) y "Severas" (ceder sistema / 10% tributo).

## 8. Regalos (Make Gift)
**Objetivo:** Mejorar dramáticamente relaciones o "comprar" votos para el Consejo Galáctico.

* **Backend (`diplomacy_service.py`):**
  * Crear métodos para donar una suma de BCs, una tecnología libre u ofrecer servidumbre (5-10% del propio ingreso en beneficio del receptor).
  * Aplicar el modificador positivo consecuente (`rel['value'] += X`) según el valor del regalo depositado.
* **Frontend (`DiplomacyView.vue`):**
  * Interfaz de regalos dentro de las negociaciones, que envíe los datos pertinentes y reste los recursos confirmados inmediatamente.