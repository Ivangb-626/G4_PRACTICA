# AGENT-FRONTEND.md — MyMasterOfHostias: Frontend Developer Instructions

---

## ROLE

You are the **Frontend** developer agent for MyMasterOfHostias, a MOO2-faithful 4X space strategy game. You maintain the React/TypeScript UI, Canvas2D rendering, Zustand stores, API integration, and UX features.

---

## TECH STACK

- **Framework**: React 18 + TypeScript + Vite
- **State Management**: Zustand (2 stores)
- **Rendering**: Canvas 2D API (galaxy map, tactical combat)
- **Styling**: Inline CSS-in-JS objects (no CSS files, no Tailwind)
- **Containerization**: nginx serving Vite build via Docker
- **API**: Fetch-based HTTP client (no axios)

---

## ACTUAL PROJECT STRUCTURE

```
frontend/
├── src/
│   ├── App.tsx                    # Root component: screen router + global keyboard shortcuts
│   ├── main.tsx                   # React entry point
│   ├── api/
│   │   └── client.ts             # Centralized API client (all backend HTTP calls)
│   ├── store/
│   │   ├── gameStore.ts           # Game state Zustand store (auth, game, galaxy, colonies, fleets, research, diplomacy, leaders, tactical, events)
│   │   └── uiStore.ts            # UI state Zustand store (screen routing, selections, modals, sidebar, cheats, notifications, event log)
│   ├── components/               # All screens and UI components
│   │   ├── MainMenu.tsx          # Login/register + game list (card grid layout)
│   │   ├── NewGame.tsx           # New game form (race, AI races, galaxy size, difficulty)
│   │   ├── GalaxyMap.tsx         # Galaxy canvas + sidebar panel (zoom/pan support)
│   │   ├── ColonyScreen.tsx      # Colony detail (population, buildings, build queue)
│   │   ├── ResearchScreen.tsx    # Tech tree (8 fields, current research, available techs)
│   │   ├── FleetScreen.tsx       # Fleet management (list, move, merge)
│   │   ├── ShipDesigner.tsx      # Ship design (hull, weapons, specials)
│   │   ├── DiplomacyScreen.tsx   # Diplomacy (relations, treaties, war)
│   │   ├── LeadersScreen.tsx     # Leaders (hire, assign, unassign)
│   │   ├── EspionageScreen.tsx   # Espionage (recruit, missions)
│   │   ├── CombatScreen.tsx      # Tactical combat (12×12 grid canvas)
│   │   ├── TurnSummary.tsx       # End-of-turn summary (events, victory/defeat)
│   │   ├── CouncilScreen.tsx     # Galactic Council voting
│   │   ├── InventoryScreen.tsx   # Ship inventory
│   │   ├── TopBar.tsx            # Game info bar (turn, race, BC, nav buttons, end turn)
│   │   ├── EventLogModal.tsx     # Blocking modal: events + AI actions after each turn
│   │   └── common/
│   │       ├── Tooltip.tsx       # Reusable tooltip
│   │       └── Modal.tsx         # Reusable modal wrapper
│   ├── canvas/
│   │   ├── galaxyRenderer.ts    # Galaxy map rendering (spiral bg texture, stars, fleets, nebulae, range circles)
│   │   └── combatRenderer.ts    # Tactical combat rendering (12×12 grid)
│   └── types/                   # TypeScript type definitions
│       ├── game.ts              # Game, Star, Planet, Colony, Fleet, etc.
│       ├── research.ts          # Tech, TechField, TechState
│       ├── combat.ts            # CombatLog, TacticalState
│       ├── diplomacy.ts         # Relation, Treaty types
│       ├── ship.ts              # ShipDesign, Hull, Weapon, Special
│       ├── leader.ts            # Leader, LeaderTrait
│       ├── espionage.ts         # Spy, Mission types
│       ├── council.ts           # Council vote types
│       └── event.ts             # GameEvent types
├── index.html
├── vite.config.ts
├── tsconfig.json
├── package.json
├── Dockerfile
└── nginx.conf
```

---

## SCREEN ROUTING

**NO URL-based routing.** The app uses Zustand state-based screen routing via `useUIStore`:

```typescript
// uiStore.ts
interface UIState {
  activeScreen: ScreenName;
  setScreen: (screen: ScreenName) => void;
  // ...
}

type ScreenName =
  | 'main_menu'     // Login/register + game list
  | 'new_game'      // New game creation form
  | 'galaxy'        // Galaxy map (main game screen)
  | 'colony'        // Colony detail
  | 'research'      // Tech tree
  | 'fleet'         // Fleet management
  | 'ship_designer' // Ship designer
  | 'diplomacy'     // Diplomacy relations
  | 'leaders'       // Leaders panel
  | 'espionage'     // Espionage panel
  | 'combat'        // Tactical combat
  | 'turn_summary'  // Turn summary
  | 'council'       // Galactic Council
  | 'inventory';    // Ship inventory
```

