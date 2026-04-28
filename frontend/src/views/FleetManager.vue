<template>
  <section class="retro-panel fleet-panel">
    <header class="panel-head">
      <div>
        <h3>Gestor de flotas</h3>
        <p class="subtitle">Movimiento tactico y estado actual de las naves del jugador.</p>
      </div>
      <button class="retro-btn" type="button" @click="loadData" :disabled="loading">
        {{ loading ? 'Cargando...' : 'Actualizar' }}
      </button>
    </header>

    <p v-if="error" class="error">{{ error }}</p>

    <div v-if="fleets.length" class="fleet-grid">
      <article v-for="fleet in fleets" :key="fleet.id" class="fleet-card">
        <div class="fleet-header">
          <div>
            <h4>{{ fleet.name }}</h4>
            <p>{{ systemName(fleet.star_system_id) }}</p>
          </div>
          <span class="status-pill" :class="{ transit: fleet.in_transit }">
            {{ fleet.in_transit ? `ETA ${fleet.eta_turns}` : 'Lista' }}
          </span>
        </div>

        <p class="ship-summary">{{ fleet.ships.map((ship) => `${ship.count}x ${ship.type}`).join(', ') }}</p>
        <p class="destination-line">Destino: {{ fleet.destination ? systemName(fleet.destination) : 'Sin ordenes' }}</p>

        <div class="fleet-actions">
          <select v-model="destinations[fleet.id]" class="retro-input" :disabled="fleet.in_transit || !reachableDestinations(fleet).length">
            <option value="">Selecciona destino</option>
            <option v-for="destination in reachableDestinations(fleet)" :key="destination.id" :value="destination.id">
              {{ destination.name }}
            </option>
          </select>

          <button
            class="retro-btn"
            type="button"
            @click="moveSelectedFleet(fleet.id)"
            :disabled="fleet.in_transit || !destinations[fleet.id]"
          >
            Mover
          </button>
        </div>
      </article>
    </div>

    <p v-else-if="!loading" class="empty">No hay flotas disponibles.</p>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../services/api'
import type { FleetSummary, GalaxySystem } from '../types/game'

const route = useRoute()
const gameId = String(route.params.id || '')

const fleets = ref<FleetSummary[]>([])
const systems = ref<GalaxySystem[]>([])
const destinations = ref<Record<string, string>>({})
const loading = ref(false)
const error = ref('')

function systemName(systemId: string | null) {
  if (!systemId) return '-'
  return systems.value.find((system) => system.id === systemId)?.name || systemId
}

function reachableDestinations(fleet: FleetSummary) {
  const current = systems.value.find((system) => system.id === fleet.star_system_id)
  if (!current) return []
  return current.connections
    .map((connection) => systems.value.find((system) => system.id === connection))
    .filter((system): system is GalaxySystem => Boolean(system))
}

async function loadData() {
  loading.value = true
  error.value = ''
  try {
    const [fleetResponse, galaxyResponse] = await Promise.all([
      api.getFleets(gameId),
      api.getGalaxy(gameId),
    ])
    fleets.value = Array.isArray(fleetResponse?.fleets) ? fleetResponse.fleets : []
    systems.value = Array.isArray(galaxyResponse?.star_systems) ? galaxyResponse.star_systems : []
    const nextDestinations: Record<string, string> = {}
    for (const fleet of fleets.value) {
      nextDestinations[fleet.id] = destinations.value[fleet.id] || ''
    }
    destinations.value = nextDestinations
  } catch (err) {
    fleets.value = []
    error.value = (err as Error).message || 'No se pudieron cargar las flotas.'
  } finally {
    loading.value = false
  }
}

async function moveSelectedFleet(fleetId: string) {
  const destination = destinations.value[fleetId]
  if (!destination) return
  error.value = ''
  try {
    await api.moveFleet(gameId, fleetId, destination)
    destinations.value[fleetId] = ''
    await loadData()
  } catch (err) {
    error.value = (err as Error).message || 'No se pudo mover la flota.'
  }
}

onMounted(loadData)
</script>

<style scoped>
.fleet-panel {
  padding: 1rem;
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

.fleet-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.85rem;
}

.fleet-card {
  padding: 0.9rem;
  border-radius: 10px;
  border: 1px solid rgba(89, 170, 255, 0.18);
  background: rgba(7, 15, 36, 0.74);
}

.fleet-header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
}

.fleet-header h4 {
  margin: 0;
}

.fleet-header p,
.ship-summary,
.destination-line {
  margin: 0.25rem 0 0;
  color: var(--text-muted);
}

.status-pill {
  height: fit-content;
  padding: 0.25rem 0.55rem;
  border-radius: 999px;
  background: rgba(141, 246, 191, 0.18);
  border: 1px solid rgba(141, 246, 191, 0.3);
  font-size: 0.76rem;
}

.status-pill.transit {
  background: rgba(255, 212, 71, 0.15);
  border-color: rgba(255, 212, 71, 0.28);
}

.fleet-actions {
  display: flex;
  gap: 0.65rem;
  margin-top: 0.9rem;
}

.fleet-actions select {
  flex: 1;
}

.empty {
  color: var(--text-muted);
}

.error {
  color: var(--danger);
  margin-bottom: 0.8rem;
}

@media (max-width: 900px) {
  .fleet-grid {
    grid-template-columns: 1fr;
  }

  .fleet-actions {
    flex-direction: column;
  }
}
</style>
