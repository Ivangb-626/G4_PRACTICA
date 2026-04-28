<template>
  <section class="system-layout" v-if="system">
    <article class="retro-panel system-panel">
      <header class="panel-head">
        <div>
          <h3>{{ system.name }}</h3>
          <p class="subtitle">{{ system.star_type }} · {{ system.planets.length }} planetas</p>
        </div>
        <button class="retro-btn" type="button" @click="backToGalaxy">Volver al mapa</button>
      </header>

      <div class="planet-grid">
        <article v-for="planet in system.planets" :key="planet.index" class="planet-card">
          <header class="planet-head">
            <div>
              <h4>{{ planet.name }}</h4>
              <p>{{ planet.type }} · {{ planet.size }} · {{ planet.gravity }}</p>
            </div>
            <span class="status-pill" :class="{ owned: planet.colonized_by === 'player' }">
              {{ planet.colonized_by || 'Libre' }}
            </span>
          </header>

          <p class="planet-meta">Minerales: {{ planet.minerals }} · Max pop: {{ planet.max_population }}</p>

          <div class="planet-actions">
            <button
              v-if="planet.colonized_by === 'player'"
              class="retro-btn"
              type="button"
              @click="openColony(planet.index)"
            >
              Gestionar colonia
            </button>
            <button
              v-else-if="colonizerFleetId"
              class="retro-btn"
              type="button"
              @click="colonizePlanet(planet.index)"
              :disabled="colonizingPlanetIndex === planet.index"
            >
              {{ colonizingPlanetIndex === planet.index ? 'Colonizando...' : 'Colonizar' }}
            </button>
          </div>
        </article>
      </div>
    </article>

    <aside class="retro-panel side-panel">
      <header class="panel-head">
        <div>
          <h3>Flotas en orbita</h3>
          <p class="subtitle">Resumen tactico del sistema.</p>
        </div>
      </header>

      <ul v-if="localFleets.length" class="fleet-list">
        <li v-for="fleet in localFleets" :key="fleet.id">
          <strong>{{ fleet.name }}</strong>
          <span>{{ fleet.ships.map((ship) => `${ship.count}x ${ship.type}`).join(', ') }}</span>
          <span v-if="fleet.destination">En transito a {{ fleet.destination }} (ETA {{ fleet.eta_turns }})</span>
        </li>
      </ul>
      <p v-else class="empty">No tienes flotas estacionadas aqui.</p>

      <p v-if="error" class="error">{{ error }}</p>
    </aside>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../services/api'
import type { Fleet, GameState, GalaxySystem } from '../types/game'

const route = useRoute()
const router = useRouter()
const gameId = String(route.params.id || '')
const systemId = String(route.params.sysId || '')

const gameState = ref<GameState | null>(null)
const system = ref<GalaxySystem | null>(null)
const error = ref('')
const colonizingPlanetIndex = ref<number | null>(null)

const localFleets = computed<Fleet[]>(() => {
  const fleets = gameState.value?.player.fleets || []
  return fleets.filter((fleet) => fleet.star_system_id === systemId)
})

const colonizerFleetId = computed(() => {
  const fleet = localFleets.value.find(
    (item) =>
      item.destination === null &&
      item.ships.some((ship) => ship.type === 'colony_ship' && ship.count > 0),
  )
  return fleet?.id || ''
})

async function loadSystem() {
  error.value = ''
  try {
    const [galaxyResponse, gameResponse] = await Promise.all([
      api.getGalaxy(gameId),
      api.loadGame(gameId),
    ])
    const systems = Array.isArray(galaxyResponse?.star_systems) ? galaxyResponse.star_systems : []
    system.value = systems.find((item: GalaxySystem) => item.id === systemId) || null
    gameState.value = gameResponse?.game_state || null
  } catch (err) {
    error.value = (err as Error).message || 'No se pudo cargar el sistema.'
  }
}

function backToGalaxy() {
  router.push(`/game/${gameId}/galaxy`)
}

function openColony(planetIndex: number) {
  router.push(`/game/${gameId}/colony/col_${systemId}_${planetIndex}`)
}

async function colonizePlanet(planetIndex: number) {
  if (!colonizerFleetId.value) return
  colonizingPlanetIndex.value = planetIndex
  error.value = ''
  try {
    await api.colonize(gameId, colonizerFleetId.value, planetIndex)
    await loadSystem()
  } catch (err) {
    error.value = (err as Error).message || 'No se pudo colonizar el planeta.'
  } finally {
    colonizingPlanetIndex.value = null
  }
}

onMounted(loadSystem)
</script>

<style scoped>
.system-layout {
  display: grid;
  grid-template-columns: minmax(0, 2fr) minmax(300px, 1fr);
  gap: 1rem;
}

.system-panel,
.side-panel {
  padding: 0.95rem;
}

.panel-head {
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

.planet-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.85rem;
}

.planet-card {
  padding: 0.85rem;
  border: 1px solid rgba(89, 170, 255, 0.18);
  border-radius: 10px;
  background: rgba(7, 15, 36, 0.74);
}

.planet-head {
  display: flex;
  justify-content: space-between;
  gap: 0.8rem;
}

.planet-head h4 {
  margin: 0;
}

.planet-head p,
.planet-meta {
  margin: 0.2rem 0 0;
  color: var(--text-muted);
  font-size: 0.84rem;
}

.status-pill {
  height: fit-content;
  padding: 0.25rem 0.55rem;
  border-radius: 999px;
  background: rgba(81, 99, 124, 0.45);
  color: var(--text);
  font-size: 0.76rem;
  white-space: nowrap;
}

.status-pill.owned {
  background: rgba(141, 246, 191, 0.18);
  border: 1px solid rgba(141, 246, 191, 0.32);
}

.planet-actions {
  margin-top: 0.75rem;
}

.fleet-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 0.7rem;
}

.fleet-list li {
  display: grid;
  gap: 0.2rem;
  padding: 0.75rem;
  border: 1px solid rgba(89, 170, 255, 0.18);
  border-radius: 8px;
  background: rgba(7, 15, 36, 0.72);
}

.empty {
  color: var(--text-muted);
}

.error {
  color: var(--danger);
  margin-top: 0.9rem;
}

@media (max-width: 1024px) {
  .system-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .planet-grid {
    grid-template-columns: 1fr;
  }
}
</style>
