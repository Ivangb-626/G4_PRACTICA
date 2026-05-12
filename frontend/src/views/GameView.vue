<template>
  <section class="game-shell retro-panel game-layout-wrapper">
    <div class="main-column">
      <header class="hud">
        <div>
          <p class="eyebrow">Partida activa</p>
          <h2>{{ gameState?.name || `Partida ${gameId}` }}</h2>
          <p class="subtitle">
            Turno {{ gameState?.turn || '-' }} · {{ gameState?.player?.race?.name || '-' }} ·
            {{ gameState?.galaxy_size || gameState?.galaxy?.size || '-' }}
          </p>
        </div>

        <div class="hud-actions">
          <button class="retro-btn secondary" type="button" @click="goBack" title="Atajo: B">
            Volver
          </button>
          <button class="retro-btn" type="button" @click="reloadGame" :disabled="loading">
            {{ loading ? 'Cargando...' : 'Recargar' }}
          </button>
          <button class="retro-btn" type="button" @click="uiStore.openEventLog" title="Atajo: O">
            Log
          </button>
          <button class="retro-btn" type="button" @click="uiStore.toggleShortcuts" title="Atajo: ?">
            Ayuda
          </button>
          <label class="speed-control" title="Atajos: 1 lenta, 2 normal, 3 rapida">
            Velocidad
            <select v-model="uiStore.gameSpeed">
              <option value="lenta">Lenta</option>
              <option value="normal">Normal</option>
              <option value="rapida">Rapida</option>
            </select>
          </label>
          <button
            class="retro-btn end-turn-btn"
            :class="{ 'is-ready': turnReady, 'is-blocked': !canEndTurn }"
            type="button"
            @click="requestEndTurn"
            :disabled="endingTurn || !canEndTurn"
            :title="endTurnTitle"
          >
            {{ endingTurn ? 'Procesando...' : endTurnButtonLabel }}
          </button>
        </div>
      </header>

      <nav class="quick-nav" aria-label="Accesos rapidos">
        <div class="quick-nav-group tactical-group">
          <span class="nav-group-label">Prioridad tactica</span>
        <router-link
          v-for="item in primaryNavItems"
          :key="item.to"
          :to="item.to"
          class="quick-nav-item"
          :class="navAttentionClass(item.id)"
          :title="`Atajo: ${item.key}`"
        >
          <span>{{ item.label }}</span>
          <kbd>{{ item.key }}</kbd>
        </router-link>
        <button
          type="button"
          class="quick-nav-item"
          :class="navAttentionClass('construction')"
          @click="showColoniesModal = true"
          title="Atajo: C"
        >
          <span>Colonias</span>
          <kbd>C</kbd>
        </button>
        </div>
        <div class="quick-nav-group advanced-group">
          <span class="nav-group-label">Avanzado</span>
          <router-link
            v-for="item in advancedNavItems"
            :key="item.to"
            :to="item.to"
            class="quick-nav-item advanced-item"
            :class="navAttentionClass(item.id)"
            :title="`Atajo: ${item.key}`"
          >
            <span>{{ item.label }}</span>
            <kbd>{{ item.key }}</kbd>
          </router-link>
        </div>
      </nav>

      <p v-if="error" class="error">{{ error }}</p>

      <section class="turn-readiness" :class="{ 'is-ready': turnReady, 'is-blocked': !canEndTurn }">
        <header class="readiness-head">
          <div>
            <p class="side-kicker">Estado del turno</p>
            <strong>{{ readinessTitle }}</strong>
          </div>
          <button class="retro-btn small-btn" type="button" @click="refreshTurnStatus" :disabled="loading">
            Verificar
          </button>
        </header>

        <div v-if="turnBlockers.length" class="readiness-list blockers">
          <strong>Bloqueos</strong>
          <p v-for="item in turnBlockers" :key="item">{{ item }}</p>
        </div>

        <div class="readiness-grid">
          <div class="readiness-list">
            <strong>Acciones disponibles</strong>
            <p v-for="action in prioritizedActions" :key="`${action.type}-${action.label}`">
              {{ action.label }} <span v-if="action.count">({{ action.count }})</span>
              <small>{{ action.reason }}</small>
            </p>
            <p v-if="!prioritizedActions.length" class="muted-line">No hay acciones criticas pendientes.</p>
          </div>

          <div class="readiness-list">
            <strong>Log previsto al pasar turno</strong>
            <p v-for="item in turnPreviewLog" :key="item.message">{{ item.message }}</p>
          </div>
        </div>

        <div v-if="turnWarnings.length" class="readiness-list warnings">
          <strong>Avisos</strong>
          <p v-for="item in turnWarnings.slice(0, 4)" :key="item">{{ item }}</p>
        </div>
      </section>

      <section v-if="turnEvents.length || aiActions.length" class="turn-report">
        <header class="turn-report-head">
          <h3>Ultimo turno resuelto</h3>
          <div class="turn-report-actions">
            <button class="retro-btn" type="button" @click="uiStore.openEventLog">Ver log completo</button>
            <button class="retro-btn" type="button" @click="clearTurnReport">Ocultar</button>
          </div>
        </header>

        <div v-if="turnEvents.length" class="event-list">
          <article v-for="(event, index) in turnEvents" :key="`${String(event.type)}-${index}`" class="event-card">
            <span class="event-icon">{{ eventIcon(event.type) }}</span>
            <p class="event-text">{{ describeEvent(event) }}</p>
          </article>
        </div>

        <div v-if="aiActions.length" class="ai-actions">
          <article v-for="report in aiActions" :key="report.ai_id" class="ai-card">
            <header class="ai-card-head">
              <strong>{{ aiName(report.ai_id) }}</strong>
              <span class="ai-personality">{{ personalityLabel(report.personality) }}</span>
            </header>
            <p class="reasoning">{{ report.reasoning || 'Sin novedades.' }}</p>
            <ul v-if="report.actions?.length" class="ai-action-list">
              <li v-for="(action, index) in report.actions" :key="index">
                {{ describeAiAction(action) }}
              </li>
            </ul>
          </article>
        </div>
      </section>

      <router-view :key="refreshKey" />

      <nav class="tabs">
        <router-link v-for="item in navItems" :key="`tab-${item.to}`" :to="item.to" class="tab-btn">
          {{ item.label }}
        </router-link>
        <button type="button" class="tab-btn" @click="showColoniesModal = true">Colonias</button>
        <router-link
          v-if="gameStore.isGameOver"
          :to="`/game/${gameId}/score`"
          class="tab-btn"
        >
          Puntuacion
        </router-link>
        <router-link v-if="isDev" :to="`/game/${gameId}/cheats`" class="tab-btn">Cheats</router-link>
      </nav>
    </div>

    <aside class="sidebar-column">
      <section class="summary-grid">
        <article class="summary-card">
          <span class="summary-label">BC</span>
          <strong>{{ formatNumber(gameState?.player?.resources?.bc) }}</strong>
        </article>
        <article class="summary-card">
          <span class="summary-label">Comida</span>
          <strong>{{ formatNumber(gameState?.player?.resources?.total_food_surplus) }}</strong>
        </article>
        <article class="summary-card">
          <span class="summary-label">Colonias</span>
          <strong>{{ gameState?.player?.colonies?.length ?? '-' }}</strong>
        </article>
        <article class="summary-card">
          <span class="summary-label">Flotas</span>
          <strong>{{ gameState?.player?.fleets?.length ?? '-' }}</strong>
        </article>
        <article class="summary-card">
          <span class="summary-label">Poblacion</span>
          <strong>{{ totalPopulation }}</strong>
        </article>
        <article class="summary-card">
          <span class="summary-label">Investigacion</span>
          <strong>{{ gameState?.player?.technologies?.current_research?.tech_id || 'Sin proyecto' }}</strong>
        </article>
        <article class="summary-card">
          <span class="summary-label">Condicion</span>
          <strong>{{ gameState?.victory_condition || 'En curso' }}</strong>
        </article>
      </section>

      <section class="side-panel" v-if="selectedSystem">
        <p class="side-kicker">Seleccionado</p>
        <strong>{{ selectedSystem.name }}</strong>
        <small>{{ selectedSystem.star_type }} · {{ selectedSystem.planets?.length || 0 }} planeta(s)</small>
        <router-link class="side-link" :to="`/game/${gameId}/system/${selectedSystem.id}`">Abrir sistema</router-link>
      </section>

      <section class="side-panel">
        <p class="side-kicker">Imperio vs rival</p>
        <div class="compare-row">
          <span>Colonias</span>
          <strong>{{ empireComparison.playerColonies }}</strong>
          <strong>{{ empireComparison.enemyColonies }}</strong>
        </div>
        <div class="compare-row">
          <span>Flotas</span>
          <strong>{{ empireComparison.playerFleets }}</strong>
          <strong>{{ empireComparison.enemyFleets }}</strong>
        </div>
        <div class="compare-row">
          <span>Poblacion</span>
          <strong>{{ empireComparison.playerPopulation }}</strong>
          <strong>{{ empireComparison.enemyPopulation }}</strong>
        </div>
        <small class="side-note">Izquierda: tu imperio. Derecha: rival mas fuerte detectado.</small>
      </section>

      <section class="side-panel tutorial-card" v-if="showTutorial">
        <p class="side-kicker">Tutorial rapido</p>
        <strong>{{ tutorialStep.title }}</strong>
        <p>{{ tutorialStep.body }}</p>
        <div class="tutorial-actions">
          <button class="retro-btn small-btn" type="button" @click="nextTutorialStep">Siguiente</button>
          <button class="retro-btn small-btn" type="button" @click="dismissTutorial">Ocultar</button>
        </div>
      </section>
    </aside>

    <!-- Modal Colonias -->
    <div v-if="showColoniesModal" class="modal-overlay">
      <div class="modal-content retro-panel">
        <header class="modal-header">
          <h3>Mis Colonias</h3>
          <button class="close-btn" @click="showColoniesModal = false">×</button>
        </header>

        <input
          v-model.trim="colonyQuery"
          class="modal-search"
          placeholder="Filtrar por nombre, sistema o poblacion..."
          type="search"
        />

        <ul class="colonies-list" v-if="filteredColonies.length">
          <li v-for="col in filteredColonies" :key="col.id" class="colony-item">
            <div class="colony-info">
              <strong>{{ colonyLabel(col) }}</strong>
              <small>Industria {{ col.industry_output || 0 }} · Ciencia {{ col.research_output || 0 }}</small>
              <small v-if="col.population">Población: {{ col.population.total }} / {{ col.population.max }}</small>
            </div>
            <router-link :to="`/game/${gameId}/colony/${col.id}`" class="retro-btn small-btn" @click="showColoniesModal = false">Gestionar</router-link>
          </li>
        </ul>
        <p v-else class="empty">No hay colonias que coincidan con el filtro.</p>
      </div>
    </div>

    <div v-if="endingTurn" class="turn-overlay">
      <div class="turn-pulse"></div>
      <strong>Procesando turno {{ gameState?.turn || '-' }}</strong>
      <span>{{ turnPhaseLabel }}</span>
    </div>

    <div v-if="confirmEndTurnOpen" class="modal-overlay">
      <div class="modal-content retro-panel confirm-modal">
        <header class="modal-header">
          <h3>Confirmar fin de turno</h3>
          <button class="close-btn" type="button" @click="confirmEndTurnOpen = false">Ã—</button>
        </header>
        <p class="confirm-copy">{{ turnReady ? 'Todo listo. Consecuencias inmediatas:' : 'Puedes avanzar, pero quedan avisos tacticos:' }}</p>
        <div v-if="turnWarnings.length" class="confirm-warning">
          <strong>Avisos activos</strong>
          <p v-for="item in turnWarnings.slice(0, 3)" :key="item">{{ item }}</p>
        </div>
        <ul class="impact-list">
          <li v-for="impact in endTurnPreview" :key="impact">{{ impact }}</li>
        </ul>
        <div class="confirm-actions">
          <button class="retro-btn secondary" type="button" @click="confirmEndTurnOpen = false">Cancelar</button>
          <button class="retro-btn end-turn-btn" type="button" @click="runEndTurn" :disabled="endingTurn">
            Avanzar turno
          </button>
        </div>
      </div>
    </div>

    <div v-if="uiStore.shortcutsOpen" class="modal-overlay">
      <div class="modal-content retro-panel shortcuts-modal">
        <header class="modal-header">
          <h3>Atajos y controles</h3>
          <button class="close-btn" type="button" @click="uiStore.closeShortcuts">Ã—</button>
        </header>
        <div class="shortcut-grid">
          <span v-for="shortcut in shortcuts" :key="shortcut.key" class="shortcut-row">
            <kbd>{{ shortcut.key }}</kbd>
            <strong>{{ shortcut.label }}</strong>
          </span>
        </div>
      </div>
    </div>

    <EventLogPanel />
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useGameStore } from '../store/gameStore'
import { useUIStore } from '../store/uiStore'
import EventLogPanel from './EventLogPanel.vue'
import type { AIActionSummary, TurnEvent } from '../types/game'

