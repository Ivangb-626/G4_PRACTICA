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


## 9. Sistema de Espionaje Avanzado
**Objetivo:** Recopilar información, sabotear enemigos y defender contra espías con riesgos y recompensas.


### Centro de Espionaje
* **Construcción:** Requiere tecnología "Xeno Relations"
* **Gestión:** Panel en UI con asignación de espías entre contraespionaje y misiones ofensivas
* **Entrenamiento:** Los espías se entrenan automáticamente con niveles 1-4


### Niveles de Espía
- **NIVEL 1 (Novato):** Riesgo detección 30-40%, Eficacia baja, Costo bajo
- **NIVEL 2 (Entrenado):** Riesgo detección 15-25%, Eficacia media, Costo medio
- **NIVEL 3 (Veterano):** Riesgo detección 5-15%, Eficacia alta, Costo alto
- **NIVEL 4 (Maestro):** Riesgo detección 1-5%, Eficacia muy alta, Costo muy alto


### Misiones de Espionaje Ofensivo
1. **SONDEO DE INFORMACIÓN:** Descubrir población/edificios de colonias (Riesgo bajo)
2. **ESPIONAJE TECNOLÓGICO:** Descubrir investigaciones en curso (Riesgo medio, 2-5 turnos)
3. **SABOTAJE ECONÓMICO:** Ralentizar producción (-15% a -30% por 3-8 turnos, Riesgo alto)
4. **SABOTAJE MILITAR:** Dañar infraestructura militar/naves (Riesgo muy alto)
5. **SABOTAJE CIENTÍFICO:** Ralentizar investigación (-20% a -40% por 4-10 turnos, Riesgo alto)
6. **ESPIONAJE POLÍTICO:** Descubrir estrategia y planes militares (Riesgo medio)


### Consecuencias de Espionaje
* **Detección:** Espía neutralizado, reputación -5 a -20 puntos
* **Éxito sin detección:** Información obtenida sin daño reputacional directo
* **Acusación diplomática:** Enemigo confronta con opciones: Admitir (-10 relaciones), Negar (-15 + desconfianza)


### Backend (`espionage_service.py`)
* Crear estructuras `Spy` y `SpyMission` en game_state
* Implementar cálculo de detectionRisk basado en nivel, contraespionaje enemigo y tipo de misión
* En resolución de turno: Chequeo de detección, aplicación de efectos (si éxito), actualización de relaciones
* Métodos para asignar/reasignar espías, evaluar riesgo, ejecutar misión


### Frontend (`EspionageView.vue`)
* Panel de gestión de espías con niveles, estados, misiones asignadas
* Selector de misión con estimación de riesgo/recompensa
* Historial de operaciones completadas/detectadas
* Indicador de espías enemigos sospechosos


## 10. Sistema de Reputación y Relaciones Detallado
**Objetivo:** Las acciones tienen consecuencias duraderas en las percepciones de otras facciones.


### Factores Positivos (+)
- Alianza activa: +2 por turno
- Tratado comercial: +1 por turno
- Paz establecida: +1 por turno
- Ayudar a aliado en guerra: +5-10 por batalla
- Regalo de dinero: +3-10 (según cantidad)
- Regalo de tecnología: +5-15 (según valor tech)
- Regalo de colonias: +10-20
- Voto en Consejo Galáctico: +5


### Factores Negativos (-)
- Rompimiento de tratado: -20-40
- Ataque a aliado: -30-50
- Espionaje detectado: -15-30
- Colocar espías fronterizos: -5-10 por turno (si detectado)
- No ayudar a aliado en guerra: -10-20
- Navíos en territorio ajeno: -2-5 por turno
- Voto en contra en Consejo: -5
- Sabotaje económico: -15-30
- Sabotaje militar: -30-50


### Escala de Relaciones (-100 a +200)
- **-100 a -51 (ENEMISTAD TOTAL):** Ataque automático, sin diplomacia
- **-50 a -1 (HOSTIL):** Posibilidad de ataque, demandas ofensivas
- **0 a 50 (NEUTRAL):** Negociaciones comerciales posibles
- **51 a 100 (AMISTOSO):** Alianzas y pactos posibles
- **101 a 150 (MUY AMISTOSO):** Alianzas garantizadas, defensa activa
- **151 a 200 (ALIADO LEAL):** Lealtad casi garantizada, sacrificio por ti


