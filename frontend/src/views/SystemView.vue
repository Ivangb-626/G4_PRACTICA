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

      <div class="system-graphic">
        <div class="star-graphic pixel-star" :class="`star-${system.star_type}`" :title="system.star_type"></div>
        <div 
          v-for="(planet, idx) in system.planets" 
          :key="planet.index" 
          class="planet-orbit"
          :style="{ 
            width: `${140 + idx * 80}px`, 
            height: `${140 + idx * 80}px`,
            transform: `rotate(${idx * (360 / (system.planets.length || 1))}deg)`
          }"
        >
          <div
            class="planet-container"
            :style="{
              transform: `translate(-50%, -50%) rotate(-${idx * (360 / (system.planets.length || 1))}deg)`
            }"
          >
            <button 
              type="button"
              class="planet-graphic pixel-planet"
              :class="[
                `planet-type-${(planet.type || '').toLowerCase().replace(/\s+/g, '-')}`, 
                { selected: selectedPlanetIndex === planet.index, owned: planet.colonized_by === 'player' }
              ]"
              @click.stop="handlePlanetClick(planet)"
              :title="planet.name"
              :style="{ 
                width: getPlanetSize(planet.size) + 'px', 
                height: getPlanetSize(planet.size) + 'px',
                animationDuration: `${10 + idx * 5}s`
              }"
            >
              <span class="sr-only">{{ planet.name }}</span>
            </button>
            <span class="planet-name-label">{{ planet.name }}</span>
          </div>
        </div>
      </div>
      
      <div class="planet-detail-area" v-if="selectedPlanet">
        <div class="planet-card selected-planet-card">
          <header class="planet-head">
            <div>
              <h4>{{ selectedPlanet.name }}</h4>
              <p>{{ selectedPlanet.type }} · {{ selectedPlanet.size }} · {{ selectedPlanet.gravity }}</p>
            </div>
            <span class="status-pill" :class="{ owned: selectedPlanet.colonized_by === 'player' }">
              {{ selectedPlanet.colonized_by || 'Libre' }}
            </span>
          </header>

          <p class="planet-meta">Minerales: {{ selectedPlanet.minerals }} · Max pop: {{ selectedPlanet.max_population }}</p>

          <div class="planet-actions">
            <button
              v-if="selectedPlanet.colonized_by === 'player'"
              class="retro-btn"
              type="button"
              @click="openColony(selectedPlanet.index)"
            >
              Gestionar colonia
            </button>
            <button
              v-else-if="colonizerFleetId"
              class="retro-btn"
              type="button"
              @click="colonizePlanet(selectedPlanet.index)"
              :disabled="colonizingPlanetIndex === selectedPlanet.index"
            >
              {{ colonizingPlanetIndex === selectedPlanet.index ? 'Colonizando...' : 'Colonizar' }}
            </button>
          </div>
        </div>
      </div>
      <p v-else class="empty select-hint">Selecciona un planeta gráficamente para ver sus detalles</p>
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
const selectedPlanetIndex = ref<number | null>(null)

const selectedPlanet = computed(() => {
  return system.value?.planets.find((p) => p.index === selectedPlanetIndex.value) || null
})

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

