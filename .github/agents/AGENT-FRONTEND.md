# AGENT-FRONTEND.md — MasterDeHostias: Instrucciones para Copilot Agent (Frontend Developer)

---

## ROL

Eres el agente de desarrollo **Frontend** para el proyecto MasterDeHostias, un juego web de estrategia 4X espacial por turnos. Tu responsabilidad principal es implementar toda la interfaz de usuario, las vistas del juego, la integración con la API del backend, y la experiencia visual del jugador.

---

## TECNOLOGÍAS

- **Framework**: Consulta la tabla de asignación en MasterDeHostias_practica.md § 4.1 para saber qué framework usa tu grupo (Vue)
- **Lenguaje**: TypeScript (recomendado) o JavaScript
- **Entorno**: Node.js
- **Estilos**: CSS/SCSS con estética sci-fi espacial
- **Estado**: Usa el store nativo del framework (Redux/Zustand para React, Pinia para Vue, NgRx para Angular, Svelte stores para Svelte)
- **HTTP**: fetch API o axios para comunicación con backend
- **Routing**: React Router / Vue Router / Angular Router / SvelteKit routing

---

## ARQUITECTURA FRONTEND

```
frontend/
├── src/
│   ├── components/        # Componentes reutilizables (Button, Modal, Panel, etc.)
│   ├── views/             # Vistas/páginas principales
│   │   ├── LandingPage
│   │   ├── LoginPage
│   │   ├── RegisterPage
│   │   ├── Dashboard
│   │   ├── GameView
│   │   ├── GalaxyMap
│   │   ├── SystemView
│   │   ├── ColonyView
│   │   ├── TechTree
│   │   ├── FleetManager
│   │   └── CombatResult
│   ├── store/             # Estado global de la aplicación
│   ├── services/          # Llamadas HTTP al backend (api.ts)
│   ├── types/             # Tipos TypeScript (interfaces del juego)
│   ├── assets/            # Imágenes, sprites, iconos
│   │   └── ai-generated/  # Recursos generados por IA (etiquetados)
│   ├── utils/             # Utilidades (formateo, cálculos de UI)
│   └── styles/            # Estilos globales, tema sci-fi
├── public/
├── Dockerfile
├── package.json
└── tsconfig.json
```

---

## VISTAS PRINCIPALES — QUÉ IMPLEMENTAR

### 1. LandingPage (`/`)
- Logo del juego y título "MasterDeHostias"
- Botones de Login y Registro
- Diseño atractivo con fondo espacial

### 2. LoginPage (`/login`)
- Formulario: username + password
- Llamada a `POST /api/auth/login`
- Almacenar JWT en store y localStorage
- Redirigir a Dashboard tras login exitoso
- Mostrar errores de autenticación

### 3. RegisterPage (`/register`)
- Formulario: username + email + password + confirmar password
- Validación client-side antes de enviar
- Llamada a `POST /api/auth/register`
- Redirigir a Dashboard tras registro exitoso

### 4. Dashboard (`/dashboard`)
- Lista de partidas guardadas (`GET /api/games`)
- Botón "Nueva Partida" que abre modal de configuración:
  - Selector de raza (3 asignadas al grupo + custom si Grupo 3)
  - Tamaño de galaxia (small, + medium/large si Grupo 6)
  - Número de oponentes
  - Dificultad
- Botón "Cargar" en cada partida
- Botón "Eliminar" con confirmación
- Info de cada partida: nombre, turno, raza, última fecha guardado

### 5. GalaxyMap (`/game/:id/galaxy`)
**VISTA PRINCIPAL DEL JUEGO**
- Renderizar estrellas como nodos en posiciones 2D
- Líneas de conexión entre sistemas conectados
- Colores de estrellas según tipo (rojo, naranja, amarillo, blanco, azul)
- Iconos sobre estrellas:
  - Bandera del jugador (si tiene colonia)
  - Bandera enemiga (si se detecta colonia enemiga)
  - Icono de flota propia
  - Icono de flota enemiga (si visible)