### Backend (`diplomacy_service.py`)
* Estructura `Relationship` con campos: relationValue, treaties[], status, lastContact, knownTechs[]
* Métodos de cálculo de modificadores (+/-) por cada evento diplomático
* Sistema de persistencia: Guardar y cargar relaciones en cada turno
* Evaluación de escala: Determinar status actual basado en relationValue


## 11. IA Diplomática Avanzada
**Objetivo:** IAs con personalidades predefinidas que toman decisiones estratégicas coherentes.


### Modelado de Personalidad IA
Rasgos configurables:
- **Agresividad:** Qué tan propenso a guerra
- **Codicia:** Interés en dinero/tecnología
- **Honor:** Probabilidad de romper tratados
- **Alianzas:** Preferencia por diplomacia vs guerra
- **Expansionismo:** Necesidad de territorio
- **Rivalidad:** Tendencia a hacer enemigos


### Modificadores por Raza
- **Carismáticos (Charismatic):** +30 a todas las relaciones diplomáticas, +20 a oportunidades de contratar líderes; las IA son más receptivas a sus propuestas.
- **Repulsivos (Repulsive):** Sin acceso a diplomacia estándar. Solo pueden proponer guerra o paz; ningún tratado, alianza, intercambio de tech ni regalo. Las IA los odian por defecto.
- **Telepáticos (Telepathic):** +20 a espionaje efectivo, +20 a diplomacia. Adicionalmente, son la única raza capaz de usar "Blitz Diplomático": capturar planetas sin invasión terrestre (Mind Control) y asimilar colonias conquistadas instantáneamente sin rebellion_timer, lo que elimina la necesidad de muchas negociaciones post-guerra.
- **Trans Dimensional:** Capacidad de salto mejorada; en diplomacia, alcanza primer contacto con más razas antes y facilita estrategias de blitz (expansión rápida antes de que el resto pueda negociar).
- **Omniscientes:** No necesitan espías para ver el estado interior de otros imperios; toda la información de scouting diplomático está disponible sin coste.
- **Comerciantes Fantásticos (Fantastic Traders):** +40% a todos los ingresos de tratados comerciales. Los primeros 5 turnos de penalización económica de los Trade Treaties no les aplican.


### Lógica de Decisión IA
**Cuando se propone un acuerdo:**
1. Evaluar posición relativa de poder
2. Calcular beneficio económico neto
3. Considerar relaciones actuales
4. Evaluar alianzas existentes
5. Aplicar rasgo de personalidad
6. Decidir: Aceptar/Rechazar/Contrapropuesta


**Cuando plantea un ataque:**
- Si fuerza militar > 1.5x del objetivo
- Y relación < -20 O aliado está bajo ataque
- Y beneficio territorial > costo militar
- → Declara guerra


**Cuando busca alianzas:**
- Si hay enemigo común más fuerte
- Y relación > 30
- → Propone alianza


### Estrategias de IA por Tipo
- **AGRESOR:** Expande conquista, rompe tratados si conviene
- **DIPLOMÁTICO:** Múltiples alianzas, victoria electoral
- **COMERCIANTE:** Tratados comerciales, máxima riqueza
- **EQUILIBRADOR:** Mantiene balance, alianzas estratégicas


### Backend (`ai_service.py` / `aiDecisionEngine.ts`)
* Cargar personalidad desde `prompts/personality/*.txt`
* Implementar árbol de decisión evaluando poder, relaciones, beneficio
* Método de contraofertas con términos mejorados
* Evaluación de promesas: ¿Cumple la IA sus compromisos? (según Honor)


## 12. Demandas Diplomáticas (Make Demand)
**Objetivo:** Permitir extorsión, tributos y robo de recursos mediante diplomacia agresiva.


