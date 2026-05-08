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
          <button class="retro-btn" type="button" @click="reloadGame" :disabled="loading">
            {{ loading ? 'Cargando...' : 'Recargar' }}
          </button>
          <button class="retro-btn" type="button" @click="runEndTurn" :disabled="endingTurn">
            {{ endingTurn ? 'Procesando...' : 'Fin de turno' }}
          </button>
        </div>
      </header>

      <p v-if="error" class="error">{{ error }}</p>

      <section v-if="turnEvents.length || aiActions.length" class="turn-report">
        <header class="turn-report-head">
          <h3>Ultimo turno resuelto</h3>
          <button class="retro-btn" type="button" @click="clearTurnReport">Ocultar</button>
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
        <router-link :to="`/game/${gameId}/galaxy`" class="tab-btn">Mapa</router-link>
        <router-link :to="`/game/${gameId}/tech`" class="tab-btn">Tech</router-link>
        <router-link :to="`/game/${gameId}/fleets`" class="tab-btn">Flotas</router-link>
        <button type="button" class="tab-btn" @click="showColoniesModal = true">Colonias</button>
        <router-link :to="`/game/${gameId}/ships`" class="tab-btn">Disenador</router-link>
        <router-link :to="`/game/${gameId}/diplomacy`" class="tab-btn">Diplomacia</router-link>
        <router-link :to="`/game/${gameId}/espionage`" class="tab-btn">Espionaje</router-link>
        <router-link :to="`/game/${gameId}/leaders`" class="tab-btn">Lideres</router-link>
        <router-link :to="`/game/${gameId}/council`" class="tab-btn">Senado</router-link>
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
    </aside>

    <!-- Modal Colonias -->
    <div v-if="showColoniesModal" class="modal-overlay">
      <div class="modal-content retro-panel">
        <header class="modal-header">
          <h3>Mis Colonias</h3>
          <button class="close-btn" @click="showColoniesModal = false">×</button>
        </header>

        <ul class="colonies-list" v-if="gameState?.player?.colonies?.length">
          <li v-for="col in gameState.player.colonies" :key="col.id" class="colony-item">
            <div class="colony-info">
              <strong>{{ colonyLabel(col) }}</strong>
              <small v-if="col.population">Población: {{ col.population.total }} / {{ col.population.max }}</small>
            </div>
            <router-link :to="`/game/${gameId}/colony/${col.id}`" class="retro-btn small-btn" @click="showColoniesModal = false">Gestionar</router-link>
          </li>
        </ul>
        <p v-else class="empty">No tienes colonias actualmente.</p>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useGameStore } from '../store/gameStore'
import type { AIActionSummary, TurnEvent } from '../types/game'

const route = useRoute()
const gameStore = useGameStore()
const gameId = computed(() => String(route.params.id || ''))

const gameState = computed<any>(() => gameStore.game)
const turnEvents = ref<TurnEvent[]>([])
const aiActions = ref<AIActionSummary[]>([])
const refreshKey = ref(0)
const loading = ref(false)
const endingTurn = ref(false)
const error = ref('')
const showColoniesModal = ref(false)

const totalPopulation = computed(() => {
  const cols = gameState.value?.player?.colonies || []
  const total = cols.reduce((acc: number, c: any) => acc + (c?.population?.total || 0), 0)
  return total || '-'
})

function formatNumber(value?: number) {
  if (value === undefined || value === null) return '-'
  return Number(value).toLocaleString()
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
  endingTurn.value = true
  error.value = ''
  try {
    const response = await gameStore.endTurn()
    turnEvents.value = Array.isArray(response?.events) ? response.events : []
    aiActions.value = Array.isArray(response?.ai_actions) ? response.ai_actions : []
    refreshKey.value += 1
  } catch (err) {
    error.value = (err as Error).message || 'No se pudo finalizar el turno.'
  } finally {
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

onMounted(async () => {
  // Skip reload if store already has this game cached (avoids hammering the backend on tab navigation).
  if (gameStore.gameId === gameId.value && gameStore.game) {
    refreshKey.value += 1
    return
  }
  await reloadGame()
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
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--border);
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