const route = useRoute()
const router = useRouter()
const gameStore = useGameStore()
const uiStore = useUIStore()
const gameId = computed(() => String(route.params.id || ''))

const gameState = computed<any>(() => gameStore.game)
const turnEvents = ref<TurnEvent[]>([])
const aiActions = ref<AIActionSummary[]>([])
const refreshKey = ref(0)
const loading = ref(false)
const endingTurn = ref(false)
const error = ref('')
const showColoniesModal = ref(false)
const colonyQuery = ref('')
const confirmEndTurnOpen = ref(false)
const tutorialIndex = ref(0)
const tutorialDismissed = ref(localStorage.getItem('moo2_ux_tutorial_dismissed') === '1')
const isDev = true  // Cheats enabled
const turnStatus = computed<any>(() => gameStore.turnStatus || {})
const turnBlockers = computed<string[]>(() => turnStatus.value?.blockers || [])
const turnWarnings = computed<string[]>(() => turnStatus.value?.warnings || [])
const turnReady = computed(() => Boolean(turnStatus.value?.ready))
const canEndTurn = computed(() => turnStatus.value?.can_end_turn !== false)
const prioritizedActions = computed<any[]>(() => turnStatus.value?.tactical_actions || [])
const turnPreviewLog = computed<any[]>(() => turnStatus.value?.preview_events || [])
const endTurnButtonLabel = computed(() => {
  if (!canEndTurn.value) return 'Turno bloqueado'
  return turnReady.value ? 'Pasar turno' : 'Pasar turno con avisos'
})
const endTurnTitle = computed(() => {
  if (turnBlockers.value.length) return turnBlockers.value[0]
  if (turnWarnings.value.length) return turnWarnings.value[0]
  return 'Todo listo para pasar turno'
})
const readinessTitle = computed(() => {
  if (!canEndTurn.value) return 'No se puede avanzar'
  if (turnReady.value) return 'Todo listo para pasar turno'
  return 'Turno jugable con avisos pendientes'
})