### Tipos de Demandas
1. **DEMANDA DE DINERO:** "Dáme X créditos o guerra"
2. **DEMANDA DE TECNOLOGÍA:** "Dáme tech X o resulta malo"
3. **DEMANDA DE TERRITORIO:** "Cede sistema X o guerra"
4. **DEMANDA DE VOTO CONSEJO:** "Vota por mí en próxima elección"
5. **DEMANDA DE APOYO MILITAR:** "Únete en guerra contra X"


### Algoritmo de Decisión IA
Comparar Poder de Flota atacante vs defensor. Si defensor tiene 0.5x o menos, tiende a ceder. Si defensor tiene 2x o más, típicamente rechaza y puede contrar-atacar.


### Backend (`diplomacy_service.py`)
* Endpoints: `demand_tech`, `demand_system`, `demand_tribute`, `demand_military_support`
* Cálculo de poder de flota: Sum(ship_count * ship_attack_power) por imperio
* Obligación de tributos: Extraer % del Gross Income al inicio cada turno
* Lógica de ruptura: Incumplimiento de demanda puede forzar guerra


### Frontend (`DiplomacyView.vue`)
* Menú de demandas organizadas: Leves, Moderadas, Severas
* Indicadores de probabilidad de aceptación
* Confirmación antes de enviar demanda


## 13. Consejo Galáctico
**Objetivo:** Sistema electoral donde la diplomacia y los votos determinan un emperador galáctico.


### Sistema Electoral
- **Estructura:** Elecciones cada 20-30 turnos para Emperador Galáctico
- **Poder de voto:** Basado en población total del imperio (más colonias y colonos = más votos)
- **Victoria electoral:** Requiere 2/3 de los votos totales. Las abstenciones cuentan como votos en contra de AMBOS candidatos simultáneamente, por lo que no son neutrales — dificultan activamente que cualquiera alcance los 2/3.
- **Candidatos:** Todos los imperios pueden ser candidatos; si hay solo dos candidatos, un tercero que se abstiene perjudica a los dos por igual


### Estrategias
- Formar bloques de voto mediante alianzas
- Respaldar candidato fuerte como proxy
- Ofrecer dinero/tech por votos
- Bloquear candidatos rivales
- Crecer población para más votos


### Impacto en Diplomacia
- Elecciones crean tensión diplomática
- AIs buscan votos activamente
- Alianzas temporales solo para voto
- Rivalidades se intensifican


### Backend (`council_service.py`)
* Estructura `GalacticCouncil` con lista de candidatos, votos, periodo electoral
* Cálculo de votos por población / imperio
* Resolver elección: Candidato con 2/3 gana (Victoria alternativa)
* Eventos: "Call to Vote", promesas de aliados, cambios de lealtad


### Frontend (`CouncilVoting.vue`)
* Panel de candidatos con votos actuales/estimados
* Visualización de bloques de voto
* Negociación de votos mediante diplomacia


## 14. Diplomacia como Exploración (Diplomacy is Scouting)
**Objetivo:** Cada interacción diplomática revela información de inteligencia sobre el imperio contactado, convirtiendo la diplomacia en una herramienta de reconocimiento estratégico además de negociación.

* **Backend (`diplomacy_service.py` / `game_service.py`):**
  * Al abrir el diálogo diplomático con un imperio, revelar automáticamente un subconjunto de datos del enemigo según el nivel de relación:
    * **Relación Neutral o superior:** Revelar población total aproximada, lista de sistemas conocidos, tecnologías que ese imperio ha ofrecido en intercambios previos.
    * **Relación Amistosa o superior:** Revelar además el número y tipo general de naves en sus flotas, el nivel de investigación actual y qué áreas de tech están explorando.
    * **Alianza activa:** Visión compartida completa — colonias, flotas, investigación, relaciones con terceros.
  * La información se guarda en `faction_relations.knownTechs[]` y `faction_relations.lastScouted` para uso interno del jugador y de la IA.
  * **Límite de fiabilidad:** La información obtenida tiene una "antigüedad" (turns_since_scouted). Pasados 10 turnos sin nuevo contacto, los datos se marcan como "desactualizados" y pueden no reflejar la situación real.
  * **IA también usa esto:** La IA explotará la información que recibe del jugador al negociar; si el jugador es débil, la IA incrementará la agresividad de sus demandas.
