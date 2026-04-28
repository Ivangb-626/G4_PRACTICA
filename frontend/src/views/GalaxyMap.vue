<template>
  <section class="map-layout">
    <article class="map-panel retro-panel">
      <header class="panel-head">
        <div>
          <h3>Mapa galactico</h3>
          <p class="subtitle">
            Sistemas explorados: {{ exploredSystems.length }}/{{ systems.length }}
          </p>
        </div>
        <button class="retro-btn" type="button" @click="loadGalaxy" :disabled="loading">
          {{ loading ? 'Cargando...' : 'Actualizar' }}
        </button>
      </header>

      <p v-if="error" class="error">{{ error }}</p>

      <div class="map-frame" v-if="systems.length">
        <svg class="connection-layer" viewBox="0 0 100 100" preserveAspectRatio="none">
          <line
            v-for="connection in connections"
            :key="connection.id"
            :x1="connection.x1"
            :y1="connection.y1"
            :x2="connection.x2"
            :y2="connection.y2"
            stroke="rgba(103, 240, 255, 0.28)"
            stroke-width="0.25"
          />
        </svg>

        <button
          v-for="system in systems"
          :key="system.id"
          class="system-node"
          :class="[
            `star-${system.star_type || 'unknown'}`,
            {
              unexplored: !system.explored,
              selected: selectedSystem?.id === system.id,
              colony: system.has_player_colony,
              fleet: system.has_player_fleet,
            },
          ]"
          :style="{ left: `${system.position.x}%`, top: `${system.position.y}%` }"
          type="button"
          @click="selectedSystemId = system.id"
        >
          <span class="sr-only">{{ system.name }}</span>
          <span class="system-label">{{ system.name }}</span>
        </button>
      </div>
    </article>

    <aside class="side-panel retro-panel">
      <template v-if="selectedSystem">
        <header class="panel-head">
          <div>
            <h3>{{ selectedSystem.name }}</h3>
            <p class="subtitle">
              {{ selectedSystem.explored ? selectedSystem.star_type : 'Sin explorar' }}
            </p>
          </div>
          <button class="retro-btn" type="button" @click="openSystem(selectedSystem.id)">
            Abrir sistema
          </button>
        </header>

        <div class="detail-grid">
          <article class="detail-card">
            <span>Planetas</span>
            <strong>{{ selectedSystem.planets.length }}</strong>
          </article>
          <article class="detail-card">
            <span>Conexiones</span>
            <strong>{{ selectedSystem.connections.length }}</strong>
          </article>
          <article class="detail-card">
            <span>Colonia propia</span>
            <strong>{{ selectedSystem.has_player_colony ? 'Si' : 'No' }}</strong>
          </article>
          <article class="detail-card">
            <span>Flota propia</span>
            <strong>{{ selectedSystem.has_player_fleet ? 'Si' : 'No' }}</strong>
          </article>
        </div>

        <ul v-if="selectedSystem.explored && selectedSystem.planets.length" class="planet-list">
          <li v-for="planet in selectedSystem.planets" :key="planet.index">
            <strong>{{ planet.name }}</strong>
            <span>{{ planet.type }} · {{ planet.size }}</span>
            <span>{{ planet.colonized_by ? `Colonizado por ${planet.colonized_by}` : 'Libre' }}</span>
          </li>
        </ul>
        <p v-else class="empty">No hay informacion detallada disponible hasta explorar el sistema.</p>
      </template>

      <p v-else class="empty">Selecciona una estrella para ver sus detalles.</p>
    </aside>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../services/api'
import type { GalaxySystem } from '../types/game'

const route = useRoute()
const router = useRouter()
const gameId = String(route.params.id || '')

const systems = ref<GalaxySystem[]>([])
const selectedSystemId = ref('')
const loading = ref(false)
const error = ref('')

const exploredSystems = computed(() => systems.value.filter((system) => system.explored))
const selectedSystem = computed(() => systems.value.find((system) => system.id === selectedSystemId.value) || null)

const connections = computed(() => {
  const items: Array<{ id: string; x1: number; y1: number; x2: number; y2: number }> = []
  const seen = new Set<string>()
  const map = new Map(systems.value.map((system) => [system.id, system]))

  for (const system of systems.value) {
    for (const targetId of system.connections) {
      const target = map.get(targetId)
      if (!target) continue
      const id = [system.id, targetId].sort().join(':')
      if (seen.has(id)) continue
      seen.add(id)
      items.push({
        id,
        x1: system.position.x,
        y1: system.position.y,
        x2: target.position.x,
        y2: target.position.y,
      })
    }
  }

  return items
})

