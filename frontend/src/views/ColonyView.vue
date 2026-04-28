<template>
  <section v-if="colony" class="colony-layout">
    <article class="retro-panel colony-panel">
      <header class="panel-head">
        <div>
          <h3>{{ colony.name }}</h3>
          <p class="subtitle">
            Sistema {{ colony.star_system_id }} · Poblacion {{ colony.population.total }}/{{ colony.population.max }}
          </p>
        </div>
        <button class="retro-btn" type="button" @click="backToSystem">Volver al sistema</button>
      </header>

      <section class="stat-grid">
        <article class="stat-card">
          <span>Comida</span>
          <strong>{{ colony.food_output }}</strong>
          <small>Superavit {{ colony.food_surplus }}</small>
        </article>
        <article class="stat-card">
          <span>Industria</span>
          <strong>{{ colony.industry_output }}</strong>
          <small>Construccion por turno</small>
        </article>
        <article class="stat-card">
          <span>Investigacion</span>
          <strong>{{ colony.research_output }}</strong>
          <small>Laboratorios activos</small>
        </article>
        <article class="stat-card">
          <span>BC</span>
          <strong>{{ colony.bc_output }}</strong>
          <small>Ingresos locales</small>
        </article>
      </section>

      <div class="panel-split">
        <section class="inner-panel">
          <header class="inner-head">
            <h4>Poblacion</h4>
            <button class="retro-btn" type="button" @click="savePopulation" :disabled="savingPopulation">
              {{ savingPopulation ? 'Aplicando...' : 'Aplicar cambios' }}
            </button>
          </header>

          <div class="slider-group">
            <label>Farmers: {{ population.farmers }}</label>
            <input v-model.number="population.farmers" type="range" min="0" :max="colony.population.total" @input="rebalance('farmers')" />
          </div>
          <div class="slider-group">
            <label>Workers: {{ population.workers }}</label>
            <input v-model.number="population.workers" type="range" min="0" :max="colony.population.total" @input="rebalance('workers')" />
          </div>
          <div class="slider-group">
            <label>Scientists: {{ population.scientists }}</label>
            <input
              v-model.number="population.scientists"
              type="range"
              min="0"
              :max="colony.population.total"
              @input="rebalance('scientists')"
            />
          </div>

          <ul v-if="warnings.length" class="warning-list">
            <li v-for="warning in warnings" :key="warning">{{ warning }}</li>
          </ul>
        </section>

        <section class="inner-panel">
          <header class="inner-head">
            <h4>Edificios construidos</h4>
          </header>
          <ul v-if="colony.buildings.length" class="simple-list">
            <li v-for="building in colony.buildings" :key="building.id">{{ building.name }}</li>
          </ul>
          <p v-else class="empty">Todavia no hay edificios completados.</p>
        </section>
      </div>
    </article>

    <article class="retro-panel queue-panel">
      <header class="panel-head">
        <div>
          <h3>Cola de construccion</h3>
          <p class="subtitle">Gestion de edificios y naves de la colonia.</p>
        </div>
      </header>

      <ul v-if="colony.build_queue.length" class="queue-list">
        <li v-for="(item, index) in colony.build_queue" :key="`${item.type}-${item.id}-${index}`">
          <div>
            <strong>{{ queueItemLabel(item.type, item.id) }}</strong>
            <p>{{ item.progress }}/{{ item.cost }}</p>
          </div>
          <div class="queue-actions">
            <button class="retro-btn" type="button" @click="moveQueueItem(index, index - 1)" :disabled="index === 0">
              Subir
            </button>
            <button
              class="retro-btn"
              type="button"
              @click="moveQueueItem(index, index + 1)"
              :disabled="index === colony.build_queue.length - 1"
            >
              Bajar
            </button>
            <button class="retro-btn retro-btn-danger" type="button" @click="removeQueueItem(index)">Quitar</button>
          </div>
        </li>
      </ul>
      <p v-else class="empty">La cola esta vacia.</p>

      <div class="build-grid">
        <section class="inner-panel">
          <header class="inner-head">
            <h4>Edificios disponibles</h4>
          </header>
          <ul v-if="availableBuildings.length" class="build-list">
            <li v-for="building in availableBuildings" :key="building.id">
              <div>
                <strong>{{ building.name }}</strong>
                <p>{{ building.description || 'Sin descripcion' }}</p>
              </div>
              <button class="retro-btn" type="button" @click="addQueueItem('building', building.id)">
                {{ building.cost }} BC
              </button>
            </li>
          </ul>
          <p v-else class="empty">No hay edificios disponibles con la tecnologia actual.</p>
        </section>

        <section class="inner-panel">
          <header class="inner-head">
            <h4>Naves disponibles</h4>
          </header>
          <ul v-if="availableShips.length" class="build-list">
            <li v-for="ship in availableShips" :key="ship.type">
              <div>
                <strong>{{ ship.name }}</strong>
                <p>{{ ship.description }}</p>
              </div>
              <button class="retro-btn" type="button" @click="addQueueItem('ship', ship.type)">
                {{ ship.cost }} BC
              </button>
            </li>
          </ul>
          <p v-else class="empty">No hay naves disponibles para esta colonia.</p>
        </section>
      </div>

      <p v-if="error" class="error">{{ error }}</p>
    </article>
  </section>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../services/api'
import type { BuildQueueItem, Colony } from '../types/game'

type AvailableBuilding = {
  id: string
  name: string
  cost: number
  description: string
}

type AvailableShip = {
  type: string
  name: string
  cost: number
  description: string
}

const route = useRoute()
const router = useRouter()
const gameId = String(route.params.id || '')
const colonyId = String(route.params.colId || '')