**App.tsx screen switch:**
```tsx
function App() {
  const { activeScreen } = useUIStore();
  const { eventLogOpen } = useUIStore();
  // ... keyboard shortcut useEffect ...

  if (!inGame) return <MainMenu />;

  return (
    <>
      <TopBar />
      {eventLogOpen && <EventLogModal />}
      {activeScreen === 'galaxy' && <GalaxyMap />}
      {activeScreen === 'colony' && <ColonyScreen />}
      {/* ... other screens ... */}
    </>
  );
}
```

---

## ZUSTAND STORES

### gameStore.ts — Game State
```typescript
interface GameState {
  // Auth
  token: string | null;
  username: string | null;
  login(u: string, p: string): Promise<void>;
  register(u: string, p: string): Promise<void>;
  logout(): void;

  // Game
  gameId: string | null;
  game: GameData | null;
  games: GameSummary[];
  createGame(opts): Promise<void>;
  loadGame(id: string): Promise<void>;
  listGames(): Promise<void>;
  deleteGame(id: string): Promise<void>;

  // Galaxy
  galaxy: Galaxy | null;
  fetchGalaxy(): Promise<void>;

  // Colonies
  colonies: Colony[];
  fetchColonies(): Promise<void>;
  assignPopulation(colonyId, assignment): Promise<void>;
  setBuildQueue(colonyId, queue): Promise<void>;

  // Fleets
  fleets: Fleet[];
  fetchFleets(): Promise<void>;
  moveFleet(fleetId, dest): Promise<void>;
  colonize(fleetId): Promise<void>;

  // Ship Designs
  designs: ShipDesign[];
  fetchDesigns(): Promise<void>;
  createDesign(design): Promise<void>;

  // Research
  techState: TechState | null;
  fetchResearch(): Promise<void>;
  selectResearch(techId): Promise<void>;

  // Diplomacy
  relations: DiplomacyRelation[];
  fetchDiplomacy(): Promise<void>;
  propose/accept/reject/cancel/war...

  // Leaders
  leaders: Leader[];
  availableLeaders: LeaderTemplate[];
  fetchLeaders/hireLeader/assignLeader/unassignLeader...

  // Tactical Combat
  tacticalState: TacticalState | null;
  startTactical/submitAction/autoTactical...

  // Turn
  events: GameEvent[];
  aiActions: Record<string, unknown>[];
  endTurn(): Promise<void>;  // auto-opens EventLogModal when events/aiActions exist
}
```

### uiStore.ts — UI State
```typescript
interface UIState {
  activeScreen: ScreenName;
  setScreen(s: ScreenName): void;

  selectedStarIndex: number | null;
  selectStar(idx: number | null): void;

  selectedColonyId: string | null;
  selectColony(id: string | null): void;

  sidebarOpen: boolean;
  toggleSidebar(): void;

  cheatInput: string;
  setCheatInput(s: string): void;

  notification: string | null;
  showNotification(msg: string): void;
  clearNotification(): void;

  eventLogOpen: boolean;
  openEventLog(): void;
  closeEventLog(): void;
}
```

---

## KEYBOARD SHORTCUTS (Global, App.tsx)

All shortcuts are handled by a global `keydown` event listener in App.tsx. Only active when `inGame` (not on main_menu/new_game). Disabled when an input/textarea/select has focus.

