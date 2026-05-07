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
          <span>Estrella (capital)</span>
          <input v-model.trim="form.home_system_name" class="retro-input" maxlength="20" required />
        </label>

        <label>
          <span>Raza del jugador</span>
          <select v-model="form.player_race" class="retro-input">
            <option v-for="race in races" :key="race.id" :value="race.id">{{ race.name }}</option>
          </select>
        </label>

        <div class="form-row">
          <label>
            <span>Tamano galaxia</span>
            <select v-model="form.galaxy_size" class="retro-input">
              <option v-for="size in scenarioSizes" :key="size" :value="size">{{ size }}</option>
            </select>
          </label>

          <label>
            <span>Edad galaxia</span>
            <select v-model="form.galaxy_age" class="retro-input">
              <option value="early">Temprana</option>
              <option value="average">Media</option>
              <option value="late">Tardia</option>
            </select>
          </label>
        </div>

        <div class="form-row">
          <label>
            <span>Dificultad</span>
            <select v-model="form.difficulty" class="retro-input">
              <option v-for="difficulty in scenarioDifficulties" :key="difficulty" :value="difficulty">
                {{ difficulty }}
              </option>
            </select>
          </label>

          <label>
            <span>Tecnologia inicial</span>
            <select v-model="form.starting_tech_level" class="retro-input">
              <option value="pre_warp">Pre-Warp</option>
              <option value="average">Media</option>
              <option value="advanced">Avanzada</option>
            </select>
          </label>
        </div>

        <label>
          <span>Numero de oponentes</span>
          <input v-model.number="form.num_opponents" class="retro-input" min="1" :max="scenarioMaxOpponents" type="number" />
        </label>

        <div class="form-row">
          <label class="checkbox-row">
            <input type="checkbox" v-model="form.antaran_attacks_enabled" />
            <span>Ataques Antaranos</span>
          </label>
          <label class="checkbox-row">
            <input type="checkbox" v-model="form.orion_guardian_enabled" />
            <span>Guardian de Orion</span>
          </label>
        </div>
        <label class="checkbox-row">
          <input type="checkbox" v-model="form.random_events_enabled" />
          <span>Eventos aleatorios</span>
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
import { useGameStore } from '../store/gameStore'
import type { GameSummary, Scenario } from '../types/game'

const gameStore = useGameStore()

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
  home_system_name: 'Sol',
  player_race: 'alkari',
  galaxy_size: 'medium',
  galaxy_age: 'average',
  difficulty: 'officer',
  starting_tech_level: 'average',
  num_opponents: 3,
  antaran_attacks_enabled: true,
  orion_guardian_enabled: true,
  random_events_enabled: true,
})

const activeScenario = computed<Scenario | null>(() => scenarios.value[0] || null)
const scenarioSizes = computed(() => activeScenario.value?.galaxy_sizes || ['small', 'medium', 'large', 'huge'])
const scenarioDifficulties = computed(() => activeScenario.value?.difficulty_options || ['gardener', 'officer', 'commander', 'lord', 'impossible'])
const scenarioMaxOpponents = computed(() => activeScenario.value?.max_opponents || 7)

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
    games.value = Array.isArray(response) ? response : (response?.games ?? [])
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
    scenarios.value = Array.isArray(response) ? response : (response?.scenarios ?? [])
    if (activeScenario.value) {
      const sizes = activeScenario.value.galaxy_sizes || ['small', 'medium', 'large', 'huge']
      if (!sizes.includes(form.value.galaxy_size)) form.value.galaxy_size = sizes[1] || sizes[0]
      const diffs = activeScenario.value.difficulty_options || ['officer']
      if (!diffs.includes(form.value.difficulty)) form.value.difficulty = diffs[1] || diffs[0]
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
    const response = await gameStore.createGame({
      name: form.value.name,
      scenario_id: activeScenario.value?.id || 'default',
      galaxy_size: form.value.galaxy_size,
      galaxy_age: form.value.galaxy_age,
      difficulty: form.value.difficulty,
      starting_tech_level: form.value.starting_tech_level,
      num_opponents: form.value.num_opponents,
      player_race: form.value.player_race,
      home_system_name: form.value.home_system_name,
      antaran_attacks_enabled: form.value.antaran_attacks_enabled,
      orion_guardian_enabled: form.value.orion_guardian_enabled,
      random_events_enabled: form.value.random_events_enabled,
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
    await gameStore.loadGame(gameId)
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

.checkbox-row {
  display: flex !important;
  align-items: center;
  gap: 0.5rem;
}
.checkbox-row input { width: auto; }

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