const colony = ref<Colony | null>(null)
const availableBuildings = ref<AvailableBuilding[]>([])
const availableShips = ref<AvailableShip[]>([])
const warnings = ref<string[]>([])
const savingPopulation = ref(false)
const error = ref('')

const population = reactive({
  farmers: 0,
  workers: 0,
  scientists: 0,
})

function syncPopulation() {
  if (!colony.value) return
  population.farmers = colony.value.population.farmers
  population.workers = colony.value.population.workers
  population.scientists = colony.value.population.scientists
}

function queueItemLabel(type: BuildQueueItem['type'], id: string) {
  if (type === 'building') {
    return availableBuildings.value.find((item) => item.id === id)?.name ||
      colony.value?.buildings.find((item) => item.id === id)?.name ||
      id
  }
  return availableShips.value.find((item) => item.type === id)?.name || id
}

function rebalance(changed: 'farmers' | 'workers' | 'scientists') {
  if (!colony.value) return
  const total = colony.value.population.total
  const keys: Array<'farmers' | 'workers' | 'scientists'> = ['farmers', 'workers', 'scientists']
  let sum = population.farmers + population.workers + population.scientists

  if (sum <= total) {
    return
  }

  for (const key of keys) {
    if (key === changed || sum <= total) continue
    const reducible = Math.min(population[key], sum - total)
    population[key] -= reducible
    sum -= reducible
  }
}

async function loadColony() {
  error.value = ''
  try {
    const response = await api.getColony(gameId, colonyId)
    colony.value = response?.colony || null
    availableBuildings.value = Array.isArray(response?.available_buildings) ? response.available_buildings : []
    availableShips.value = Array.isArray(response?.available_ships) ? response.available_ships : []
    warnings.value = []
    syncPopulation()
  } catch (err) {
    error.value = (err as Error).message || 'No se pudo cargar la colonia.'
  }
}

async function savePopulation() {
  if (!colony.value) return
  savingPopulation.value = true
  error.value = ''
  try {
    const response = await api.manageColony(gameId, colonyId, {
      population: {
        farmers: population.farmers,
        workers: population.workers,
        scientists: population.scientists,
      },
    })
    colony.value = response?.colony || colony.value
    warnings.value = Array.isArray(response?.validation_warnings) ? response.validation_warnings : []
    syncPopulation()
  } catch (err) {
    error.value = (err as Error).message || 'No se pudieron aplicar los cambios.'
  } finally {
    savingPopulation.value = false
  }
}

async function addQueueItem(type: 'building' | 'ship', id: string) {
  error.value = ''
  try {
    await api.addBuildQueueItem(gameId, colonyId, type, id)
    await loadColony()
  } catch (err) {
    error.value = (err as Error).message || 'No se pudo anadir a la cola.'
  }
}

async function removeQueueItem(index: number) {
  error.value = ''
  try {
    await api.removeBuildQueueItem(gameId, colonyId, index)
    await loadColony()
  } catch (err) {
    error.value = (err as Error).message || 'No se pudo quitar el elemento.'
  }
}

async function moveQueueItem(from: number, to: number) {
  error.value = ''
  try {
    await api.reorderBuildQueue(gameId, colonyId, from, to)
    await loadColony()
  } catch (err) {
    error.value = (err as Error).message || 'No se pudo reordenar la cola.'
  }
}

function backToSystem() {
  if (!colony.value) {
    router.push(`/game/${gameId}/galaxy`)
    return
  }
  router.push(`/game/${gameId}/system/${colony.value.star_system_id}`)
}

onMounted(loadColony)
</script>

<style scoped>
.colony-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(360px, 1fr);
  gap: 1rem;
}

.colony-panel,
.queue-panel {
  padding: 0.95rem;
}

.panel-head,
.inner-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 0.9rem;
}

.subtitle {
  margin: 0.25rem 0 0;
  color: var(--text-muted);
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.stat-card,
.inner-panel {
  padding: 0.8rem;
  border: 1px solid rgba(89, 170, 255, 0.18);
  border-radius: 10px;
  background: rgba(7, 15, 36, 0.74);
}

.stat-card span {
  display: block;
  margin-bottom: 0.35rem;
  color: var(--text-muted);
  text-transform: uppercase;
  font-size: 0.75rem;
  letter-spacing: 0.08em;
}

.stat-card small {
  display: block;
  margin-top: 0.3rem;
  color: var(--text-muted);
}

.panel-split,
.build-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.9rem;
}

.slider-group {
  display: grid;
  gap: 0.35rem;
  margin-bottom: 0.85rem;
}

.slider-group input {
  width: 100%;
}

.simple-list,
.warning-list,
.queue-list,
.build-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.warning-list {
  display: grid;
  gap: 0.45rem;
  color: #ffd27d;
}

.queue-list {
  display: grid;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.queue-list li,
.build-list li {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.8rem;
  border: 1px solid rgba(112, 166, 214, 0.18);
  border-radius: 8px;
  background: rgba(7, 15, 36, 0.72);
}

.queue-list p,
.build-list p {
  margin: 0.2rem 0 0;
  color: var(--text-muted);
  font-size: 0.84rem;
}

.queue-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
  align-items: center;
  justify-content: flex-end;
}

.empty {
  color: var(--text-muted);
}

.error {
  margin-top: 1rem;
  color: var(--danger);
}

@media (max-width: 1180px) {
  .colony-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 860px) {
  .stat-grid,
  .panel-split,
  .build-grid {
    grid-template-columns: 1fr;
  }

  .queue-list li,
  .build-list li {
    flex-direction: column;
  }
}
</style>