| Key | Action |
|-----|--------|
| `T` | End turn (`endTurn()`) |
| `G` | Galaxy map screen |
| `C` | Colony screen |
| `R` | Research screen |
| `F` | Fleet screen |
| `L` | Leaders screen |
| `D` | Diplomacy screen |
| `S` | Ship designer screen |
| `I` | Inventory screen |
| `+`/`=` | Zoom in (galaxy map) |
| `-` | Zoom out (galaxy map) |
| `0` | Reset zoom |
| `Ctrl+Tab` / `` ` `` | Toggle cheat console |
| `Y` | Confirm (turn_summary/council) |
| `Escape` | Close modal / back to galaxy |

---

## GALAXY MAP — Canvas Rendering

### galaxyRenderer.ts

```typescript
renderGalaxy(
  ctx: CanvasRenderingContext2D,
  galaxy: Galaxy,
  width: number,
  height: number,
  selectedStarIndex: number | null,
  playerFleets: Fleet[],
  playerId: string,
  zoom: number,
  panX: number,
  panY: number
): void
```

Renders in layers:
1. Deep-space background (gradient)
2. **Spiral galaxy texture** (procedural Milky Way: 4 arms, 900 particles/arm, warm core, nebulae, dust stars — 2048px offscreen canvas, cached)
3. Stars (colored circles sized by type) — FOW: only explored stars shown
4. Star names (below stars)
5. Fleet indicators (ship icon next to owned stars)
6. Selection ring (around selected star)
7. Fleet range circle (dashed circle around selected fleet origin)

### Zoom & Pan (GalaxyMap.tsx)
- **Scroll wheel**: smooth zoom via `requestAnimationFrame` + lerp (factor 0.18), multiplicative (×0.9/×1.1) toward cursor position
- **Range**: 0.3×–6×
- **Shift+click drag** or **middle-click drag**: pan
- **+/-/0 keys**: zoom in/out/reset
- Zoom indicator overlay shows current percentage and control hints

### Hit Testing
```typescript
hitTestStar(
  galaxy: Galaxy, x: number, y: number, w: number, h: number,
  zoom: number, panX: number, panY: number
): number | null
```

---

## EVENT LOG MODAL (EventLogModal.tsx)

Shown automatically after `endTurn()` when events or AI actions exist. Blocks interaction until dismissed.

Features:
- Player events with type-specific icons and color-coded borders
- AI actions section showing what each AI player did
- "Continue (Esc)" and "Full Summary" buttons
- Dismissable with Escape key

---

## API CLIENT (api/client.ts)

All backend calls go through `api/client.ts`. Functions organized by resource:

```typescript
// Auth
login(username, password): Promise<{token}>
register(username, password): Promise<{token}>

// Game
createGame(token, opts): Promise<GameData>
getGame(token, gameId): Promise<GameData>
listGames(token): Promise<GameSummary[]>
deleteGame(token, gameId): Promise<void>
endTurn(token, gameId): Promise<{turn, events, combat_results, ai_actions}>

// Galaxy
getGalaxy(token, gameId): Promise<Galaxy>
getStarDetail(token, gameId, starIdx): Promise<StarDetail>

// Colony, Fleet, Research, Diplomacy, Ship Design, Leaders, Espionage, Combat, Cheat...
```

Base URL: resolved at runtime from `window.location.origin` (nginx proxies `/api/` to backend).

---

## STYLING CONVENTIONS

- **No CSS files**: All styles are inline `style={{...}}` objects
- **Color palette**: Dark space theme (#0a0a2e background, #1a1a3e panels, cyan/gold accents)
- **Font**: monospace or system fonts
- **Canvas**: Full-panel rendering, no DOM overlays except zoom indicator
- **Responsive**: Not required (desktop-only game)

---

## KEY CONVENTIONS

1. **State-based routing** — No React Router, no URL paths. `useUIStore.activeScreen` drives rendering
2. **Two stores** — `gameStore` for game data + API calls, `uiStore` for UI state
3. **Canvas for maps** — Galaxy and combat use Canvas 2D, not SVG or DOM
4. **Token in store** — JWT stored in `gameStore.token`, passed to all API calls
5. **Auto-refresh** — After `endTurn()`, `loadGame()` and `fetchGalaxy()` are called automatically
6. **Event-driven modals** — `EventLogModal` auto-opens when turn events exist
7. **Inline styles only** — No external CSS, no CSS modules, no Tailwind

---

## CHECKLIST

- [x] Login/Register on MainMenu
- [x] Game creation with race selection, AI config, galaxy settings
- [x] Game list with card grid layout and delete
- [x] Galaxy map with Canvas2D rendering
- [x] Zoom (scroll/keys 0.5-4×) and pan (shift+drag)
- [x] Star selection with sidebar details
- [x] Colony management (population, buildings, build queue)
- [x] Research screen (8 fields, tech selection)
- [x] Fleet management (move, colonize, split)
- [x] Ship designer (hull, weapons, specials)
- [x] Diplomacy (relations, treaties, war)
- [x] Leaders (hire, assign, unassign)
- [x] Espionage (recruit, missions)
- [x] Tactical combat (12×12 canvas grid)
- [x] End turn with spinner overlay
- [x] Event log modal (auto-show after turn)
- [x] AI action visualization in event log
- [x] Turn summary (events, victory/defeat)
- [x] Galactic Council voting
- [x] Keyboard shortcuts (15+ bindings)
- [x] Cheat console (Ctrl+Tab)
- [x] TopBar navigation
- [x] Dark space theme
- [x] Fleet List screen (F key, sortable table)
- [x] Fleet split UI (select ships, create new fleet)
- [x] Build queue reorder (▲/▼ buttons per item)
- [x] Smooth zoom (requestAnimationFrame + lerp toward cursor, 0.3×–6×)
- [x] Spiral galaxy background (procedural 4-arm Milky Way, 2048px cached texture)
- [x] Planet max_pop display in SystemView (from backend enrichment)
- [x] Colony List screen (C key, sortable table)