const totalPopulation = computed(() => {
  const cols = gameState.value?.player?.colonies || []
  const total = cols.reduce((acc: number, c: any) => acc + (c?.population?.total || 0), 0)
  return total || '-'
})

const primaryNavItems = computed(() => [
  { id: 'diplomacy', label: 'Diplomacia', key: 'D', to: `/game/${gameId.value}/diplomacy` },
  { id: 'combat', label: 'Combate', key: 'F', to: `/game/${gameId.value}/fleets` },
  { id: 'map', label: 'Mapa', key: 'M', to: `/game/${gameId.value}/galaxy` },
  { id: 'research', label: 'Tech', key: 'R', to: `/game/${gameId.value}/tech` },
])

const advancedNavItems = computed(() => [
  { id: 'ship-design', label: 'Disenador', key: 'S', to: `/game/${gameId.value}/ships` },
  { id: 'espionage', label: 'Espionaje', key: 'E', to: `/game/${gameId.value}/espionage` },
  { id: 'leaders', label: 'Lideres', key: 'L', to: `/game/${gameId.value}/leaders` },
  { id: 'council', label: 'Senado', key: '-', to: `/game/${gameId.value}/council` },
])

const navItems = computed(() => [...primaryNavItems.value, ...advancedNavItems.value])

const shortcuts = [
  { key: 'M', label: 'Abrir mapa galactico' },
  { key: 'C', label: 'Abrir lista de colonias' },
  { key: 'F', label: 'Gestionar flotas' },
  { key: 'R', label: 'Investigacion' },
  { key: 'D/E/L/S', label: 'Diplomacia, espionaje, lideres, disenador' },
  { key: 'T', label: 'Confirmar fin de turno' },
  { key: 'O', label: 'Abrir log del turno' },
  { key: 'B', label: 'Volver atras' },
  { key: '1/2/3', label: 'Velocidad lenta, normal o rapida' },
  { key: 'Esc', label: 'Cerrar paneles y modales' },
]