- **Fog of War**: Sistemas no explorados oscurecidos/ocultos
- Click en estrella → navegar a SystemView
- Click en flota propia → abrir panel de flota
- Panel lateral con:
  - Recursos del jugador (BC, comida total, producción, investigación, puntos de comando)
  - Turno actual
  - Botón "Fin de Turno"
  - Botón "Guardar"
- **Atajos de teclado MOO2**: Todos los atajos definidos en SPECS.md § 4.3 deben funcionar aquí (`T` fin de turno, `C` colonias, `F` flotas, `P` planetas, `R` razas, `G` menú, `+`/`-` zoom, `F1`/`F2` ciclar colonias, `F10` guardar, `Alt+F` rutas de flotas, etc.)
- **Ctrl+Tab** → abrir consola de cheats (CheatConsole)

### 6. SystemView (`/game/:id/system/:sysId`)
- Estrella central con planetas orbitando
- Click en planeta → tooltip con info (tipo, tamaño, minerales, gravedad)
- Click en planeta colonizado → navegar a ColonyView
- Botón "Colonizar" si hay nave colonizadora y planeta libre
- Lista de flotas en el sistema
- Botón "Volver al mapa"

### 7. ColonyView (`/game/:id/colony/:colId`)
- **Panel de Población**: Sliders o +/- para Granjeros, Trabajadores, Científicos
  - Suma debe ser = total population
  - Actualización en tiempo real de producción estimada
- **Barras de Producción**: Comida, Industria, Investigación, BC
- **Edificios Construidos**: Grid de iconos con nombre
- **Cola de Construcción**: Lista de hasta 7 elementos, drag-and-drop para reordenar
  - Barra de progreso en el primer elemento
  - Botón para añadir/eliminar elementos
- **Selector de Construcción**: Categorías (Edificios | Naves), filtrado por disponibilidad tecnológica
- Botón "Aplicar Cambios" → `POST /api/games/{gameId}/colony/{colonyId}/manage`
- Info del planeta (tipo, tamaño, minerales, gravedad)

### 8. TechTree (`/game/:id/tech`)
- 8 columnas (una por campo de investigación)
- Filas por nivel (1, 2, 3+)
- Cada tech es un nodo con estado visual:
  - Verde brillante: disponible para investigar
  - Azul: ya investigado
  - Gris: bloqueado (nivel anterior no completado)
  - Rojo tachado: descartado (se eligió otra opción del mismo nivel)
- Click en tech disponible → confirmación → `POST /api/games/{gameId}/research`
- Tooltip con descripción, coste, desbloqueos
- Barra de progreso de investigación actual

### 9. FleetManager (`/game/:id/fleets`)
- Lista de todas las flotas del jugador
- Para cada flota: nombre, ubicación, composición (tipos y cantidades), destino si en tránsito
- Click en flota → opciones:
  - Mover: seleccionar destino en mapa
  - Ver composición detallada
- Indicador de puntos de comando (usados / total)
- Posibilidad de seleccionar destino directamente desde el GalaxyMap

### 10. CombatResult (`/game/:id/combat/:combatId`)
- Pantalla dividida: lado atacante vs lado defensor
- Sprites/iconos de naves de cada bando
- Después de la resolución: naves tachadas = destruidas
- Resultado claro: VICTORIA / DERROTA
- Detalles de bajas
- Botón "Continuar"

### 11. AITurnViewer (componente overlay)
- Se activa al pulsar "Fin de Turno"
- **Modo Pantalla Completa**: reemplaza la vista del jugador
- **Modo Pantalla Dividida**: izquierda estática (jugador), derecha dinámica (IA)
- Controles: Play/Pause, Paso adelante, Paso atrás, Velocidad (Normal/Rápido/Instantáneo)
- Animaciones:
  - Movimiento de flotas: línea animada entre estrellas
  - Combate: destello/explosión
  - Colonización: icono de bandera aparece
  - Investigación: icono de bombilla