* **Frontend (`DiplomacyView.vue` / `Dashboard.vue`):**
  * En la pantalla de diplomacia, sección "Inteligencia Conocida" con los datos descubiertos sobre cada facción con la que se ha tenido contacto.
  * Indicador de frescura de la información: icono verde (reciente, <5 turnos), amarillo (5-10 turnos), rojo (desactualizado, >10 turnos).
  * Tooltip en cada dato mostrando "Información del turno X" para que el jugador sepa cuándo fue obtenida.
  * Botón "Abrir Contacto" (aunque no haya intención de negociar) para refrescar datos de scouting.

## 15. Implementación Técnica Detallada


### Estructuras de Datos (TypeScript/Python)
```typescript
// RELACIONES DIPLOMÁTICAS
interface DiplomaticRelation {
  empireA: string;
  empireB: string;
  relationValue: number; // -100 to +200
  treaties: Treaty[];
  status: 'at_war' | 'peace' | 'allied' | 'neutral';
  lastContact: number; // turn
  knownTechs: string[];
  suspicions?: { empire: string; level: number }[];
}


// TRATADOS
interface Treaty {
  id: string;
  type: 'peace' | 'non_aggression' | 'alliance' | 'trade' | 'research';
  empires: [string, string];
  startTurn: number;
  endTurn?: number; // null = indefinido
  isActive: boolean;
  terms?: Record<string, unknown>;
}


// ESPÍAS
interface Spy {
  id: string;
  ownerEmpire: string;
  targetEmpire: string;
  level: 1 | 2 | 3 | 4;
  status: 'training' | 'active' | 'compromised' | 'dead';
  mission: 'defense' | 'intelligence' | 'sabotage' | null;
  missionType?: string;
  infiltrationTurns: number;
  detectionRisk: number; // 0-1
}


// REPUTACIÓN
interface Reputation {
  empire: string;
  observer: string;
  value: number;
  suspicions: { empire: string; level: number }[];
  breachHistory: { treaty: string; turn: number }[];
}
```


### Arquitectura de Módulos
```
/diplomacy
  ├─ /relations
  │  ├─ relationshipManager.ts
  │  ├─ relationshipCalculations.ts
  │  └─ relationshipEvents.ts
  │
  ├─ /treaties
  │  ├─ treatyManager.ts
  │  ├─ treatyTypes.ts
  │  └─ treatyValidation.ts
  │
  ├─ /espionage
  │  ├─ spyManager.ts
  │  ├─ missionExecutor.ts
  │  ├─ detectionSystem.ts
  │  └─ spyLevels.ts
  │
  ├─ /ai
  │  ├─ aiPersonality.ts
  │  ├─ aiDecisionEngine.ts
  │  ├─ aiStrategy.ts
  │  └─ aiNegotiation.ts
  │
  ├─ /council
  │  ├─ galacticCouncil.ts
  │  ├─ voteSystem.ts
  │  └─ electionLogic.ts
  │
  ├─ /scouting
  │  ├─ scoutingManager.ts
  │  ├─ intelligenceCache.ts
  │  └─ dataFreshness.ts
  │
  └─ /ui
     ├─ diplomacyScreen.tsx
     ├─ treatyNegotiation.tsx
     ├─ espionagePanel.tsx
     ├─ councilVoting.tsx
     └─ intelligencePanel.tsx
```


### Flujos Principales
**A. Inicio de Negociación:**
1. Jugador selecciona imperio y acción
2. Sistema valida contacto establecido
3. Abre diálogo de negociación
4. Muestra relación actual y opciones
5. Jugador propone acuerdo
6. IA evalúa y responde
7. Acuerdo se formaliza o rechaza
8. Efectos se aplican inmediatamente


**B. Misión de Espionaje:**
1. Jugador asigna espía a misión
2. Sistema verifica nivel y disponibilidad
3. Calcula riesgo de detección
4. Inicia temporizador de misión
5. Cada turno: chequeo de detección
6. Si detectado: Reacción IA
7. Si éxito: Obtener información
8. Fin de misión: Resultados


