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
        <button
          v-for="system in systems"
          :key="system.id"
          class="system-node"
          :class="[
            `star-${system.star_type}`,
            {
              colony: system.has_player_colony,
              fleet: system.has_player_fleet,
            },
          ]"
          :style="{ left: `calc(5% + ${system.position.x * 0.9}%)`, top: `calc(5% + ${system.position.y * 0.9}%)` }"
          type="button"
          @click="openSystem(system.id)"
        >
          <span class="sr-only">{{ system.name }}</span>
          <span class="system-label">{{ system.name }}</span>
        </button>
      </div>
    </article>
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
const loading = ref(false)
const error = ref('')

const exploredSystems = computed(() => systems.value.filter((system) => system.explored))

async function loadGalaxy() {
  loading.value = true
  error.value = ''
  try {
    const response = await api.getGalaxy(gameId)
    systems.value = Array.isArray(response?.star_systems) ? response.star_systems : []
    // Ensure all have a type even if unexplored
    systems.value.forEach(sys => {
      if (!sys.star_type || sys.star_type === 'unknown') {
        const types = ['red', 'orange', 'yellow', 'white', 'blue']
        sys.star_type = types[sys.id.length % types.length] // pseudo-random stable
      }
    })
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
  display: block;
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
  width: 16px;
  height: 16px;
  border-radius: 0;
  border: 0;
  cursor: pointer;
  background: transparent;
  z-index: 1;
}

.system-node::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 2px;
  height: 2px;
  background: var(--star-core, #ffffff);
  animation: glow-pulse 3s infinite alternate;
  box-shadow:
    /* Inner Cross */
    -2px 0 0 var(--star-core),
    2px 0 0 var(--star-core),
    0 -2px 0 var(--star-core),
    0 2px 0 var(--star-core),
    /* Main Color Cross */
    -4px 0 0 var(--star-color),
    4px 0 0 var(--star-color),
    0 -4px 0 var(--star-color),
    0 4px 0 var(--star-color),
    -2px -2px 0 var(--star-color),
    -2px 2px 0 var(--star-color),
    2px -2px 0 var(--star-color),
    2px 2px 0 var(--star-color),
    /* Outer Dim Cross */
    -6px 0 0 var(--star-dim),
    6px 0 0 var(--star-dim),
    0 -6px 0 var(--star-dim),
    0 6px 0 var(--star-dim),
    -4px -2px 0 var(--star-dim),
    -4px 2px 0 var(--star-dim),
    4px -2px 0 var(--star-dim),
    4px 2px 0 var(--star-dim),
    -2px -4px 0 var(--star-dim),
    2px -4px 0 var(--star-dim),
    -2px 4px 0 var(--star-dim),
    2px 4px 0 var(--star-dim),
    /* Deep Glow Effect */
    0 0 10px 2px var(--star-color);
}

@keyframes glow-pulse {
  0% { filter: brightness(0.8) drop-shadow(0 0 2px var(--star-color)); transform: translate(-50%, -50%) scale(0.9); }
  100% { filter: brightness(1.2) drop-shadow(0 0 6px var(--star-color)); transform: translate(-50%, -50%) scale(1.1); }
}

.system-node.selected::before {
  box-shadow:
    -4px 0 0 var(--star-core), 4px 0 0 var(--star-core),
    0 -4px 0 var(--star-core), 0 4px 0 var(--star-core),
    -8px 0 0 var(--star-color), 8px 0 0 var(--star-color),
    0 -8px 0 var(--star-color), 0 8px 0 var(--star-color),
    -4px -4px 0 var(--star-color), -4px 4px 0 var(--star-color),
    4px -4px 0 var(--star-color), 4px 4px 0 var(--star-color),
    -12px 0 0 var(--star-dim), 12px 0 0 var(--star-dim),
    0 -12px 0 var(--star-dim), 0 12px 0 var(--star-dim),
    -8px -4px 0 var(--star-dim), -8px 4px 0 var(--star-dim),
    8px -4px 0 var(--star-dim), 8px 4px 0 var(--star-dim),
    -4px -8px 0 var(--star-dim), 4px -8px 0 var(--star-dim),
    -4px 8px 0 var(--star-dim), 4px 8px 0 var(--star-dim),
    0 0 0 4px #ffe082,
    0 0 15px 4px #ffe082,
    0 0 20px 4px var(--star-color);
}

.system-node.colony::before {
  box-shadow:
    -4px 0 0 var(--star-core), 4px 0 0 var(--star-core),
    0 -4px 0 var(--star-core), 0 4px 0 var(--star-core),
    -8px 0 0 var(--star-color), 8px 0 0 var(--star-color),
    0 -8px 0 var(--star-color), 0 8px 0 var(--star-color),
    -4px -4px 0 var(--star-color), -4px 4px 0 var(--star-color),
    4px -4px 0 var(--star-color), 4px 4px 0 var(--star-color),
    -12px 0 0 var(--star-dim), 12px 0 0 var(--star-dim),
    0 -12px 0 var(--star-dim), 0 12px 0 var(--star-dim),
    -8px -4px 0 var(--star-dim), -8px 4px 0 var(--star-dim),
    8px -4px 0 var(--star-dim), 8px 4px 0 var(--star-dim),
    -4px -8px 0 var(--star-dim), 4px -8px 0 var(--star-dim),
    -4px 8px 0 var(--star-dim), 4px 8px 0 var(--star-dim),
    0 0 10px rgba(141, 246, 191, 0.9),
    0 0 15px 4px var(--star-color);
}

.system-node.fleet::after {
  content: '';
  position: absolute;
  width: 6px;
  height: 6px;
  right: -5px;
  top: -3px;
  background: var(--primary-strong);
  box-shadow: 0 0 0.5rem rgba(103, 240, 255, 0.9);
  /* Make fleet pixel-ish too */
  border-radius: 0;
}

.system-label {
  position: absolute;
  left: 50%;
  top: 130%;
  transform: translateX(-50%);
  min-width: max-content;
  color: var(--text);
  font-size: 0.74rem;
  text-shadow: 0 0 0.35rem rgba(0, 0, 0, 0.8);
  font-family: monospace; /* Retro pixel font feel */
}

.star-red {
  --star-core: #ffb8bf;
  --star-color: #ff5d6c;
  --star-dim: rgba(255, 93, 108, 0.4);
}

.star-orange {
  --star-core: #ffdcba;
  --star-color: #ff9d3a;
  --star-dim: rgba(255, 157, 58, 0.4);
}

.star-yellow {
  --star-core: #fff1bb;
  --star-color: #ffd447;
  --star-dim: rgba(255, 212, 71, 0.4);
}

.star-white {
  --star-core: #ffffff;
  --star-color: #d5ecff;
  --star-dim: rgba(213, 236, 255, 0.4);
}

.star-blue {
  --star-core: #bce3ff;
  --star-color: #4bb7ff;
  --star-dim: rgba(75, 183, 255, 0.4);
}

.star-unknown {
  --star-core: #cbd3de;
  --star-color: #6881a1;
  --star-dim: rgba(104, 129, 161, 0.4);
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
