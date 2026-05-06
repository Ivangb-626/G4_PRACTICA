<template>
  <section class="game-shell retro-panel game-layout-wrapper">
    <div class="main-column">
      <header class="hud">
        <div>
          <p class="eyebrow">Partida activa</p>
          <h2>{{ gameState?.name || `Partida ${gameId}` }}</h2>
          <p class="subtitle">
            Turno {{ status?.turn || gameState?.turn || '-' }} · {{ gameState?.player.race.name || '-' }} ·
            {{ gameState?.galaxy.size || '-' }}
          </p>
        </div>

        <div class="hud-actions">
          <button class="retro-btn" type="button" @click="reloadGame" :disabled="loading">
            {{ loading ? 'Cargando...' : 'Recargar' }}
          </button>
          <button class="retro-btn" type="button" @click="saveCurrentGame" :disabled="saving">
            {{ saving ? 'Guardando...' : 'Guardar' }}
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
        <router-link :to="`/game/${gameId}/tech`" class="tab-btn">Tecnologia</router-link>
        <router-link :to="`/game/${gameId}/fleets`" class="tab-btn">Flotas</router-link>
        <router-link :to="`/game/${gameId}/diplomacy`" class="tab-btn">Diplomacia</router-link>
      </nav>
    </div>

    <aside class="sidebar-column">
      <section class="summary-grid">
        <article class="summary-card">
          <span class="summary-label">BC</span>
          <strong>{{ formatNumber(status?.resources?.bc) }}</strong>
        </article>
        <article class="summary-card">
          <span class="summary-label">Colonias</span>
          <strong>{{ status?.colonies_count ?? gameState?.player.colonies.length ?? '-' }}</strong>
        </article>
        <article class="summary-card">
          <span class="summary-label">Flotas</span>
          <strong>{{ status?.fleets_count ?? gameState?.player.fleets.length ?? '-' }}</strong>
        </article>
        <article class="summary-card">
          <span class="summary-label">Poblacion</span>
          <strong>{{ status?.total_population ?? '-' }}</strong>
        </article>
        <article class="summary-card">
          <span class="summary-label">Investigacion</span>
          <strong>{{ status?.current_research?.tech_id || 'Sin proyecto' }}</strong>
        </article>
        <article class="summary-card">
          <span class="summary-label">Condicion</span>
          <strong>{{ status?.victory_condition || 'En curso' }}</strong>
        </article>
      </section>
    </aside>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../services/api'
import type { AIActionSummary, GameState, TurnEvent } from '../types/game'

const route = useRoute()
const gameId = computed(() => String(route.params.id || ''))

const gameState = ref<GameState | null>(null)
const status = ref<Record<string, any> | null>(null)
const turnEvents = ref<TurnEvent[]>([])
const aiActions = ref<AIActionSummary[]>([])
const refreshKey = ref(0)
const loading = ref(false)
const saving = ref(false)
const endingTurn = ref(false)
const error = ref('')

function formatNumber(value?: number) {
  if (value === undefined || value === null) return '-'
  return Number(value).toLocaleString()
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
    const [gameResponse, statusResponse] = await Promise.all([
      api.loadGame(gameId.value),
      api.getStatus(gameId.value),
    ])
    gameState.value = gameResponse?.game_state || null
    status.value = statusResponse || null
    refreshKey.value += 1
  } catch (err) {
    error.value = (err as Error).message || 'No se pudo cargar la partida.'
  } finally {
    loading.value = false
  }
}

async function saveCurrentGame() {
  saving.value = true
  error.value = ''
  try {
    await api.saveGame(gameId.value)
    await reloadGame()
  } catch (err) {
    error.value = (err as Error).message || 'No se pudo guardar la partida.'
  } finally {
    saving.value = false
  }
}

async function runEndTurn() {
  endingTurn.value = true
  error.value = ''
  try {
    const response = await api.endTurn(gameId.value)
    turnEvents.value = Array.isArray(response?.events) ? response.events : []
    aiActions.value = Array.isArray(response?.ai_actions) ? response.ai_actions : []
    await reloadGame()
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

onMounted(reloadGame)
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
