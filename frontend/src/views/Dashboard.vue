<template>
  <section class="dashboard-grid">
    <section class="dashboard-panel retro-panel">
      <header class="panel-head">
        <div>
          <h2>Dashboard</h2>
          <p class="subtitle">Crea una campana nueva o retoma una partida guardada.</p>
        </div>
        <button class="retro-btn" type="button" @click="loadGames" :disabled="loadingGames">
          {{ loadingGames ? 'Cargando...' : 'Refrescar' }}
        </button>
      </header>

      <p v-if="error" class="error">{{ error }}</p>

      <div v-if="games.length" class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Nombre</th>
              <th>Turno</th>
              <th>Raza</th>
              <th>Galaxia</th>
              <th>Guardado</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="game in games" :key="game.game_id">
              <td>{{ game.name }}</td>
              <td>{{ game.turn }}</td>
              <td>{{ raceLabel(game.player_race) }}</td>
              <td>{{ game.galaxy_size || '-' }}</td>
              <td>{{ formatDate(game.last_saved) }}</td>
              <td class="row-actions">
                <button class="retro-btn" type="button" @click="openGame(game.game_id)">Cargar</button>
                <button class="retro-btn retro-btn-danger" type="button" @click="removeGame(game.game_id)">
                  Eliminar
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-else-if="!loadingGames" class="empty">Todavia no hay partidas guardadas.</p>
    </section>

    <section class="dashboard-panel retro-panel">
      <header class="panel-head">
        <div>
          <h2>Nueva Partida</h2>
          <p class="subtitle">Configuracion minima para empezar rapido.</p>
        </div>
      </header>

      <form class="create-form" @submit.prevent="createNewGame">
        <label>
          <span>Nombre</span>
          <input v-model.trim="form.name" class="retro-input" maxlength="100" required />
        </label>

        <label>
          <span>Raza del jugador</span>
          <select v-model="form.player_race" class="retro-input">
            <option v-for="race in races" :key="race.id" :value="race.id">{{ race.name }}</option>
          </select>
        </label>

        <div class="form-row">
          <label>
            <span>Galaxia</span>
            <select v-model="form.galaxy_size" class="retro-input">
              <option v-for="size in scenarioSizes" :key="size" :value="size">{{ size }}</option>
            </select>
          </label>

          <label>
            <span>Dificultad</span>
            <select v-model="form.difficulty" class="retro-input">
              <option v-for="difficulty in scenarioDifficulties" :key="difficulty" :value="difficulty">
                {{ difficulty }}
              </option>
            </select>
          </label>
        </div>

        <label>
          <span>Numero de oponentes</span>
          <input v-model.number="form.num_opponents" class="retro-input" min="1" :max="scenarioMaxOpponents" type="number" />
        </label>

        <button class="retro-btn" type="submit" :disabled="creating">
          {{ creating ? 'Creando...' : 'Crear partida' }}
        </button>
      </form>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../services/api'
import type { GameSummary, Scenario } from '../types/game'

const router = useRouter()

const loadingGames = ref(false)
const creating = ref(false)
const error = ref('')
const games = ref<GameSummary[]>([])
const scenarios = ref<Scenario[]>([])

const races = [
  { id: 'alkari', name: 'Alkari' },
  { id: 'meklar', name: 'Meklar' },
  { id: 'trilarian', name: 'Trilarian' },
]

const form = ref({
  name: 'Partida nueva',
  player_race: 'alkari',
  galaxy_size: 'small',
  difficulty: 'normal',
  num_opponents: 1,
})

const activeScenario = computed<Scenario | null>(() => scenarios.value[0] || null)
const scenarioSizes = computed(() => activeScenario.value?.galaxy_sizes || ['small', 'medium', 'large'])
const scenarioDifficulties = computed(() => activeScenario.value?.difficulty_options || ['easy', 'normal', 'hard'])
const scenarioMaxOpponents = computed(() => activeScenario.value?.max_opponents || 3)

function raceLabel(raceId?: string) {
  return races.find((race) => race.id === raceId)?.name || raceId || '-'
}

function formatDate(value?: string) {
  if (!value) return '-'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString()
}

async function loadGames() {
  loadingGames.value = true
  error.value = ''
  try {
    const response = await api.listGames()
    games.value = Array.isArray(response?.games) ? response.games : []
  } catch (err) {
    error.value = (err as Error).message || 'No se pudieron cargar las partidas.'
    games.value = []
  } finally {
    loadingGames.value = false
  }
}

async function loadScenarios() {
  try {
    const response = await api.getScenarios()
    scenarios.value = Array.isArray(response?.scenarios) ? response.scenarios : []
    if (activeScenario.value) {
      form.value.galaxy_size = activeScenario.value.galaxy_sizes[0]
      form.value.difficulty = activeScenario.value.difficulty_options[1] || activeScenario.value.difficulty_options[0]
      form.value.num_opponents = Math.min(form.value.num_opponents, activeScenario.value.max_opponents)
    }
  } catch {
    scenarios.value = []
  }
}

async function createNewGame() {
  creating.value = true
  error.value = ''
  try {
    const response = await api.createGame(form.value.name, {
      scenario_id: activeScenario.value?.id || 'default',
      galaxy_size: form.value.galaxy_size,
      difficulty: form.value.difficulty,
      num_opponents: form.value.num_opponents,
      player_race: form.value.player_race,
    })
    router.push(`/game/${response.game_id}/galaxy`)
  } catch (err) {
    error.value = (err as Error).message || 'No se pudo crear la partida.'
  } finally {
    creating.value = false
  }
}

async function openGame(gameId: string) {
  try {
    await api.loadGame(gameId)
    router.push(`/game/${gameId}/galaxy`)
  } catch (err) {
    error.value = (err as Error).message || 'No se pudo cargar la partida.'
  }
}

async function removeGame(gameId: string) {
  if (!confirm('Seguro que quieres eliminar esta partida?')) {
    return
  }
  try {
    await api.deleteGame(gameId)
    await loadGames()
  } catch (err) {
    error.value = (err as Error).message || 'No se pudo eliminar la partida.'
  }
}

onMounted(async () => {
  await Promise.all([loadGames(), loadScenarios()])
})
</script>

<style scoped>
.dashboard-grid {
  display: grid;
  grid-template-columns: 1.6fr 1fr;
  gap: 1rem;
}

.dashboard-panel {
  padding: 1rem;
}

.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 1rem;
}

.subtitle {
  margin: 0.25rem 0 0;
  color: var(--text-muted);
}

.table-wrap {
  overflow-x: auto;
  border: 1px solid rgba(89, 170, 255, 0.22);
  border-radius: 10px;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th,
td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid rgba(89, 170, 255, 0.18);
}

th {
  color: var(--primary-strong);
  text-transform: uppercase;
  font-size: 0.75rem;
  letter-spacing: 0.08em;
}

.row-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.create-form {
  display: grid;
  gap: 0.85rem;
}

.create-form label {
  display: grid;
  gap: 0.35rem;
}

.create-form span {
  color: var(--text-muted);
  font-size: 0.84rem;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.85rem;
}

.empty {
  color: var(--text-muted);
}

.error {
  color: var(--danger);
  margin-bottom: 1rem;
}

@media (max-width: 980px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .panel-head {
    flex-direction: column;
  }

  .form-row {
    grid-template-columns: 1fr;
  }
}
</style>
