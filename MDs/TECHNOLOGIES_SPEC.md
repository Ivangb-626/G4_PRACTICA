# Master of Orion II: Sistema de Tecnologías
## Especificación de Implementación Técnica

---

## 📋 Tabla de Contenidos
1. [Visión General](#visión-general)
2. [Estructura del Árbol de Tecnologías](#estructura-del-árbol-de-tecnologías)
3. [8 Ramas Principales](#8-ramas-principales)
4. [Sistema de Investigación](#sistema-de-investigación)
5. [Características Especiales](#características-especiales)
6. [Modificaciones de Armas](#modificaciones-de-armas)
7. [Miniaturización](#miniaturización)
8. [Ruta de Investigación Recomendada](#ruta-de-investigación-recomendada)
9. [Implementación Técnica](#implementación-técnica)

---

## Visión General

La tecnología es el alma de la dominación imperial en Master of Orion II. Aunque tener la tecnología correcta no gana guerras automáticamente, proporciona una ventaja increíble sobre la oposición.

### Principios Clave

Una nave de guerra de alta tecnología puede vencer fácilmente 2 naves de menor tecnología, y un imperio avanzado puede superar económicamente, agrícola y científicamente a un imperio más grande pero tecnológicamente inferior.

### Tres Categorías de Tecnología

```
1. TECNOLOGÍAS COLONIALES
   └─ Estructuras para planetas
   └─ Mejoran producción, defensa, población
   └─ Efectos inmediatos en colonias

2. TECNOLOGÍAS NAVALES
   └─ Armas, escudos, motores
   └─ Módulos para naves
   └─ Mejoran capacidad combativa

3. LOGROS TECNOLÓGICOS (Achievements)
   └─ Bonificaciones globales del imperio
   └─ Se aplican inmediatamente al descubrir
   └─ Benefician múltiples aspectos del juego
```

---

## Estructura del Árbol de Tecnologías

### Organización General

El árbol de tecnologías consiste en 8 ramas sin interdependencias entre ellas. En teoría podrías investigar completamente una rama y negleger el resto, pero eso sería casi siempre suicida.

```
ÁRBOL DE TECNOLOGÍAS (8 RAMAS)
│
├─ Engineering (Ingeniería)
├─ Power (Potencia)
├─ Chemistry (Química)
├─ Sociology (Sociología)
├─ Computers (Computadoras)
├─ Biology (Biología)
├─ Physics (Física)
└─ Force Fields (Campos de Fuerza)
```

### Niveles de Tecnología

```
ESTRUCTURA POR NIVEL:
├─ Nivel 0 (Starter): Tecnologías iniciales gratuitas
├─ Nivel 1-7: Tecnologías tempranas (costo bajo-medio)
├─ Nivel 8-12: Tecnologías mid-game (costo medio)
├─ Nivel 13-20: Tecnologías avanzadas (costo alto)
└─ Hiperavanzadas: Tecnologías finales (costo muy alto)

COSTO ACUMULATIVO:
├─ Cada nivel requiere suma de RP acumulados
├─ Ej: Para llegar a nivel 5, necesitas RPs de 1+2+3+4+5
├─ Los niveles posteriores son exponencialmente más caros
└─ Planificación estratégica es CRÍTICA
```

### Disponibilidad Aleatoria de Tecnologías

Las tecnologías no son siempre las mismas. El juego genera aleatoriamente cuáles tecnologías están disponibles. Hay un número que siempre está disponible, pero aproximadamente la mitad de las tecnologías son seleccionadas aleatoriamente, dejando al jugador con el resto.

```
MECÁNICA DE GENERACIÓN:
├─ ~50% de probabilidad que cada tech exista
├─ El juego asegura que nunca quedes sin opciones
├─ Si solo quedan techs nivel 8+ sin nivel 1-7, las genera
├─ Redundancia integrada en el sistema
└─ Permite múltiples rutas hacia objetivos

PARA CREATIVES:
├─ Excepción: AMs reciben más opciones en sus ramas
├─ Pueden acceder a más variedad de tecnologías
└─ Ventaja estratégica desde el inicio
```

---

## 8 Ramas Principales

### 1. ENGINEERING (Ingeniería)

**Propósito:** Construcción de naves y estructuras avanzadas

#### Tecnologías Clave

```
NIVEL 1: Advanced Engineering
├─ Mejora de construcción básica
└─ Prepara para naves mejoradas

NIVEL 3: Advanced Construction
├─ Permite construcción rápida
├─ Base para estructuras especiales
└─ Mejora velocidad de producción

NIVEL 5: Astro Engineering
├─ Puertos espaciales
├─ Mejora docking y flota
└─ Aumenta capacidad de construcción naval

NIVEL 8: Advanced Manufacturing
├─ Automatización de producción
├─ Androides de producción disponibles
└─ +3 puntos de producción por androide

NIVEL 13: Superscalar Construction
├─ Construcción mega-estructuras
├─ Permite Doom Stars
└─ Máxima capacidad constructiva

NIVEL 20: Planetoid Construction
├─ Construcciones en asteroides
└─ Expande opciones de construcción
```

#### Bonificaciones Globales

```
- Velocidad general de construcción: +15% por nivel
- Eficiencia de astilleros: +10% por nivel
- Capacidad de flotas espaciales: +1 por nivel
```

---

### 2. POWER (Potencia)

**Propósito:** Sistemas de propulsión y energía

#### Tecnologías Clave

```
NIVEL 2: Deuterium Fuel Cells
├─ Aumenta rango de naves
├─ Primero de combustibles
└─ Crítico para expansión temprana

NIVEL 5: Deuterium Fuel Cells (mejorado)
├─ Mayor rango de exploración
└─ Imprescindible para temprana exploración

NIVEL 8: Fusion Drives
├─ Velocidad de viaje mejorada
├─ Viajes más rápidos
└─ Defensa mejorada de colonias

NIVEL 12: Anti-Matter Drive
├─ Velocidad máxima de viaje
├─ +50% velocidad de despliegue
└─ Decisivo en guerras tardías

NIVEL 18: Annihilation Drive
├─ Máxima potencia
├─ Viajes ultra-rápidos
└─ Punto final de línea de propulsión
```

#### Impacto en Juego

```
- Rango de naves: Afecta exploración y alcance táctico
- Velocidad de viaje: Crítica para invasiones y defensa
- Movilidad: Fundamental para maniobras de batalla
```

---

### 3. CHEMISTRY (Química)

**Propósito:** Misiles, armaduras y mejoras coloniales

#### Tecnologías de Armas

```
NIVEL 2: Nuclear Missile
├─ Primer arma de misil
├─ Daño base: 40-50 puntos
├─ Puede ser modificada

NIVEL 4: Merculite Missile
├─ Misil mejorado
├─ Daño: 60-70 puntos
└─ MIRV-able en niveles posteriores

NIVEL 8: Hellfire Missile
├─ Misil de fuego
├─ Daño: 100+ puntos
└─ Muy efectivo contra armaduras

NIVEL 13: Zortium Bomb
├─ Arma de bomba
├─ Daño: 150+ puntos
└─ Muy efectivo contra múltiples objetivos
```

#### Tecnologías de Armadura

```
NIVEL 2: Titanium Armor
├─ Primera armadura
├─ Bloquea 2 puntos/impacto
└─ Mejora defensa básica

NIVEL 5: Tritanium Armor
├─ Armadura mejorada
├─ Bloquea 5 puntos/impacto
└─ Estándar temprano-medio

NIVEL 10: Zortium Armor
├─ Armadura pesada
├─ Bloquea 10 puntos/impacto
└─ Mejor defensa disponible

NIVEL 18: Neutronium Armor
├─ Armadura final
├─ Bloquea 15 puntos/impacto
└─ Máxima protección
```

#### Tecnologías Coloniales

```
NIVEL 3: Soil Enrichment
├─ Mejora producción de alimentos
├─ +1 alimento por trabajador
└─ Crítica para crecimiento

NIVEL 6: Clone Center
├─ Crecimiento automático de población
├─ +3 población por turno
└─ Alternativa a Soil Enrichment

NIVEL 10: Pollution Processor
├─ Reduce contaminación
├─ -30% contaminación global
└─ Mejora viabilidad de colonias

NIVEL 18: Terraforming
├─ Modifica terreno planetario
└─ Permite colonización de cualquier planeta
```

---

### 4. SOCIOLOGY (Sociología)

**Propósito:** Gobernanza, liderazgo y morale

#### Tecnologías Clave

```
NIVEL 1: Constitution
├─ Forma de gobierno base
├─ Mejora estabilidad
└─ Bonificaciones según tipo

NIVEL 3: Space Academy
├─ Entrena tripulaciones navales
├─ Naves comienzan +1 nivel experiencia
├─ Ganan +1 experiencia por turno en sistema
└─ Crítica para superioridad combativa

NIVEL 6: Banking
├─ Genera ingresos adicionales
├─ +15% ingresos por turno
└─ Mejora economía

NIVEL 10: Democracy
├─ Forma de gobierno
├─ Bonificaciones sociales y económicas
├─ Penalizaciones en seguridad
└─ Votación en políticas internas

NIVEL 18: Advanced Government
├─ Gobernanza final
├─ Bonificaciones máximas
└─ Mantiene población feliz
```

#### Impacto en Juego

```
- Morale: Afecta producción y lealtad
- Liderazgo: Permite hiring de mejores líderes
- Estabilidad: Evita rebeliones
- Ingresos: Bonus económico directo
```

---

### 5. COMPUTERS (Computadoras)

**Propósito:** Sistemas de combate, defensa y espionaje

#### Tecnologías de Combate

```
NIVEL 2: Battle Computer Mark III
├─ Computadora de batalla temprana
├─ +20 al hit de armas de rayo
├─ Mejora acuratez

NIVEL 5: Battle Computer Mark V
├─ Computadora mejorada
├─ +50 al hit
└─ Estándar temprano-medio

NIVEL 10: Battle Computer Mark IX
├─ Computadora avanzada
├─ +80 al hit
└─ Mejora sustancial

NIVEL 18: Battle Computer Mark XI
├─ Computadora final
├─ +100 al hit
└─ Máxima acuratez de rayos
```

#### Tecnologías ECM

```
NIVEL 3: ECM Jammer Mark I
├─ Jamming de misiles
├─ -20% acuratez misiles enemigos
└─ Defensa contra cohetes

NIVEL 8: ECM Jammer Mark III
├─ Jamming mejorado
├─ -50% acuratez misiles enemigos
└─ Fuerte defensa contra misiles

NIVEL 15: ECM Jammer Mark V
├─ Jamming avanzado
├─ -80% acuratez misiles enemigos
└─ Defensa excepcional contra misiles
```

#### Tecnologías Especiales

```
NIVEL 7: Tachyon Communications
├─ Comunicaciones mejoradas
├─ +1 punto de comando por starbase
├─ Permite más naves en flota

NIVEL 12: Tachyon Scanner
├─ Scaneo avanzado
├─ Rango de detección: 8 parsecs + 1 por clase
├─ Reduce evasión de misiles -70%
└─ Crítica para visibilidad

NIVEL 15: Cyber Security Link
├─ Defensa contra espionaje
├─ +10 contra ciberespías
└─ Protege información
```

#### Androides Especiales

```
NIVEL 8: Android Workers
├─ Trabajadores robóticos
├─ +3 producción vs colonistas normales
└─ No afectados por morale

NIVEL 12: Android Scientists
├─ Científicos robóticos
├─ +3 investigación vs colonistas
└─ Generan RP constantemente
```

---

### 6. BIOLOGY (Biología)

**Propósito:** Mejoras genéticas y biológicas

#### Tecnologías Coloniales

```
NIVEL 2: Genetic Engineering
├─ Ingeniería genética temprana
├─ Mejora reproducción
└─ Base para posteriores

NIVEL 5: Advanced Biology
├─ Biología mejorada
├─ +1 población por turno
├─ Soil Enrichment alternativo
└─ Cloning Center alternativo

NIVEL 10: Genetic Enhancement
├─ Mejora genética avanzada
├─ Inteligencia mejorada
├─ +1 RP por científico
└─ Mejora capacidad mental

NIVEL 18: Evolutionary Genetics
├─ Genética final
├─ Heightened Intelligence achievement
├─ +2 RP por científico
└─ Máxima mejora biológica
```

#### Logros Biológicos

```
HEIGHTENED INTELLIGENCE
├─ Efecto: +2 RP por científico trabajando
├─ Mejora investigación global
└─ Clave para victoria científica

GENETIC ENHANCEMENT
├─ Efecto: Población más eficiente
├─ Mejora resistencia a enfermedades
└─ Extensión de vida
```

---

### 7. PHYSICS (Física)

**Propósito:** Armas de rayo y sistemas especiales

#### Tecnologías de Rayos

```
NIVEL 1: Laser Cannon
├─ Primer rayo láser
├─ Daño: 3 puntos
├─ Sin disipación por rango
└─ Base para posteriores

NIVEL 3: Fusion Beam
├─ Rayo de fusión
├─ Daño: 6 puntos
├─ Disipación normal
└─ Mejora sobre láser

NIVEL 6: Photon Torpedo
├─ Torpedo de fotones
├─ Daño: 12 puntos
└─ Efectivo contra armaduras

NIVEL 10: Meson Cannon
├─ Cañón de mesones
├─ Daño: 20 puntos
├─ Penetra armadura moderada
└─ Arma media-fuerte

NIVEL 14: Gauss Cannon
├─ Cañón de Gauss
├─ Daño: 25 puntos
├─ Penetra armadura pesada
└─ Excepcional contra blindaje

NIVEL 18: Phasor
├─ Arma de fase final
├─ Daño: 40+ puntos
├─ Penetra cualquier armadura
└─ Arma de élite
```

#### Sistemas Especiales

```
NIVEL 5: Subspace Communications
├─ Comunicaciones FTL
├─ +1 punto de comando por starbase
└─ Expande control de flota

NIVEL 10: Tractor Beam
├─ Rayo tractor
├─ Inmoviliza naves
├─ 4 necesarios para inmobilizar Battleship
└─ Crítico para abordajes

NIVEL 15: Battle Scanner
├─ Scaneo de batalla
├─ +50 acuratez de rayos a corto rango
└─ Invaluable para combate
```

---

### 8. FORCE FIELDS (Campos de Fuerza)

**Propósito:** Escudos, defensas especiales y jamming

#### Escudos Navales

```
NIVEL 1: Class I Shield
├─ Escudo básico
├─ Bloquea 1 punto de daño
├─ Absorbe 5x tamaño nave
└─ Base para posteriores

NIVEL 3: Class III Shield
├─ Escudo mejorado
├─ Bloquea 3 puntos de daño
├─ Absorbe 15x tamaño nave
└─ Defensa temprana

NIVEL 6: Class VI Shield
├─ Escudo avanzado
├─ Bloquea 6 puntos de daño
├─ Absorbe 30x tamaño nave
└─ Estándar medio-fuerte

NIVEL 10: Class X Shield
├─ Escudo potente
├─ Bloquea 10 puntos de daño
├─ Absorbe 50x tamaño nave
└─ Defensa sólida

NIVEL 18: Class XV Shield
├─ Escudo final
├─ Bloquea 15 puntos de daño
├─ Absorbe 75x tamaño nave
└─ Máxima protección escudo
```

#### Defensas Especiales

```
NIVEL 4: Radiation Shield
├─ Escudo de radiación
├─ Protege contra radiación
├─ Crítica para misiles nucleares
└─ Recomendado con defensa antimisil

NIVEL 7: Planetary Shield
├─ Escudo planetario
├─ Protege colonias de bombardeos
├─ -90% daño de ataques espaciales
└─ Clave para defensa

NIVEL 12: Stasis Field
├─ Campo de estasis
├─ Congela unidades
├─ Efecto temporal
└─ Defensivo especializado

NIVEL 16: Lightning Field
├─ Campo de rayo
├─ Destruye 50% de misiles
├─ Daño a unidades cercanas
└─ Defensa versátil
```

#### Sistemas de Transporte

```
NIVEL 8: Subspace Teleporter
├─ Teletransportador
├─ Teleportación de combate
├─ Escape táctico
└─ Posicionamiento estratégico

NIVEL 12: Advanced Teleporter
├─ Teletransportador mejorado
├─ Mayor rango
├─ Menos cooldown
└─ Más versatilidad
```

#### Sistemas de Evasión

```
NIVEL 5: Inertial Stabilizer
├─ Estabilizador inercial
├─ +30 defensa contra rayos
├─ Mejora movilidad
└─ Crítica para evasión

NIVEL 10: Displacement Device
├─ Dispositivo de desplazamiento
├─ -50% acuratez enemiga
├─ Evasión excepcional
└─ Muy efectivo
```

---

## Sistema de Investigación

### Mecánica de Investigación

```
PROCESO:
1. Seleccionar tecnología objetivo
2. Gastar Puntos de Investigación (RP)
3. Pagar costo base (2x costo base = garantizado)
4. Esperar "breakthrough" aleatorio
5. Tecnología investigada = disponible

COST STRUCTURE:
├─ Base Cost: Cantidad fija de RP necesarios
├─ Breakthrough Cost: RPs adicionales post-base
└─ Total: 2x Base = Garantizado siguiente turno
```

### Costo en Puntos de Investigación

Cada nivel tiene un costo base fijo. Después de pagar el costo base, puntos de investigación adicionales aumentan la probabilidad de "breakthrough". Una vez que el costo base se paga dos veces (incluyendo los RP del turno actual), la tecnología está garantizada para investigarse el próximo turno.

```
TABLA DE COSTOS (Aproximado):
├─ Nivel 1: 80 RP
├─ Nivel 2: 160 RP
├─ Nivel 3: 280 RP
├─ Nivel 5: 600 RP
├─ Nivel 8: 1500 RP
├─ Nivel 10: 2500 RP
├─ Nivel 13: 4500 RP
├─ Nivel 15: 7000 RP
└─ Nivel 20: 15000+ RP

TOTAL ACUMULADO:
├─ Para llegar a Nivel 10: ~10,000 RP
├─ Para llegar a Nivel 15: ~30,000 RP
└─ Para llegar a Nivel 20: ~60,000 RP
```

### Bonificadores de Costo

Después de pagar el costo base, puntos adicionales aumentan la probabilidad de breakthrough. La tasa exacta es aleatoria. Algunas razas pagan menos por tecnologías en sus especialidades (Excelente=60% costo, Bueno=80%, Promedio=100%, Pobre=125%).

```
MULTIPLICADORES POR RAZA:

ESPECIALIDAD EXCELENTE:
└─ 60% del costo base
└─ Ahorro: 40%

ESPECIALIDAD BUENA:
└─ 80% del costo base
└─ Ahorro: 20%

ESPECIALIDAD PROMEDIO:
└─ 100% del costo base
└─ Sin descuento

ESPECIALIDAD POBRE:
└─ 125% del costo base
└─ Penalización: 25%
```

### Gestión de Científicos

```
ASIGNACIÓN:
├─ Scientists al investigar: RP por turno
├─ Reasignación: Posible en cualquier turno
├─ Costo: Solo RP pagados, no reembolsados
└─ Optimización: Clave para eficiencia

ESTRATEGIA:
├─ Overallocate scientists temporalmente
├─ Una vez en 100%, reasignar a otros trabajos
├─ Libera población para producción/alimentos
└─ Maximiza eficiencia económica
```

---

## Características Especiales

### Creatives vs Non-Creatives vs Uncreatives

Los Creatives, cuando investigan 1 tech en un nivel, reciben TODAS las techs en ese nivel, generalmente 2-3 por el precio de una (hay ~6 niveles donde no aplica de ~80 total).

```
CREATIVES:
├─ Efecto: 1 tech investigada = TODAS en ese nivel
├─ Ventaja: Aceso 3x más rápido a opciones
├─ Costo: Igual que non-creative
├─ Impacto: Ventaja científica enorme

NON-CREATIVES:
├─ Efecto: Investigas solo 1 tech por turno
├─ Costo: Costo base normal
├─ Elección: Estratégica entre opciones
├─ Desafío: Seleccionar rama correcta

UNCREATIVES:
├─ Efecto: 1 tech investigada = 1 tech nada más
├─ Penalización: Investigación más lenta
├─ Costo: Mayor costo de investigación
└─ Desafío: Máximo en dificultad
```

### Bonus de Inicio Avanzado

```
STANDARD START (Pre-Warp):
├─ Algunas techs básicas gratis
├─ Flota pequeña
└─ Sin ventajas iniciales

ADVANCED START:
├─ Flota más grande
├─ Techs adicionales
├─ Mayor ventaja inicial
└─ Especialmente beneficiosa para Creatives
```

### Logros Tecnológicos

Los logros son beneficios globales que se aplican inmediatamente:

```
EJEMPLOS DE LOGROS:
├─ Heightened Intelligence: +2 RP por científico
├─ Planetary Shielding: -90% daño a colonias
├─ Subspace Communications: +1 comando por starbase
├─ Soil Enrichment: +1 comida por trabajador
├─ Cloning Center: +3 población por turno
└─ Advanced Manufacturing: +15% producción
```

---

## Modificaciones de Armas

### Sistema de Modificaciones

Las armas pueden ser modificadas mediante tecnologías especiales para mejorar su rendimiento.

```
MODIFICACIÓN DE MISILES:

Emissions Guidance (EMG):
├─ Requiere: Technology específica
├─ Efecto: Daño va directo a motores
├─ Consecuencia: Inmovilización o explosión
└─ Aplicación: A todos los misiles

MIRV (Multiple Independent Reentry Vehicle):
├─ Requiere: Nivel avanzado de Química
├─ Efecto: 1 misil → 3 misiles
├─ Daño: Distribuido en 3 objetivos
└─ Aplicación: Misiles seleccionados

MODIFICACIÓN DE RAYOS:

Heavy Armor Piercing (HAP):
├─ Efecto: Penetra armadura
├─ Penalización: Menor daño total
└─ Aplicación: Contra blindaje pesado

Increased Payload (IP):
├─ Efecto: Mayor daño
├─ Penalización: Menor alcance
└─ Aplicación: Combate cercano
```

### Miniaturización

La miniaturización es un concepto único en MOO2 que permite hacer armas más pequeñas y baratas.

```
MINIATURIZACIÓN:

DEFINICIÓN:
└─ Reducción de tamaño y costo de equipamiento
└─ Sin pérdida de funcionalidad

FACTORES:
├─ Nivel de miniaturización: 1-20
├─ Mejora cada nivel completado
└─ Afecta TODAS las armas y módulos

BENEFICIO:
├─ Tamaño: -5% por miniaturización
├─ Costo: -5% por miniaturización
├─ Mantenimiento: -5% por miniaturización
└─ Total: Compuesto acumulativo

LÍMITES:
├─ Nunca llega a 0
├─ Siempre cuesta algo
└─ Ligeramente menos reducido que costo
```

#### Mejora de Miniaturización en Niveles

```
NIVEL 1: Base (0% reducción)
NIVEL 5: -20% tamaño/costo
NIVEL 10: -40% tamaño/costo
NIVEL 15: -55% tamaño/costo
NIVEL 20: -65% tamaño/costo
```

---

## Ruta de Investigación Recomendada

### Temprano (Turnos 1-50)

```
PRIORIDADES:

1. EXPLORACIÓN
   └─ Deuterium Fuel Cells (Power Nivel 2)
   └─ Extiende rango de exploración

2. ECONOMÍA
   └─ Construction Techs (Engineering)
   └─ Permite colonias mejores
   └─ Soil Enrichment o Cloning Center (Chemistry/Biology)

3. DEFENSA MÍNIMA
   └─ Laser Cannon (Physics Nivel 1)
   └─ Tritanium Armor (Chemistry Nivel 5)
   └─ Class III Shield (Force Fields Nivel 3)

4. GOBERNANZA
   └─ Space Academy (Sociology Nivel 3)
   └─ Entrena tripulaciones mejores

ESTRATEGIA:
├─ Balancear expansión territorial
├─ Construir base económica
└─ Preparar defensa básica
```

### Mid-Game (Turnos 50-150)

```
PRIORIDADES:

1. PODER MILITAR MEJORADO
   ├─ Fusion Beam (Physics Nivel 3)
   ├─ Merculite Missile (Chemistry Nivel 4)
   ├─ Class VI Shield (Force Fields Nivel 6)
   └─ Armas más potentes

2. VELOCIDAD DE VIAJE
   ├─ Fusion Drives (Power Nivel 8)
   └─ Más rápida invasión/defensa

3. INVESTIGACIÓN MEJORADA
   ├─ Laboratory Techs (Sociology/Computers)
   ├─ Heightened Intelligence (Biology)
   └─ Acelera investigación

4. EXPANSIÓN ECONÓMICA
   ├─ Banking (Sociology Nivel 6)
   └─ +15% ingresos

ESTRATEGIA:
├─ Conquistar imperios rivales débiles
├─ Construir ventaja tecnológica
└─ Prepararse para conflictos mayores
```

### Tardío (Turnos 150+)

```
PRIORIDADES:

1. ARMAS FINALES
   ├─ Phasor (Physics Nivel 18)
   ├─ Neutronium Armor (Chemistry Nivel 18)
   ├─ Class XV Shield (Force Fields Nivel 18)
   └─ Equipamiento superior

2. SISTEMAS ESPECIALES
   ├─ Subspace Teleporter (Force Fields Nivel 8)
   ├─ Tractor Beam (Physics Nivel 10)
   ├─ Battle Scanner (Physics Nivel 15)
   └─ Ventaja táctica

3. MOVILIDAD EXTREMA
   ├─ Anti-Matter Drive (Power Nivel 12)
   ├─ Annihilation Drive (Power Nivel 18)
   └─ Despliegue instantáneo

4. DEFENSA PLANETARIA
   ├─ Planetary Shield (Force Fields Nivel 7)
   ├─ Lightning Field (Force Fields Nivel 16)
   └─ Protección total

ESTRATEGIA:
├─ Dominar militarmente
├─ O prepararse para victoria electoral/Antares
└─ Asegurar supervivencia contra múltiples enemigos
```

### Ruta para Victoria Electoral

```
ENFOQUE DIPLOMÁTICO:

1. INVESTIGACIÓN RÁPIDA
   ├─ Heightened Intelligence
   ├─ Laboratories avanzados
   └─ Investigación 50%+ más rápida

2. ECONOMÍA FUERTE
   ├─ Banking (Sociology Nivel 6)
   ├─ Trade Goods (Sociology)
   └─ Dinero para diplomacia

3. POBLACIÓN MÁXIMA
   ├─ Cloning Center
   ├─ Soil Enrichment
   └─ Population growth = votos en Consejo

4. DEFENSA MÍNIMA VIABLE
   ├─ Anti-missile techs
   ├─ Planetary Shields
   └─ Evita destrucción sin armas costosas

VENTAJA: Menos inversión militar = más dinero para diplomacia y crecimiento
```

### Ruta para Victoria de Antares

```
ENFOQUE CONQUISTA:

1. PODER MILITAR MÁXIMO
   ├─ Todas las armas finales
   ├─ Todas las defensas finales
   └─ Flota Doom Star

2. MOVILIDAD
   ├─ Anti-Matter Drive
   ├─ Subspace Teleporter
   └─ Despliegue rápido

3. SISTEMAS DE CONTROL
   ├─ Tractor Beam (inmoviliza)
   ├─ Tachyon Scanner (ve todo)
   ├─ Battle Scanner (acuratez)
   └─ Dominio absoluto

4. SUPERVIVENCIA
   ├─ Shields máximos
   ├─ Regeneración
   ├─ Evasión
   └─ Defensa anti-daño

VENTAJA: Podrás destruir al Guardián de Orión y penetrar el Portal
```

---

## Implementación Técnica

### Estructuras de Datos

```javascript
// TECNOLOGÍA
Technology {
  id: string
  name: string
  category: 'engineering' | 'power' | 'chemistry' | ... 
  level: number (0-20)
  baseCost: number (RP)
  researchTime: number (turns)
  prerequisite?: TechnologyId[]
  effects: TechEffect[]
  bonusForRace?: { raceId: string, multiplier: number }
  isAvailable: boolean (generado aleatoriamente)
  isResearched: boolean
  inProgress: boolean
}

// EFECTO DE TECNOLOGÍA
TechEffect {
  type: 'ship_weapon' | 'ship_shield' | 'building' | 'achievement' | ...
  targetType: string
  bonusValue: number | string
  bonusType: '+' | '*' | 'replace'
  description: string
}

// ÁRBOL DE TECNOLOGÍAS
TechTree {
  empire: string (empireId)
  researching?: Technology
  rpProgress: number (RPs gastados)
  completedTechs: TechnologyId[]
  raceBonus: {
    engineering: number
    power: number
    chemistry: number
    sociology: number
    computers: number
    biology: number
    physics: number
    forceFields: number
  }
}

// MODIFICACIÓN DE ARMA
WeaponModification {
  id: string
  name: string
  baseWeapon: string
  techRequired: TechnologyId
  effects: {
    damageMultiplier?: number
    rangeMultiplier?: number
    accuracyBonus?: number
    sizeMultiplier?: number
    costMultiplier?: number
  }
}

// MINIATURIZACIÓN
Miniaturization {
  currentLevel: number (0-20)
  costReduction: number (calculated from level)
  sizeReduction: number (calculated from level)
  maintenanceReduction: number (calculated from level)
}
```

### Arquitectura de Módulos

```
/technology
  ├─ /research
  │  ├─ researchManager.ts
  │  ├─ researchCalculations.ts
  │  ├─ breakthroughSystem.ts
  │  └─ researchUI.tsx
  │
  ├─ /tree
  │  ├─ technologyTree.ts
  │  ├─ technologyGenerator.ts (random availability)
  │  ├─ technologyDatabase.ts
  │  └─ treeVisualization.tsx
  │
  ├─ /effects
  │  ├─ effectApplier.ts
  │  ├─ buildingUnlocker.ts
  │  ├─ weaponEnhancer.ts
  │  └─ shipModifier.ts
  │
  ├─ /modifications
  │  ├─ weaponModifications.ts
  │  ├─ miniaturization.ts
  │  └─ modificationCalculator.ts
  │
  ├─ /ai
  │  ├─ aiResearchStrategy.ts
  │  ├─ techPathPlanner.ts
  │  └─ raceSpecializationBonus.ts
  │
  └─ /data
     ├─ technologies.json
     ├─ raceBonus.json
     └─ weaponModifications.json
```

### Flujos Principales

#### A. Seleccionar Tecnología a Investigar

```
1. Abrir pantalla de investigación
2. Ver árbol de tecnologías (8 ramas)
3. Seleccionar rama específica
4. Elegir tecnología disponible del nivel actual
5. Confirmar selección
6. Asignar científicos (opcional)
7. Investigación comienza
```

#### B. Avance de Investigación

```
Cada turno:
1. Calcular RP producidos (científicos × productividad)
2. Sumar a rpProgress de tech actual
3. Si rpProgress >= baseCost:
   └─ Entra fase "breakthrough"
4. Cada turno en breakthrough:
   ├─ Calcular % probabilidad
   ├─ Roll aleatorio
   ├─ Si éxito: Tech completada
   └─ Si fallo: Esperar siguiente turno
5. Tech completada:
   ├─ Aplicar todos los efectos
   ├─ Desbloquear edificios/armas
   ├─ Activar logros
   └─ Permitir siguiente tech en rama
```

#### C. Aplicar Efectos de Tecnología

```
1. Tech completada
2. Buscar todos los TechEffects
3. Para cada efecto:
   ├─ Determinar tipo (arma/edificio/logro)
   ├─ Aplicar bonificación al imperio
   ├─ Actualizar stats de colonias
   ├─ Actualizar opciones de construcción naval
   └─ Notificar jugador
4. Actualizar UI (nuevas opciones disponibles)
```

### Cálculos Clave

```typescript
// Costo ajustado por raza
adjustedCost = baseCost * raceBonus[category]

// Reducción por miniaturización
sizeAfterMiniaturization = baseSize * (1 - miniLevel * 0.05)
costAfterMiniaturization = baseCost * (1 - miniLevel * 0.045)

// Breakthrough probability
let progress = rpSpent - baseCost
let remainingCost = baseCost  // costo para garantizar
let breakthroughChance = progress / remainingCost * 100
if (breakthroughChance > 100) breakthroughChance = 100

// RP total acumulado para alcanzar nivel
totalRPToLevel = sum(costLevel[1] through costLevel[n])
```

---

## Testing y Balance

### Casos de Prueba Críticos

```
✓ Selección y comencio de investigación
✓ Avance correcto de breakthrough
✓ Aplicación de efectos inmediatos
✓ Descubrimiento de edificios/armas
✓ Generación aleatoria de árbol (Creative = 3x opciones)
✓ Bonificadores de raza correctos
✓ Miniaturización reduce costo/tamaño
✓ Modificaciones de arma funcionan
✓ Reasignación de científicos valida RP
✓ Transición a siguiente nivel de rama
✓ Logros se aplican globalmente
✓ IA elige ruta estratégica
✓ No-Creative recibe solo 1 tech por nivel
✓ Uncreative tiene penalización de costo
```

### Métricas de Balance

```
- Tiempo promedio para tech por nivel
- Distribución de opciones entre ramass
- Impacto de bonificadores de raza
- Ventaja de Creative vs Non-Creative
- Eficiencia de diferentes rutas de investigación
- Poder relativo de armas por nivel
- Costo/beneficio de edificios especiales
```

---

## Notas de Diseño

### Por qué la Tecnología es Fundamental

1. **Escalado No-Linear**
   - Early advantage crece exponencialmente
   - Una generación de tecnología = victoria
   - Diferencia de 2-3 niveles = imposible de alcanzar

2. **Múltiples Caminos**
   - No hay ruta "correcta" única
   - Diferentes estrategias requieren diferentes techs
   - Aleatoriedad mantiene replayability

3. **Integración con Otros Sistemas**
   - Techs desbloquean edificios
   - Edificios mejoran producción y RP
   - Mejor RP = más techs = más poder
   - Ciclo de retroalimentación positiva

### Consideraciones de Dificultad

```
FÁCIL:
- Costos 30% menos
- Probabilidad breakthrough +20%
- IA avanza más lento
- Árbol con más opciones

NORMAL:
- Costos estándar
- Probabilidad breakthrough estándar
- IA estratégica
- Árbol balanceado

DIFÍCIL:
- Costos 15% más
- Probabilidad breakthrough -10%
- IA min-maxea investigación
- Árbol limitado

IMPOSIBLE:
- Costos 30% más
- Probabilidad breakthrough -25%
- IA investigación óptima
- Árbol minimizado
```

---

## Próximos Pasos

1. **Crear base de datos de tecnologías**
   - 8 ramas × ~15 niveles = ~120 techs
   - Definir cada tech con efectos
   
2. **Implementar sistema de investigación**
   - Gestión de RP
   - Cálculo de breakthrough
   
3. **Desarrollar árbol de tecnologías**
   - Generación aleatoria
   - Sistema de disponibilidad
   
4. **Crear sistema de efectos**
   - Aplicar bonificaciones
   - Desbloquear opciones
   
5. **Implementar miniaturización**
   - Cálculos de reducción
   - Aplicación a armas/estructuras
   
6. **Agregar modificaciones de armas**
   - Sistema MIRV
   - Sistema EMG
   
7. **Integrar con diseño naval**
   - Nuevas armas disponibles
   - Nuevas defensas disponibles
   
8. **Testing y balanceo**
   - Verificar costos
   - Validar rutas de investigación

---

**Versión:** 1.0  
**Última actualización:** 2024  
**Estado:** Especificación Completa Lista para Implementación