const selectedSystem = computed(() => {
  const id = uiStore.selectedSystemId
  const systems = gameState.value?.galaxy?.star_systems || gameStore.galaxy?.star_systems || []
  return id ? systems.find((system: any) => system.id === id) || null : null
})

const filteredColonies = computed(() => {
  const colonies = gameState.value?.player?.colonies || []
  const query = colonyQuery.value.toLowerCase()
  if (!query) return colonies
  return colonies.filter((colony: any) => {
    const system = (gameState.value?.galaxy?.star_systems || []).find((s: any) => s.id === colony?.star_system_id)
    const haystack = [
      colonyLabel(colony),
      colony?.id,
      colony?.name,
      system?.name,
      String(colony?.population?.total || ''),
    ].join(' ').toLowerCase()
    return haystack.includes(query)
  })
})

const empireComparison = computed(() => {
  const aiPlayers = gameState.value?.ai_players || gameState.value?.aiPlayers || []
  const enemies = Array.isArray(aiPlayers) ? aiPlayers : []
  const strongest = [...enemies].sort((a: any, b: any) => {
    const aScore = (a?.colonies?.length || 0) * 3 + (a?.fleets?.length || 0)
    const bScore = (b?.colonies?.length || 0) * 3 + (b?.fleets?.length || 0)
    return bScore - aScore
  })[0] || {}
  const player = gameState.value?.player || {}
  return {
    playerColonies: player?.colonies?.length ?? '-',
    enemyColonies: strongest?.colonies?.length ?? '-',
    playerFleets: player?.fleets?.length ?? '-',
    enemyFleets: strongest?.fleets?.length ?? '-',
    playerPopulation: totalPopulation.value,
    enemyPopulation: populationTotal(strongest?.colonies || []),
  }
})

const endTurnPreview = computed(() => {
  const impacts = turnPreviewLog.value.map((item: any) => item.message).filter(Boolean)
  if (!impacts.length) {
    impacts.push('Se procesaran produccion, investigacion, movimientos de flotas y acciones de IA.')
  }
  impacts.push(`Colonias activas: ${gameState.value?.player?.colonies?.length || 0}. Flotas activas: ${gameState.value?.player?.fleets?.length || 0}.`)
  return impacts
})

const turnPhaseLabel = computed(() => {
  const speed = uiStore.gameSpeed
  if (speed === 'lenta') return 'Animacion lenta: mostrando movimientos y resoluciones.'
  if (speed === 'rapida') return 'Animacion rapida: saltando pausas no esenciales.'
  return 'Resolviendo economia, IA y eventos importantes.'
})

const tutorialSteps = [
  {
    title: '1. Empieza por el mapa',
    body: 'Pulsa M, selecciona una estrella y revisa planetas, flotas y rango antes de mover nada.',
  },
  {
    title: '2. Revisa colonias',
    body: 'Pulsa C para abrir la lista filtrable. En cada colonia puedes previsualizar comida, industria y ciencia antes de aplicar.',
  },
  {
    title: '3. Avanza con control',
    body: 'Pulsa T para abrir la confirmacion de fin de turno. El log O resume consecuencias y acciones rivales.',
  },
]

const showTutorial = computed(() => !tutorialDismissed.value && Number(gameState.value?.turn || 1) <= 2)
const tutorialStep = computed(() => tutorialSteps[tutorialIndex.value] || tutorialSteps[0])

function formatNumber(value?: number) {
  if (value === undefined || value === null) return '-'
  return Number(value).toLocaleString()
}

function populationTotal(colonies: any[]) {
  if (!Array.isArray(colonies) || !colonies.length) return '-'
  const total = colonies.reduce((acc: number, colony: any) => acc + (colony?.population?.total || 0), 0)
  return total || '-'
}

function colonyLabel(colony: any) {
  const systems = gameState.value?.galaxy?.star_systems || []
  const system = systems.find((s: any) => s.id === colony?.star_system_id)
  const planetName = system?.planets?.[colony?.planet_index]?.name || colony?.planet_name || colony?.name || ''
  if (!planetName) return 'Colonia'
  if (/^Colonia:\s*".*"$/.test(colony?.name || '')) return colony.name
  return `Colonia: "${planetName}"`
}

function ownerLabel(owner: unknown) {
  if (typeof owner !== 'string' || !owner) return 'Desconocido'
  if (owner === 'player') return 'Tu imperio'
  if (owner.startsWith('ai_')) return `IA ${owner.slice(3)}`
  return owner.charAt(0).toUpperCase() + owner.slice(1)
}

function aiName(id: unknown) {
  if (typeof id !== 'string' || !id) return 'Imperio rival'
  if (id.startsWith('ai_')) return `Imperio rival ${id.slice(3)}`
  return id
}