- Panel con reasoning de la IA (texto explicativo)
- Botón "Saltar al resultado final"

### 12. EventLogPanel (componente modal)
- Modal bloqueante que aparece al inicio de cada turno del jugador, tras resolver el turno de la IA
- Lista todos los eventos del turno: combates, colonizaciones, investigaciones completadas, escasez de comida, edificios/naves completados, ataques Antaranos, votaciones del Consejo, victoria/derrota
- Cada evento con icono según tipo y color (rojo: ataques/pérdidas, verde: completados/victorias, amarillo: alertas)
- Botón "Continuar" o Escape para cerrar
- Si no hay eventos, no se muestra
- Fuente de datos: campo `events` de la respuesta de `POST /api/games/{gameId}/endTurn`

### 13. CheatConsole (componente overlay)
- Se activa con Ctrl+Tab
- Input de texto para escribir código
- Selector de target (sistema/colonia) si lo requiere el cheat
- Historial de cheats aplicados
- Botón "Aplicar" → `POST /api/games/{gameId}/cheat`
- Respuesta visual del resultado
- Botón "Cerrar" o Escape

---

## SERVICIO API (services/api.ts)

Implementar un servicio centralizado para todas las llamadas HTTP:

```typescript
// services/api.ts
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function request(method: string, path: string, body?: any) {
  const token = localStorage.getItem('token');
  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    },
    body: body ? JSON.stringify(body) : undefined
  });
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.error || 'Request failed');
  }
  return res.json();
}

export const api = {
  // Auth
  login: (username: string, password: string) => request('POST', '/api/auth/login', { username, password }),
  register: (username: string, email: string, password: string) => request('POST', '/api/auth/register', { username, email, password }),
  getProfile: () => request('GET', '/api/auth/profile'),

  // Games
  listGames: () => request('GET', '/api/games'),
  createGame: (config: any) => request('POST', '/api/games', config),
  loadGame: (gameId: string) => request('GET', `/api/games/${gameId}`),
  saveGame: (gameId: string, name?: string) => request('POST', `/api/games/${gameId}/save`, { name }),
  deleteGame: (gameId: string) => request('DELETE', `/api/games/${gameId}`),

  // In-game
  manageColony: (gameId: string, colonyId: string, data: any) => request('POST', `/api/games/${gameId}/colony/${colonyId}/manage`, data),
  selectResearch: (gameId: string, data: any) => request('POST', `/api/games/${gameId}/research`, data),
  moveFleet: (gameId: string, fleetId: string, destination: string) => request('POST', `/api/games/${gameId}/fleet/${fleetId}/move`, { destination }),
  colonize: (gameId: string, fleetId: string, planetIndex: number) => request('POST', `/api/games/${gameId}/colonize`, { fleet_id: fleetId, planet_index: planetIndex }),
  endTurn: (gameId: string) => request('POST', `/api/games/${gameId}/endTurn`),
  applyCheat: (gameId: string, code: string, target?: any) => request('POST', `/api/games/${gameId}/cheat`, { cheat_code: code, target }),

  // Queries
  getGalaxy: (gameId: string) => request('GET', `/api/games/${gameId}/galaxy`),
  getTechTree: (gameId: string) => request('GET', `/api/games/${gameId}/tech-tree`),
  getColony: (gameId: string, colonyId: string) => request('GET', `/api/games/${gameId}/colony/${colonyId}`),
  getScenarios: () => request('GET', '/api/scenarios'),
};
```

---

## TIPOS TYPESCRIPT

Consultar SPECS.md § 1 para los modelos de datos completos. Crear interfaces TypeScript que reflejen exactamente esos modelos:

```typescript
// types/game.ts — Crear interfaces para:
interface User { ... }
interface Race { ... }
interface Planet { ... }
interface StarSystem { ... }
interface Colony { ... }
interface Building { ... }
interface Technology { ... }
interface Ship { ... }
interface Fleet { ... }
interface GameState { ... }
interface PlayerState { ... }
interface AIAction { ... }
interface CombatResult { ... }
interface CheatResponse { ... }
```

---

## ESTILO VISUAL

- **Tema**: Sci-fi espacial, oscuro
- **Colores base**: Negro (#0a0a1a), azul oscuro (#1a1a3e), cyan (#00d4ff), verde (#00ff88), rojo (#ff3366)
- **Fuentes**: Monoespaciada para datos numéricos, sans-serif para texto general
- **Elementos**: Bordes biselados estilo panel de nave, glow effects en iconos activos
- **Fondo**: Estrellas animadas (partículas) o imagen estática de campo estelar
- **Iconos**: Generados con IA o pixel art, etiquetados como generados por IA

---

## MÓDULO ESPECÍFICO DEL GRUPO

Consultar SPECS.md § 6 para los requisitos del módulo asignado a tu grupo. El frontend debe implementar la interfaz correspondiente:

| Grupo | Módulo | Frontend adicional |
|-------|--------|--------------------|
| 1 | Combate Táctico | Arena de combate 12×12, sprites, orden de turnos, acciones tácticas |
| 2 | Espionaje | Panel de espías, asignación de misiones, informes |
| 3 | Constructor Razas | Pantalla de creación con picks, preview, validación en tiempo real |
| 4 | Diplomacia | Embajadores, tratados, votación del Consejo |
| 5 | Diseño Naves | Designer drag-and-drop, componentes, preview de stats |
| 6 | Galaxia Grande | Mapa escalable, minimapa, zoom, lazy loading |

---

## REGLAS DE DESARROLLO

1. **Consulta SPECS.md** antes de implementar cualquier endpoint o componente
2. **No inventes datos** — usa los modelos exactos de SPECS.md
3. **Fog of War**: Nunca renderices información de sistemas no visibles para el jugador
4. **Feedback visual**: Toda acción del usuario debe tener feedback inmediato (loading, success, error)
5. **Reutiliza componentes**: Panel, Modal, Button, Tooltip deben ser componentes compartidos
6. **Manejo de errores HTTP**: Capturar y mostrar errores al usuario de forma amigable
7. **JWT**: Guardar en localStorage, enviar en headers, redirigir a login si 401
8. **Ctrl+Tab cheats**: Debe funcionar desde el GalaxyMap, implementar listener de teclado
9. **Recursos IA**: Todo recurso visual generado con IA va en `/assets/ai-generated/` con etiqueta
10. **Atajos de teclado MOO2**: Implementar todos los atajos de SPECS.md § 4.3. Los atajos globales deben funcionar cuando GalaxyMap tiene foco, usando un `keydown` listener en el componente raíz del juego. Ignorar atajos si un `<input>` o `<textarea>` tiene foco.

---

## CHECKLIST ANTES DE ENTREGAR

- [ ] Login/Register funcionales con feedback de errores
- [ ] Dashboard con lista de partidas y creación de nueva
- [ ] GalaxyMap renderiza estrellas, conexiones, fog of war
- [ ] SystemView muestra planetas con info + colonización
- [ ] ColonyView con gestión de población y cola de construcción
- [ ] TechTree interactivo con estados visuales
- [ ] FleetManager con movimiento de flotas
- [ ] CombatResult con resumen visual
- [ ] AITurnViewer con al menos 1 modo de visualización
- [ ] EventLogPanel modal bloqueante al inicio de turno
- [ ] CheatConsole funcional con Ctrl+Tab
- [ ] Atajos de teclado MOO2 funcionales (T, C, F, P, R, G, +/-, F1/F2, F10, Alt+F, etc.)
- [ ] Estética sci-fi coherente
- [ ] Sin errores en consola del navegador
- [ ] Módulo específico del grupo implementado
- [ ] Dockerfile funcional
