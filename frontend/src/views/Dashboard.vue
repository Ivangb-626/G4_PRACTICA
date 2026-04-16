<template>
  <section class="dashboard">
    <header class="topbar">
      <div>
        <h2>Dashboard</h2>
        <p class="subtitle">Gestiona tus partidas guardadas y crea una nueva campaña.</p>
      </div>
      <div class="actions">
        <button class="btn" @click="loadGames" :disabled="loading">{{ loading ? 'Cargando...' : 'Refrescar' }}</button>
        <button class="btn primary" @click="newGame" :disabled="creating">{{ creating ? 'Creando...' : 'Nueva Partida' }}</button>
      </div>
    </header>

    <p v-if="error" class="error">{{ error }}</p>

    <div v-if="games.length" class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Nombre</th>
            <th>Turno</th>
            <th>Raza</th>
            <th>Tamaño galaxia</th>
            <th>Último guardado</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="g in games" :key="g.game_id">
            <td>{{ g.name }}</td>
            <td>{{ g.turn }}</td>
            <td>{{ prettyRace(g.player_race) }}</td>
            <td>{{ g.galaxy_size || '—' }}</td>
            <td>{{ formatDate(g.last_saved) }}</td>
            <td class="row-actions">
              <button class="btn" @click="loadGame(g.game_id)">Cargar</button>
              <button class="btn danger" @click="deleteGame(g.game_id)">Eliminar</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <p v-else class="empty">No hay partidas guardadas aún.</p>
  </section>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../services/api'

type GameSummary = {
  game_id: string
  name: string
  turn: number
  player_race?: string
  galaxy_size?: string
  last_saved?: string
}

const games = ref<GameSummary[]>([])
const router = useRouter()
const loading = ref(false)
const creating = ref(false)
const error = ref('')

const raceLabels: Record<string, string> = {
  humans: 'Humanos',
  sakkra: 'Sakkra',
  mrrshan: 'Mrrshan',
  darlok: 'Darlok',
  alkari: 'Alkari',
  bulrathi: 'Bulrathi',
  psilon: 'Psilon',
  silicoid: 'Silicoid',
  meklar: 'Meklar',
  klackon: 'Klackon'
}

async function loadGames() {
  loading.value = true
  error.value = ''
  try {
    const response = await api.listGames()
    games.value = Array.isArray(response?.games) ? response.games : []
  } catch (err) {
    console.error(err)
    games.value = []
    const e = err as Error
    error.value = e.message || 'No se pudieron cargar las partidas.'
  } finally {
    loading.value = false
  }
}

async function newGame() {
  const name = prompt('Nombre de la nueva partida:', 'Partida 1')
  if (!name) return
  const scenario = { galaxy_size: 'small', num_opponents: 1, difficulty: 'normal', player_race: 'humans' }
  creating.value = true
  error.value = ''
  try {
    const response = await api.createGame(name, scenario)
    const gameId = response?.game_id
    if (!gameId) {
      throw new Error('La API no devolvió game_id al crear la partida.')
    }
    router.push(`/game/${gameId}/galaxy`)
  } catch (err) {
    console.error(err)
    const e = err as Error
    error.value = e.message || 'No se pudo crear la partida.'
  } finally {
    creating.value = false
  }
}

async function loadGame(id: string) {
  error.value = ''
  try {
    await api.loadGame(id)
    router.push(`/game/${id}/galaxy`)
  } catch (err) {
    console.error(err)
    const e = err as Error
    error.value = e.message || 'No se pudo cargar la partida.'
  }
}

async function deleteGame(id: string) {
  if (!confirm('¿Seguro que quieres eliminar esta partida?')) return
  error.value = ''
  try {
    await api.deleteGame(id)
    await loadGames()
  } catch (err) {
    console.error(err)
    const e = err as Error
    error.value = e.message || 'No se pudo eliminar la partida.'
  }
}

function prettyRace(raceId?: string) {
  if (!raceId) return '—'
  return raceLabels[raceId] || raceId
}

function formatDate(value?: string) {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString()
}

onMounted(loadGames)
</script>

<style scoped>
.dashboard {
  color: var(--text);
  border: 1px solid var(--panel-border);
  background: var(--panel);
  border-radius: 10px;
  box-shadow: var(--shadow-neon);
  padding: 0.9rem;
}
.topbar {
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
.actions {
  display: flex;
  gap: 0.5rem;
}
.table-wrap {
  border: 1px solid var(--panel-border);
  border-radius: 8px;
  overflow: hidden;
  background: rgba(6, 13, 34, 0.5);
}
table {
  width: 100%;
  border-collapse: collapse;
}
th, td {
  padding: 0.7rem;
  text-align: left;
  border-bottom: 1px solid rgba(89, 170, 255, 0.24);
}
th {
  color: var(--primary-strong);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-size: 0.74rem;
}
.row-actions {
  display: flex;
  gap: 0.5rem;
}
.btn {
  border: 1px solid var(--primary);
  background: linear-gradient(180deg, rgba(79, 180, 255, 0.2), rgba(79, 180, 255, 0.05));
  color: var(--text);
  padding: 0.4rem 0.7rem;
  border-radius: 6px;
  cursor: pointer;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-size: 0.72rem;
}
.btn:hover {
  border-color: var(--primary-strong);
  box-shadow: 0 0 0.65rem rgba(103, 240, 255, 0.45);
}
.btn:disabled {
  opacity: 0.6;
  cursor: default;
}
.btn.primary {
  background: linear-gradient(180deg, rgba(79, 180, 255, 0.4), rgba(79, 180, 255, 0.18));
}
.btn.primary:hover {
  background: linear-gradient(180deg, rgba(103, 240, 255, 0.45), rgba(79, 180, 255, 0.22));
}
.btn.danger {
  border-color: var(--danger);
  color: #ffdbe3;
}
.btn.danger:hover {
  background: rgba(255, 107, 138, 0.14);
  box-shadow: 0 0 0.65rem rgba(255, 107, 138, 0.4);
}
.empty {
  color: var(--text-muted);
}
.error {
  color: var(--danger);
}
</style>