function personalityLabel(personality: unknown) {
  return ({
    aggressive: 'Agresivo',
    defensive: 'Defensivo',
    expansionist: 'Expansionista',
    researcher: 'Investigador',
    balanced: 'Equilibrado',
  } as Record<string, string>)[String(personality || '')] || 'Equilibrado'
}

function eventIcon(type: unknown) {
  return ({
    building_complete: '[C]',
    ship_complete: '[N]',
    research_complete: '[I]',
    fleet_arrival: '[F]',
    combat_resolved: '[X]',
    ai_research_selected: '[i]',
    ai_colonized: '[c]',
    ai_fleet_moved: '[f]',
    ai_build_order: '[p]',
    tribute_paid: '[$]',
    peace_expired: '[!]',
    council_convened: '[*]',
    antarans_escaped: '[!]',
    antaran_attack: '[!]',
  } as Record<string, string>)[String(type || '')] || '[*]'
}

function describeEvent(event: any) {
  const type = String(event?.type || '')
  switch (type) {
    case 'building_complete':
      return `Construccion completada: ${event.building_id || 'edificio'} en ${event.colony_id || 'una colonia'}.`
    case 'ship_complete':
      return `Nueva nave lista: ${event.ship_type || 'desconocida'} en ${event.colony_id || 'una colonia'}.`
    case 'research_complete':
      return `${ownerLabel(event.owner)} ha completado la investigacion ${event.tech_id || 'desconocida'}.`
    case 'fleet_arrival':
      return `Flota ${event.fleet_id || ''} de ${ownerLabel(event.owner)} llega al sistema ${event.system_id || ''}.`
    case 'combat_resolved': {
      const winner = event.winner ? ownerLabel(event.winner) : 'el ganador'
      const loc = event.system_id || event.location || 'un sistema'
      return `Combate resuelto en ${loc}: ${winner} se impone.`
    }
    case 'ai_research_selected':
      return `${ownerLabel(event.owner)} inicia la investigacion ${event.tech_id || 'desconocida'}.`
    case 'ai_colonized':
      return `${ownerLabel(event.owner)} funda la colonia ${event.colony_id || ''}.`
    case 'ai_fleet_moved':
      return `${ownerLabel(event.owner)} reposiciona la flota ${event.fleet_id || ''}.`
    case 'ai_build_order':
      return `${ownerLabel(event.owner)} pone en cola ${event.item_id || 'una unidad'}.`
    case 'tribute_paid':
      return `${ownerLabel(event.from)} paga ${event.amount || 0} BC de tributo a ${ownerLabel(event.to)}.`
    case 'peace_expired': {
      const a = Array.isArray(event.between) ? event.between.map(ownerLabel).join(' y ') : 'dos imperios'
      return `Expira el tratado de paz entre ${a}.`
    }
    case 'council_convened':
      return 'El Consejo Galactico se reune.'
    case 'antarans_escaped':
      return event.message || 'Los Antaranos han escapado de su dimension.'
    case 'antaran_attack':
      return `Ataque antarano sobre ${event.target || 'tu imperio'}.`
    case 'victory_military':
      return 'Victoria militar conseguida.'
    case 'victory_diplomatic':
      return 'Victoria diplomatica conseguida.'
    case 'victory_economic':
      return 'Victoria economica conseguida.'
    default:
      if (type.startsWith('victory')) return `Condicion de victoria: ${type.replace('victory_', '')}.`
      return `Evento: ${type.replaceAll('_', ' ') || 'sin tipo'}.`
  }
}

function describeAiAction(action: any) {
  const type = String(action?.type || '')
  const d = action?.details || {}
  switch (type) {
    case 'colonizePlanet':
      return `Coloniza el planeta ${d.planetIndex ?? '?'} con la flota ${d.fleetId || '?'}.`
    case 'selectResearch':
      return `Selecciona investigacion: ${d.techId || d.field || 'desconocida'}.`
    case 'addBuildQueue': {
      const kind = d.itemType === 'ship' ? 'nave' : 'edificio'
      return `Encola ${kind} ${d.itemId || ''} en ${d.colonyId || 'una colonia'}.`
    }
    case 'moveFleet':
      return `Mueve la flota ${d.fleetId || ''} hacia ${d.destination || 'un sistema'}.`
    case 'endTurn':
      return 'Finaliza su turno.'
    default:
      return `Accion: ${type.replaceAll('_', ' ') || 'desconocida'}.`
  }
}

function clearTurnReport() {
  turnEvents.value = []
  aiActions.value = []
}

function navAttentionClass(id: string) {
  const actionTypes = new Set(prioritizedActions.value.map((action: any) => String(action.type || '')))
  const map: Record<string, string[]> = {
    diplomacy: ['diplomacy'],
    construction: ['construction', 'colonize'],
    combat: ['combat', 'colonize'],
    research: ['research'],
    map: ['colonize'],
  }
  return {
    'is-attention': (map[id] || []).some((type) => actionTypes.has(type)),
  }
}

async function refreshTurnStatus() {
  if (!gameStore.gameId) return
  try {
    await gameStore.fetchTurnStatus()
  } catch {
    /* status panel is advisory; keep the last known state */
  }
}

function requestEndTurn() {
  if (!canEndTurn.value) {
    error.value = turnBlockers.value[0] || 'No se puede pasar el turno.'
    return
  }
  confirmEndTurnOpen.value = true
}

function goBack() {
  router.back()
}

function nextTutorialStep() {
  tutorialIndex.value = (tutorialIndex.value + 1) % tutorialSteps.length
}

function dismissTutorial() {
  tutorialDismissed.value = true
  localStorage.setItem('moo2_ux_tutorial_dismissed', '1')
}