function handlePlanetClick(planet: any) {
  selectedPlanetIndex.value = planet.index
  if (planet.colonized_by === 'player') {
    openColony(planet.index)
  }
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

function getPlanetSize(sizeString: string) {
  const sizeMap: Record<string, number> = {
    tiny: 18,
    small: 28,
    medium: 38,
    large: 48,
    huge: 58,
    giant: 70
  }
  const key = (sizeString || 'medium').toLowerCase()
  return sizeMap[key] || 38
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

.system-graphic {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4rem;
  margin: 2rem 0;
  background: rgba(4, 9, 23, 0.4);
  border-radius: 12px;
  border: 1px dashed rgba(89, 170, 255, 0.15);
  overflow: hidden;
  height: 500px;
}

.star-graphic.pixel-star {
  position: absolute;
  width: 48px;
  height: 48px;
  background: var(--star-core, #fff);
  /* Pixel art hard edges for circle */
  clip-path: polygon(
    30% 0%, 70% 0%,
    85% 15%, 100% 30%,
    100% 70%, 85% 85%,
    70% 100%, 30% 100%,
    15% 85%, 0% 70%,
    0% 30%, 15% 15%
  );
  box-shadow:
    inset -8px -8px 0 var(--star-color),
    inset 4px 4px 0 rgba(255, 255, 255, 0.4);
  /* The glow filter applies nicely over the clip path */
  filter: drop-shadow(0 0 15px var(--star-color)) drop-shadow(0 0 5px var(--star-color));
  z-index: 2;
  animation: spin 30s steps(12) infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Star color CSS variables */
.star-red { --star-core: #ffb8bf; --star-color: #ff5d6c; --star-dim: rgba(255, 93, 108, 0.4); }
.star-orange { --star-core: #ffdcba; --star-color: #ff9d3a; --star-dim: rgba(255, 157, 58, 0.4); }
.star-yellow { --star-core: #fff1bb; --star-color: #ffd447; --star-dim: rgba(255, 212, 71, 0.4); }
.star-white { --star-core: #ffffff; --star-color: #d5ecff; --star-dim: rgba(213, 236, 255, 0.4); }
.star-blue { --star-core: #bce3ff; --star-color: #4bb7ff; --star-dim: rgba(75, 183, 255, 0.4); }
.star-unknown { --star-core: #cbd3de; --star-color: #6881a1; --star-dim: rgba(104, 129, 161, 0.4); }

.planet-orbit {
  position: absolute;
  border-radius: 50%;
  border: 1px dashed rgba(89, 170, 255, 0.25);
  display: flex;
  align-items: center;
  justify-content: flex-start;
  z-index: 3;
}

.planet-container {
  position: absolute;
  left: 0;
  top: 50%;
  /* We start at top left edge of the orbit border. The rotate offset is applied inline so it stays upright! */
  display: flex;
  align-items: center;
  justify-content: center;
  width: 0; 
  height: 0;
}

.planet-graphic.pixel-planet {
  position: relative;
  display: block;
  background: var(--p-core, #ccc) !important;
  border: none;
  cursor: pointer;
  padding: 0;
  box-sizing: border-box;
  aspect-ratio: 1 / 1;
  transform-origin: center;
  animation: spin var(--duration, 15s) linear infinite;
  
  /* Smooth shape */
  border-radius: 50% !important;
  
  /* Hard shading without blur */
  box-shadow:
    inset -6px -6px 0 var(--p-color),
    inset -12px -12px 0 var(--p-dim),
    inset 4px 4px 0 rgba(255,255,255,0.3);
}

/* Base removed to use real width/height and pixelated borders instead of pseudo boxes */
.planet-graphic.pixel-planet::before {
  display: none;
}

.planet-graphic.selected.pixel-planet {
  /* Go back to outline/box shadow for round elements */
  outline: 2px dashed #67f0ff;
  outline-offset: 6px;
  box-shadow:
    0 0 15px 4px #67f0ff,
    inset -6px -6px 0 var(--p-color),
    inset -12px -12px 0 var(--p-dim),
    inset 4px 4px 0 rgba(255,255,255,0.3);
}

.planet-graphic.owned.pixel-planet {
  outline: 2px dashed #8df6bf;
  outline-offset: 4px;
}

.planet-type-terran, .planet-type-ocean { --p-core: #8bf9b0; --p-color: #3b9e59; --p-dim: #1e5a5f; }
.planet-type-barren, .planet-type-desert { --p-core: #ebd9b5; --p-color: #ba8842; --p-dim: #6b4317; }
.planet-type-toxic, .planet-type-radiated { --p-core: #cfff9c; --p-color: #72a849; --p-dim: #325a17; }
.planet-type-tundra { --p-core: #ffffff; --p-color: #8daeb2; --p-dim: #446366; }
.planet-type-gas-giant { --p-core: #ffe8d3; --p-color: #cf8449; --p-dim: #844517; }

.planet-name-label {
  display: block;
  position: absolute;
  top: calc(50% + 30px); /* Just below planet */
  left: 50%;
  transform: translateX(-50%);
  font-size: 0.75rem;
  color: var(--text);
  font-weight: bold;
  pointer-events: none;
  white-space: nowrap;
  text-shadow: 0 0 5px #000;
  z-index: 4;
}

.planet-detail-area {
  margin-top: 1rem;
}

.planet-card {
  padding: 1.25rem;
  border: 1px solid rgba(89, 170, 255, 0.18);
  border-radius: 10px;
  background: rgba(7, 15, 36, 0.85);
}

.select-hint {
  padding: 1rem;
  text-align: center;
  font-style: italic;
  border: 1px dashed rgba(89,170,255,0.2);
  border-radius: 8px;
  background: rgba(7, 15, 36, 0.4);
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
</style>
