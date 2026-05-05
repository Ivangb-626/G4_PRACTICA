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

      <nav class="tabs">
        <router-link :to="`/game/${gameId}/galaxy`">Mapa</router-link>
        <router-link :to="`/game/${gameId}/tech`">Tecnologia</router-link>
        <router-link :to="`/game/${gameId}/fleets`">Flotas</router-link>
        <router-link :to="`/game/${gameId}/diplomacy`">Diplomacia</router-link>
      </nav>

      <section v-if="turnEvents.length || aiActions.length" class="turn-report">
        <header class="turn-report-head">
          <h3>Ultimo turno resuelto</h3>
          <button class="retro-btn" type="button" @click="clearTurnReport">Ocultar</button>
        </header>

        <div v-if="turnEvents.length" class="event-list">
          <article v-for="(event, index) in turnEvents" :key="`${String(event.type)}-${index}`" class="event-card">
            <strong>{{ prettyEventType(event.type) }}</strong>
            <pre>{{ stringifyEvent(event) }}</pre>
          </article>
        </div>

        <div v-if="aiActions.length" class="ai-actions">
          <article v-for="report in aiActions" :key="report.ai_id" class="ai-card">
            <strong>{{ report.ai_id }} · {{ report.personality }}</strong>
            <p class="reasoning">{{ report.reasoning || 'Sin detalle' }}</p>
            <ul>
              <li v-for="(action, index) in report.actions" :key="index">{{ stringifyEvent(action) }}</li>
            </ul>
          </article>
        </div>
      </section>

      <router-view :key="refreshKey" />
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

function prettyEventType(type: unknown) {
  if (typeof type !== 'string') return 'Evento'
  return type.replaceAll('_', ' ')
}

function stringifyEvent(value: unknown) {
  return JSON.stringify(value, null, 2)
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
  margin: 1rem 0;
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 0.75rem;
}

.summary-card {
  padding: 0.8rem;
  border: 1px solid rgba(89, 170, 255, 0.24);
  border-radius: 10px;
  background: rgba(6, 13, 34, 0.52);
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
  gap: 0.9rem;
  flex-wrap: wrap;
  margin-bottom: 1rem;
}

.tabs a {
  color: var(--text-muted);
  text-decoration: none;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 0.78rem;
  border-bottom: 1px solid transparent;
  padding-bottom: 0.2rem;
}

.tabs a.router-link-active {
  color: var(--primary-strong);
  border-bottom-color: var(--primary-strong);
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
  gap: 0.75rem;
}

.event-card,
.ai-card {
  padding: 0.75rem;
  border: 1px solid rgba(112, 166, 214, 0.18);
  border-radius: 8px;
  background: rgba(10, 18, 42, 0.7);
}

.event-card pre {
  margin: 0.5rem 0 0;
  white-space: pre-wrap;
  word-break: break-word;
  color: var(--text-muted);
  font-size: 0.82rem;
}

.reasoning {
  margin: 0.45rem 0;
  color: var(--text-muted);
}

.error {
  color: var(--danger);
  margin-top: 0.8rem;
}

@media (max-width: 1200px) {
  .summary-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
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