async function reloadGame() {
  loading.value = true
  error.value = ''
  try {
    await gameStore.loadGame(gameId.value)
    refreshKey.value += 1
  } catch (err) {
    error.value = (err as Error).message || 'No se pudo cargar la partida.'
  } finally {
    loading.value = false
  }
}

async function runEndTurn() {
  confirmEndTurnOpen.value = false
  endingTurn.value = true
  error.value = ''
  const startedAt = Date.now()
  try {
    const response = await gameStore.endTurn()
    turnEvents.value = Array.isArray(response?.events) ? response.events : []
    aiActions.value = Array.isArray(response?.ai_actions) ? response.ai_actions : []
    refreshKey.value += 1
    uiStore.openEventLog()
  } catch (err) {
    error.value = (err as Error).message || 'No se pudo finalizar el turno.'
  } finally {
    const minDelay = uiStore.gameSpeed === 'lenta' ? 700 : uiStore.gameSpeed === 'rapida' ? 80 : 300
    const remaining = minDelay - (Date.now() - startedAt)
    if (remaining > 0) await new Promise((resolve) => setTimeout(resolve, remaining))
    endingTurn.value = false
  }
}

watch(
  () => route.params.id,
  async () => {
    clearTurnReport()
    await reloadGame()
  },
)

const handleRequestEndTurn = () => requestEndTurn()
const handleOpenColonies = () => {
  showColoniesModal.value = true
}
const handleEscape = () => {
  showColoniesModal.value = false
  confirmEndTurnOpen.value = false
}

onMounted(async () => {
  window.addEventListener('ux:request-end-turn', handleRequestEndTurn)
  window.addEventListener('ux:open-colonies', handleOpenColonies)
  window.addEventListener('ux:escape', handleEscape)
  // Skip reload if store already has this game cached (avoids hammering the backend on tab navigation).
  if (gameStore.gameId === gameId.value && gameStore.game) {
    refreshKey.value += 1
    await refreshTurnStatus()
    return
  }
  await reloadGame()
})

onUnmounted(() => {
  window.removeEventListener('ux:request-end-turn', handleRequestEndTurn)
  window.removeEventListener('ux:open-colonies', handleOpenColonies)
  window.removeEventListener('ux:escape', handleEscape)
})
</script>

<style scoped>
.game-shell {
  padding: 1rem;
}

.game-layout-wrapper {
  display: flex;
  flex-direction: row;
  gap: 1rem;
  align-items: stretch;
}

.main-column {
  flex: 1 1 auto;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.sidebar-column {
  flex: 0 0 220px;
  display: flex;
  flex-direction: column;
}

.hud {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  flex-wrap: wrap;
}

.eyebrow {
  margin: 0 0 0.25rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.14em;
  font-size: 0.7rem;
}

.subtitle {
  margin: 0.25rem 0 0;
  color: var(--text-muted);
}

.hud-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  align-items: center;
}

.retro-btn.secondary {
  border-color: rgba(141, 255, 159, 0.62);
}

.end-turn-btn {
  border-color: #ffeb66;
  color: #ffeb66;
  min-width: 154px;
  font-weight: 700;
}

.end-turn-btn.is-ready {
  background: rgba(255, 235, 102, 0.14);
  box-shadow: 0 0 1rem rgba(255, 235, 102, 0.22);
}

.end-turn-btn.is-blocked {
  border-color: #777;
  color: #aaa;
}

.speed-control {
  display: grid;
  gap: 0.2rem;
  color: var(--text-muted);
  font-size: 0.7rem;
  text-transform: uppercase;
}

.speed-control select,
.modal-search {
  background: var(--bg-0);
  color: var(--primary);
  border: 1px solid var(--primary);
  padding: 0.4rem 0.55rem;
  font-family: var(--font-mono);
}

.quick-nav {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(260px, 0.75fr);
  gap: 0.65rem;
  margin: 0.9rem 0;
}

.quick-nav-group {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(116px, 1fr));
  gap: 0.45rem;
  padding: 0.55rem;
  border: 1px solid rgba(51, 255, 102, 0.16);
  background: rgba(3, 18, 10, 0.45);
}

.nav-group-label {
  grid-column: 1 / -1;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.12em;
  font-size: 0.62rem;
}

.quick-nav-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
  padding: 0.45rem 0.55rem;
  border: 1px solid rgba(51, 255, 102, 0.35);
  background: rgba(3, 18, 10, 0.78);
  color: var(--text);
  font-family: var(--font-mono);
  cursor: pointer;
  text-align: left;
}

.quick-nav-item.is-attention {
  border-color: #ffeb66;
  background: rgba(80, 60, 8, 0.72);
  color: #ffeb66;
}

.quick-nav-item.advanced-item {
  opacity: 0.78;
}

.quick-nav-item:hover,
.quick-nav-item.router-link-active {
  border-color: var(--primary);
  background: rgba(51, 255, 102, 0.16);
}

.turn-readiness {
  display: grid;
  gap: 0.65rem;
  margin: 0 0 1rem;
  padding: 0.75rem;
  border: 1px solid rgba(255, 235, 102, 0.28);
  background: rgba(20, 18, 8, 0.62);
}

.turn-readiness.is-ready {
  border-color: rgba(51, 255, 102, 0.38);
  background: rgba(5, 24, 12, 0.62);
}

.turn-readiness.is-blocked {
  border-color: rgba(255, 85, 119, 0.55);
  background: rgba(42, 6, 12, 0.56);
}