async function loadGalaxy() {
  loading.value = true
  error.value = ''
  try {
    const response = await api.getGalaxy(gameId)
    systems.value = Array.isArray(response?.star_systems) ? response.star_systems : []
    if (!selectedSystemId.value && systems.value.length) {
      selectedSystemId.value =
        systems.value.find((system) => system.has_player_colony || system.has_player_fleet)?.id ||
        systems.value[0].id
    }
  } catch (err) {
    systems.value = []
    error.value = (err as Error).message || 'No se pudo cargar el mapa galactico.'
  } finally {
    loading.value = false
  }
}

function openSystem(systemId: string) {
  router.push(`/game/${gameId}/system/${systemId}`)
}

onMounted(loadGalaxy)
</script>

<style scoped>
.map-layout {
  display: grid;
  grid-template-columns: minmax(0, 2fr) minmax(300px, 1fr);
  gap: 1rem;
}

.map-panel,
.side-panel {
  padding: 0.9rem;
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

.map-frame {
  position: relative;
  min-height: 720px;
  border-radius: 12px;
  border: 1px solid rgba(89, 170, 255, 0.22);
  background:
    radial-gradient(circle at 30% 20%, rgba(27, 83, 149, 0.25), transparent 20%),
    radial-gradient(circle at 80% 10%, rgba(0, 212, 255, 0.15), transparent 16%),
    linear-gradient(180deg, rgba(3, 9, 24, 0.96), rgba(4, 11, 29, 0.88));
  overflow: hidden;
}

.map-frame::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image:
    radial-gradient(circle, rgba(255, 255, 255, 0.9) 0 0.08rem, transparent 0.08rem),
    radial-gradient(circle, rgba(103, 240, 255, 0.8) 0 0.05rem, transparent 0.05rem);
  background-position: 0 0, 1.4rem 1.1rem;
  background-size: 2.2rem 2.2rem, 2.8rem 2.8rem;
  opacity: 0.25;
}

.connection-layer {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.system-node {
  position: absolute;
  transform: translate(-50%, -50%);
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 0;
  cursor: pointer;
  box-shadow: 0 0 0.9rem rgba(255, 255, 255, 0.35);
  z-index: 1;
}

.system-node.unexplored {
  background: #51637c;
  box-shadow: none;
}

.system-node.selected {
  outline: 2px solid #ffe082;
  outline-offset: 5px;
}

.system-node.colony {
  box-shadow: 0 0 1rem rgba(141, 246, 191, 0.8);
}

.system-node.fleet::after {
  content: '';
  position: absolute;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  right: -5px;
  top: -3px;
  background: var(--primary-strong);
  box-shadow: 0 0 0.5rem rgba(103, 240, 255, 0.9);
}

.system-label {
  position: absolute;
  left: 50%;
  top: 120%;
  transform: translateX(-50%);
  min-width: max-content;
  color: var(--text);
  font-size: 0.74rem;
  text-shadow: 0 0 0.35rem rgba(0, 0, 0, 0.8);
}

.star-red {
  background: #ff5d6c;
}

.star-orange {
  background: #ff9d3a;
}

.star-yellow {
  background: #ffd447;
}

.star-white {
  background: #d5ecff;
}

.star-blue {
  background: #4bb7ff;
}

.star-unknown {
  background: #6881a1;
}

.detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
  margin: 0.9rem 0 1rem;
}

.detail-card {
  padding: 0.75rem;
  border-radius: 10px;
  border: 1px solid rgba(89, 170, 255, 0.18);
  background: rgba(8, 15, 38, 0.72);
}

.detail-card span {
  display: block;
  margin-bottom: 0.35rem;
  color: var(--text-muted);
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.planet-list {
  display: grid;
  gap: 0.7rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.planet-list li {
  display: grid;
  gap: 0.2rem;
  padding: 0.7rem;
  border: 1px solid rgba(112, 166, 214, 0.18);
  border-radius: 8px;
  background: rgba(7, 15, 36, 0.72);
}

.empty {
  color: var(--text-muted);
}

.error {
  color: var(--danger);
  margin-bottom: 0.75rem;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  border: 0;
}

@media (max-width: 1080px) {
  .map-layout {
    grid-template-columns: 1fr;
  }

  .map-frame {
    min-height: 580px;
  }
}
</style>