**C. Evaluación IA de Oferta:**
1. Recibir propuesta diplomática
2. Evaluar estado interno (poder, recursos, amenazas, objetivos)
3. Calcular valor de acuerdo (económico, militar, estratégico)
4. Aplicar personalidad IA (multiplicadores, sesgos)
5. Decidir: Aceptar/Rechazar/Contraoferta
6. Generar respuesta con justificación
7. Aplicar efectos a relaciones


## 16. Testing y Balance


### Casos de Prueba Críticos
- ✓ Contacto inicial entre imperios
- ✓ Proposición y aceptación de tratado
- ✓ Ruptura de tratado y consecuencias
- ✓ Espionaje exitoso sin detección
- ✓ Espionaje detectado y reacción
- ✓ Escalada de conflicto diplomático
- ✓ Resolución de Consejo Galáctico
- ✓ Victoria electoral vs. militar
- ✓ Múltiples alianzas simultáneas
- ✓ Conflicto entre aliados
- ✓ Sabotaje efectivo con limpieza
- ✓ Demandas rechazadas
- ✓ Contrapropuestas IA
- ✓ Scouting via diplomacia: datos revelados según nivel de relación
- ✓ Datos de inteligencia marcados como desactualizados tras 10 turnos sin contacto
- ✓ Raza Repulsiva: sin acceso a tratados ni regalos, solo guerra/paz
- ✓ Raza Telepática: Mind Control sin rebellion_timer en colonias capturadas
- ✓ Abstenciones en Consejo Galáctico perjudican a ambos candidatos
- ✓ Comerciante Fantástico: sin penalización en primeros 5 turnos de tratado comercial


### Métricas de Balance
- Frecuencia de guerras diplomáticas vs militares (30-40% diplomática ideal)
- Duración promedio de tratados (20-40 turnos)
- Éxito de espías por nivel (Nivel 1: 40%, Nivel 4: 80%)
- Distribución de victorias (militar/electoral/Antares)
- Longevidad de alianzas (promedio 30+ turnos)
- Impacto económico de tratados comerciales (+10-20% ingresos)


## 17. Consideraciones de Dificultad


### FÁCIL
- IA más dispuesta a tratados
- Demandas menos agresivas
- Espionaje IA menos efectivo (riesgo detección +15%)
- Oportunidades diplomáticas abundantes


### NORMAL
- IA actúa racionalmente
- Equilibrio entre guerra y paz
- Espionaje desafiante
- Oportunidades limitadas


### DIFÍCIL
- IA desconfía más
- Demandas frecuentes
- Espionaje IA muy efectivo (riesgo detección -15%)
- Alianzas raras (relación mín. +75)
- Enemigos coordenados


### IMPOSIBLE
- IA casi imposible de confiar (relación mín. +120)
- Diplomacia principalmente defensa
- Espionaje crítico
- Victoria debe ser militar o electoral pura


## 18. Próximos Pasos de Implementación


### Fase 1: Estructuras Base
- [ ] Implementar estructuras de datos (Relationship, Treaty, Spy, etc.)
- [ ] Persistencia entre turnos
- [ ] Carga/guardado de diplomacia en BD


### Fase 2: Sistema de Relaciones
- [ ] Cálculos de bonificación/penalización
- [ ] Escala de relaciones (mapeo de valores)
- [ ] UI básica de diplomacia


### Fase 3: Sistema de Espionaje
- [ ] Misiones y resultados
- [ ] Sistema de detección
- [ ] Panel de gestión de espías


### Fase 4: IA Diplomática
- [ ] Personalidades cargables
- [ ] Decisiones estratégicas
- [ ] Evaluación de ofertas


### Fase 5: Consejo Galáctico
- [ ] Sistema electoral
- [ ] Mecánica de votación
- [ ] Determinación de emperador


### Fase 6: Scouting Diplomático
- [ ] Implementar revelación de datos por nivel de relación
- [ ] Sistema de caducidad de inteligencia (turns_since_scouted)
- [ ] Panel de Inteligencia en DiplomacyView
- [ ] Lógica IA para explotar info del jugador en negociaciones

### Fase 7: Testing y Balanceo
- [ ] Juegos de prueba completos
- [ ] Ajustes de dificultad
- [ ] Optimización de fórmulas