.readiness-head,
.readiness-grid {
  display: grid;
  gap: 0.6rem;
}

.readiness-head {
  grid-template-columns: 1fr auto;
  align-items: center;
}

.readiness-head strong {
  color: var(--primary-strong);
}

.readiness-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.readiness-list {
  display: grid;
  gap: 0.35rem;
  padding: 0.55rem;
  border: 1px solid rgba(141, 255, 159, 0.16);
  background: rgba(0, 0, 0, 0.22);
}

.readiness-list strong {
  color: #ffeb66;
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.readiness-list p {
  margin: 0;
  color: var(--text);
  line-height: 1.35;
}

.readiness-list small {
  display: block;
  margin-top: 0.1rem;
  color: var(--text-muted);
}

.readiness-list.blockers strong,
.readiness-list.blockers p {
  color: #ff7799;
}

.readiness-list.warnings strong {
  color: #ffb266;
}

.muted-line {
  color: var(--text-muted) !important;
}

kbd {
  min-width: 1.4rem;
  padding: 0.1rem 0.3rem;
  border: 1px solid rgba(141, 255, 159, 0.45);
  color: var(--primary-strong);
  background: rgba(0, 0, 0, 0.45);
  text-align: center;
  font-family: var(--font-pixel);
  font-size: 0.55rem;
}

.summary-grid {
  margin: 0;
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.7rem;
  position: sticky;
  top: 0.5rem;
}

.summary-card {
  padding: 0.7rem 0.85rem;
  border: 1px solid rgba(89, 170, 255, 0.32);
  border-radius: 10px;
  background: linear-gradient(180deg, rgba(15, 28, 64, 0.78), rgba(6, 13, 34, 0.78));
  box-shadow: 0 0 0.6rem rgba(79, 180, 255, 0.18) inset;
  position: relative;
  overflow: hidden;
}

.summary-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background: repeating-linear-gradient(
    180deg,
    rgba(255, 255, 255, 0.04) 0,
    rgba(255, 255, 255, 0.04) 1px,
    transparent 1px,
    transparent 4px
  );
  pointer-events: none;
}

.summary-card strong {
  font-size: 1.1rem;
  color: var(--primary-strong);
  text-shadow: 0 0 0.45rem rgba(103, 240, 255, 0.55);
  font-family: monospace;
  letter-spacing: 0.04em;
}

.summary-label {
  display: block;
  margin-bottom: 0.35rem;
  color: var(--text-muted);
  text-transform: uppercase;
  font-size: 0.72rem;
  letter-spacing: 0.08em;
}

.side-panel {
  margin-top: 0.7rem;
  padding: 0.75rem;
  border: 1px solid rgba(51, 255, 102, 0.28);
  background: rgba(2, 14, 8, 0.74);
  display: grid;
  gap: 0.35rem;
}

.side-panel strong {
  color: var(--primary-strong);
}

.side-panel small,
.side-note {
  color: var(--text-muted);
  line-height: 1.3;
}

.side-kicker {
  margin: 0;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.12em;
  font-size: 0.66rem;
}

.side-link {
  width: fit-content;
  border-bottom: 1px dashed currentColor;
}

.compare-row {
  display: grid;
  grid-template-columns: 1fr auto auto;
  gap: 0.5rem;
  align-items: center;
  padding: 0.25rem 0;
  border-bottom: 1px dashed rgba(51, 255, 102, 0.16);
}

.compare-row span {
  color: var(--text-muted);
}

.tutorial-card p:not(.side-kicker) {
  margin: 0;
  color: var(--text);
  line-height: 1.35;
}

.tutorial-actions,
.turn-report-actions,
.confirm-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.tabs {
  display: flex;
  gap: 0.6rem;
  flex-wrap: wrap;
  margin-top: 0.8rem;
  justify-content: center;
}

.tab-btn {
  font-family: var(--font-pixel);
  font-size: 0.65rem;
  letter-spacing: 0.08em;
  border: 2px solid var(--primary);
  background: var(--bg-1);
  color: var(--primary);
  padding: 0.6rem 1.1rem;
  border-radius: 0;
  text-transform: uppercase;
  text-decoration: none;
  text-shadow: 0 0 0.4rem rgba(51, 255, 102, 0.55);
  box-shadow:
    0 0 0 2px var(--bg-0),
    0 0 0.5rem rgba(51, 255, 102, 0.35),
    inset -2px -2px 0 var(--green-deep),
    inset 2px 2px 0 rgba(141, 255, 159, 0.18);
  transition: transform 0.06s steps(2), background 0.1s steps(2), color 0.1s steps(2);
  image-rendering: pixelated;
}

.tab-btn:hover {
  background: var(--primary);
  color: var(--bg-0);
  text-shadow: none;
  box-shadow:
    0 0 0 2px var(--bg-0),
    0 0 0.9rem var(--primary-strong),
    inset -2px -2px 0 var(--green-mid),
    inset 2px 2px 0 rgba(255, 255, 255, 0.4);
}

.tab-btn.router-link-active {
  background: var(--primary);
  color: var(--bg-0);
  text-shadow: none;
  box-shadow:
    0 0 0 2px var(--bg-0),
    0 0 0.9rem var(--primary-strong),
    inset -2px -2px 0 var(--green-mid),
    inset 2px 2px 0 rgba(255, 255, 255, 0.4);
}

.turn-report {
  margin-bottom: 1rem;
  padding: 0.9rem;
  border: 1px solid rgba(89, 170, 255, 0.22);
  border-radius: 10px;
  background: rgba(5, 11, 29, 0.55);
}

.turn-report-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  margin-bottom: 0.9rem;
}

.event-list,
.ai-actions {
  display: grid;
  gap: 0.5rem;
}

.event-card {
  display: flex;
  align-items: flex-start;
  gap: 0.6rem;
  padding: 0.55rem 0.75rem;
  border: 1px solid var(--green-deep);
  border-left: 3px solid var(--primary);
  background: rgba(10, 30, 18, 0.7);
}

.event-icon {
  font-family: var(--font-pixel);
  font-size: 0.65rem;
  color: var(--primary-strong);
  text-shadow: 0 0 0.4rem rgba(141, 255, 159, 0.6);
  letter-spacing: 0.08em;
}

.event-text {
  margin: 0;
  color: var(--text);
  font-size: 1rem;
  line-height: 1.3;
}

.ai-card {
  padding: 0.7rem 0.85rem;
  border: 1px solid var(--green-deep);
  border-left: 3px solid var(--primary);
  background: rgba(10, 30, 18, 0.7);
}

.ai-card-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.6rem;
  margin-bottom: 0.4rem;
}

.ai-card-head strong {
  font-family: var(--font-pixel);
  font-size: 0.7rem;
  color: var(--primary-strong);
}

.ai-personality {
  font-size: 0.85rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.reasoning {
  margin: 0.3rem 0 0.4rem;
  color: var(--text);
  font-style: italic;
}

.ai-action-list {
  margin: 0;
  padding-left: 1.1rem;
  display: grid;
  gap: 0.2rem;
  color: var(--text-muted);
  font-size: 0.95rem;
}

.ai-action-list li::marker {
  color: var(--primary);
}

.error {
  color: var(--danger);
  margin-top: 0.8rem;
}

/* Modales */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  backdrop-filter: blur(2px);
}
.modal-content {
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 4px 20px rgba(0,255,255,0.2);
}

.confirm-modal,
.shortcuts-modal {
  max-width: 640px;
}

.modal-search {
  width: 100%;
  margin-bottom: 0.75rem;
}

.confirm-copy {
  margin: 0 0 0.7rem;
  color: var(--text);
}

.confirm-warning {
  margin-bottom: 0.75rem;
  padding: 0.55rem;
  border: 1px solid rgba(255, 178, 102, 0.35);
  background: rgba(64, 34, 6, 0.28);
}

.confirm-warning strong {
  color: #ffb266;
}

.confirm-warning p {
  margin: 0.25rem 0 0;
  color: var(--text);
}

.impact-list {
  margin: 0 0 1rem;
  padding-left: 1.1rem;
  display: grid;
  gap: 0.35rem;
  color: var(--text);
}

.impact-list li::marker {
  color: #ffeb66;
}

.shortcut-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
  gap: 0.45rem;
}

.shortcut-row {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.5rem;
  border: 1px solid rgba(51, 255, 102, 0.22);
  background: rgba(0, 0, 0, 0.24);
}

.shortcut-row strong {
  color: var(--text);
  font-size: 0.9rem;
}

.turn-overlay {
  position: fixed;
  inset: 0;
  z-index: 150;
  display: grid;
  place-items: center;
  align-content: center;
  gap: 0.75rem;
  background:
    radial-gradient(circle, rgba(51, 255, 102, 0.12), rgba(0, 0, 0, 0.86) 55%),
    rgba(0, 0, 0, 0.72);
  color: var(--primary-strong);
  text-align: center;
}

.turn-overlay strong {
  font-family: var(--font-pixel);
  letter-spacing: 0.08em;
}

.turn-overlay span {
  color: var(--text-muted);
}

.turn-pulse {
  width: 72px;
  height: 72px;
  border: 2px solid var(--primary);
  box-shadow: 0 0 24px rgba(51, 255, 102, 0.45), inset 0 0 24px rgba(51, 255, 102, 0.24);
  animation: turn-pulse 0.9s ease-in-out infinite alternate;
}

@keyframes turn-pulse {
  from {
    transform: scale(0.85) rotate(0deg);
    opacity: 0.55;
  }
  to {
    transform: scale(1.08) rotate(45deg);
    opacity: 1;
  }
}
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--panel-border);
  padding-bottom: 0.5rem;
  margin-bottom: 1rem;
}
.modal-header h3 {
  margin: 0;
  color: var(--primary);
}
.close-btn {
  background: transparent;
  color: var(--danger);
  border: 1px solid var(--danger);
  font-size: 1.5rem;
  cursor: pointer;
  line-height: 1;
  padding: 0 0.5rem;
  border-radius: 4px;
}
.close-btn:hover {
  background: rgba(255, 68, 68, 0.1);
}
.colonies-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.colony-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.6rem;
  background: rgba(0, 255, 255, 0.05);
  border: 1px solid rgba(0, 255, 255, 0.2);
  border-radius: 4px;
}
.colony-info strong {
  display: block;
  color: var(--text-bright);
}
.colony-info small {
  color: var(--text-muted);
  font-size: 0.8rem;
}
.small-btn {
  padding: 0.3rem 0.6rem;
  font-size: 0.8rem;
}

@media (max-width: 1080px) {
  .game-layout-wrapper {
    flex-direction: column;
  }

  .quick-nav,
  .readiness-grid {
    grid-template-columns: 1fr;
  }

  .sidebar-column {
    flex: 1 1 auto;
  }

  .summary-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    position: static;
  }
}

@media (max-width: 720px) {
  .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 520px) {
  .summary-grid {
    grid-template-columns: 1fr;
  }
}
</style>
