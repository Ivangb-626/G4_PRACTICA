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
        <div class="space-bg" aria-hidden="true">
          <div class="nebula nebula-1"></div>
          <div class="nebula nebula-2"></div>
          <div class="nebula nebula-3"></div>
          <div class="stars stars-far"></div>
          <div class="stars stars-mid"></div>
          <div class="stars stars-near"></div>
          <div class="twinkle"></div>
          <div class="grid-overlay"></div>
        </div>
        <div class="star-corona" :class="`star-${system.star_type}`" aria-hidden="true"></div>
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
  background: #02030a;
  border-radius: 12px;
  border: 1px solid rgba(89, 170, 255, 0.35);
  overflow: hidden;
  height: 500px;
  box-shadow:
    0 0 1.5rem rgba(79, 180, 255, 0.18) inset,
    0 0 0.8rem rgba(103, 240, 255, 0.25);
}

/* === ANIMATED SPACE BACKGROUND (shared with GalaxyMap) === */
.space-bg {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
  z-index: 0;
  background:
    radial-gradient(ellipse at 20% 30%, rgba(48, 22, 92, 0.55), transparent 55%),
    radial-gradient(ellipse at 80% 70%, rgba(13, 64, 110, 0.55), transparent 55%),
    radial-gradient(ellipse at 50% 50%, rgba(6, 12, 40, 0.6), transparent 70%),
    linear-gradient(180deg, #02030a 0%, #050920 50%, #02030a 100%);
}

.nebula {
  position: absolute;
  border-radius: 50%;
  filter: blur(40px);
  opacity: 0.45;
  mix-blend-mode: screen;
  animation: nebula-drift 60s ease-in-out infinite alternate;
}

.nebula-1 {
  width: 50%; height: 50%;
  top: -10%; left: -10%;
  background: radial-gradient(circle, rgba(140, 60, 200, 0.6), transparent 70%);
  animation-duration: 70s;
}

.nebula-2 {
  width: 60%; height: 60%;
  bottom: -20%; right: -15%;
  background: radial-gradient(circle, rgba(40, 130, 220, 0.55), transparent 70%);
  animation-duration: 90s;
  animation-direction: alternate-reverse;
}

.nebula-3 {
  width: 40%; height: 40%;
  top: 30%; left: 40%;
  background: radial-gradient(circle, rgba(220, 80, 130, 0.35), transparent 70%);
  animation-duration: 110s;
}

@keyframes nebula-drift {
  0% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(4%, -3%) scale(1.08); }
  100% { transform: translate(-3%, 4%) scale(0.95); }
}

.stars {
  position: absolute;
  inset: -100% -100%;
  width: 300%; height: 300%;
  background-repeat: repeat;
  image-rendering: pixelated;
}

.stars-far {
  background-image:
    radial-gradient(1px 1px at 20px 30px, rgba(255, 255, 255, 0.6), transparent),
    radial-gradient(1px 1px at 60px 80px, rgba(200, 220, 255, 0.55), transparent),
    radial-gradient(1px 1px at 110px 50px, rgba(255, 255, 255, 0.5), transparent),
    radial-gradient(1px 1px at 170px 120px, rgba(180, 200, 255, 0.45), transparent),
    radial-gradient(1px 1px at 220px 30px, rgba(255, 255, 255, 0.55), transparent),
    radial-gradient(1px 1px at 280px 90px, rgba(255, 240, 220, 0.5), transparent);
  background-size: 320px 160px;
  animation: stars-drift 240s linear infinite;
  opacity: 0.55;
}

.stars-mid {
  background-image:
    radial-gradient(1.5px 1.5px at 40px 60px, rgba(255, 255, 255, 0.85), transparent),
    radial-gradient(1.5px 1.5px at 130px 110px, rgba(180, 220, 255, 0.8), transparent),
    radial-gradient(1.5px 1.5px at 220px 40px, rgba(255, 255, 255, 0.75), transparent),
    radial-gradient(1.5px 1.5px at 300px 150px, rgba(255, 220, 200, 0.7), transparent);
  background-size: 360px 200px;
  animation: stars-drift 160s linear infinite;
  opacity: 0.75;
}

.stars-near {
  background-image:
    radial-gradient(2px 2px at 50px 80px, rgba(255, 255, 255, 1), transparent),
    radial-gradient(2px 2px at 180px 30px, rgba(170, 220, 255, 0.95), transparent),
    radial-gradient(2px 2px at 310px 120px, rgba(255, 240, 200, 0.9), transparent);
  background-size: 400px 220px;
  animation: stars-drift 90s linear infinite;
  opacity: 0.9;
}

@keyframes stars-drift {
  from { transform: translate(0, 0); }
  to { transform: translate(-300px, -200px); }
}

.twinkle {
  position: absolute;
  inset: 0;
  background-image:
    radial-gradient(1px 1px at 15% 25%, #ffffff, transparent),
    radial-gradient(1px 1px at 35% 75%, #aee3ff, transparent),
    radial-gradient(1px 1px at 55% 15%, #ffffff, transparent),
    radial-gradient(1px 1px at 78% 55%, #ffd9a8, transparent),
    radial-gradient(1px 1px at 88% 85%, #ffffff, transparent),
    radial-gradient(1px 1px at 25% 60%, #ffffff, transparent);
  animation: twinkle 3.6s ease-in-out infinite alternate;
}

@keyframes twinkle {
  0% { opacity: 0.25; }
  50% { opacity: 0.9; }
  100% { opacity: 0.4; }
}

.grid-overlay {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(89, 170, 255, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(89, 170, 255, 0.05) 1px, transparent 1px),
    repeating-linear-gradient(0deg, rgba(255, 255, 255, 0.025) 0 1px, transparent 1px 3px);
  background-size: 60px 60px, 60px 60px, 100% 3px;
  pointer-events: none;
  opacity: 0.6;
}

/* === RETRO PIXEL STAR === */
.star-corona {
  position: absolute;
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: radial-gradient(circle, var(--star-color) 0%, transparent 60%);
  filter: blur(8px);
  opacity: 0.65;
  z-index: 1;
  animation: corona-pulse 4s ease-in-out infinite alternate;
}

@keyframes corona-pulse {
  0% { transform: scale(0.85); opacity: 0.5; }
  100% { transform: scale(1.15); opacity: 0.85; }
}

.star-graphic.pixel-star {
  position: absolute;
  width: 56px;
  height: 56px;
  background: var(--star-core, #fff);
  image-rendering: pixelated;
  /* Chunky pixel polygon (8-bit style) */
  clip-path: polygon(
    25% 0%, 75% 0%,
    87.5% 12.5%, 100% 25%,
    100% 75%, 87.5% 87.5%,
    75% 100%, 25% 100%,
    12.5% 87.5%, 0% 75%,
    0% 25%, 12.5% 12.5%
  );
  box-shadow:
    inset -10px -10px 0 var(--star-color),
    inset -16px -16px 0 var(--star-dim),
    inset 6px 6px 0 rgba(255, 255, 255, 0.55);
  filter:
    drop-shadow(0 0 6px var(--star-core))
    drop-shadow(0 0 14px var(--star-color))
    drop-shadow(0 0 24px var(--star-color));
  z-index: 2;
  animation: spin 30s steps(12) infinite, star-pulse 2.6s ease-in-out infinite alternate;
}

/* Pixel sun rays */
.star-graphic.pixel-star::before,
.star-graphic.pixel-star::after {
  content: '';
  position: absolute;
  background: var(--star-color);
  box-shadow: 0 0 6px var(--star-color);
  z-index: -1;
}

.star-graphic.pixel-star::before {
  top: -14px; left: 50%;
  width: 4px; height: 12px;
  transform: translateX(-50%);
  box-shadow:
    0 80px 0 var(--star-color),
    -36px 40px 0 var(--star-color),
    36px 40px 0 var(--star-color),
    0 0 6px var(--star-color);
}

.star-graphic.pixel-star::after {
  top: 50%; left: -14px;
  width: 12px; height: 4px;
  transform: translateY(-50%);
  box-shadow:
    80px 0 0 var(--star-color),
    40px -36px 0 var(--star-color),
    40px 36px 0 var(--star-color),
    0 0 6px var(--star-color);
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes star-pulse {
  0% { filter: drop-shadow(0 0 4px var(--star-core)) drop-shadow(0 0 10px var(--star-color)) drop-shadow(0 0 18px var(--star-color)); }
  100% { filter: drop-shadow(0 0 8px var(--star-core)) drop-shadow(0 0 18px var(--star-color)) drop-shadow(0 0 32px var(--star-color)); }
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
  border: 1px dashed rgba(103, 240, 255, 0.32);
  box-shadow: 0 0 0.4rem rgba(103, 240, 255, 0.08) inset;
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
  image-rendering: pixelated;

  /* Chunky pixel polygon — retro 8-bit ball */
  border-radius: 0 !important;
  clip-path: polygon(
    25% 0%, 75% 0%,
    87.5% 12.5%, 100% 25%,
    100% 75%, 87.5% 87.5%,
    75% 100%, 25% 100%,
    12.5% 87.5%, 0% 75%,
    0% 25%, 12.5% 12.5%
  );

  /* Hard banded shading — no blur for that pixel feel */
  box-shadow:
    inset -3px -3px 0 var(--p-color),
    inset -7px -7px 0 var(--p-color),
    inset -11px -11px 0 var(--p-dim),
    inset 3px 3px 0 rgba(255, 255, 255, 0.55),
    inset 6px 6px 0 rgba(255, 255, 255, 0.18),
    0 0 0.5rem var(--p-color),
    0 0 1rem var(--p-dim);
  filter: drop-shadow(0 0 4px var(--p-dim));
  transition: transform 0.2s ease;
}

.planet-graphic.pixel-planet:hover {
  filter: drop-shadow(0 0 8px var(--p-color)) drop-shadow(0 0 14px var(--p-color));
}

/* Base removed to use real width/height and pixelated borders instead of pseudo boxes */
.planet-graphic.pixel-planet::before {
  display: none;
}

.planet-graphic.selected.pixel-planet {
  box-shadow:
    inset -3px -3px 0 var(--p-color),
    inset -7px -7px 0 var(--p-color),
    inset -11px -11px 0 var(--p-dim),
    inset 3px 3px 0 rgba(255, 255, 255, 0.55),
    inset 6px 6px 0 rgba(255, 255, 255, 0.18),
    0 0 0 3px #67f0ff,
    0 0 14px 4px #67f0ff;
  filter: drop-shadow(0 0 8px #67f0ff);
}

.planet-graphic.owned.pixel-planet {
  box-shadow:
    inset -3px -3px 0 var(--p-color),
    inset -7px -7px 0 var(--p-color),
    inset -11px -11px 0 var(--p-dim),
    inset 3px 3px 0 rgba(255, 255, 255, 0.55),
    inset 6px 6px 0 rgba(255, 255, 255, 0.18),
    0 0 0 2px #8df6bf,
    0 0 12px 3px rgba(141, 246, 191, 0.7);
}

.planet-type-terran, .planet-type-ocean { --p-core: #8bf9b0; --p-color: #3b9e59; --p-dim: #1e5a5f; }
.planet-type-barren, .planet-type-desert { --p-core: #ebd9b5; --p-color: #ba8842; --p-dim: #6b4317; }
.planet-type-toxic, .planet-type-radiated { --p-core: #cfff9c; --p-color: #72a849; --p-dim: #325a17; }
.planet-type-tundra { --p-core: #ffffff; --p-color: #8daeb2; --p-dim: #446366; }
.planet-type-gas-giant { --p-core: #ffe8d3; --p-color: #cf8449; --p-dim: #844517; }

.planet-name-label {
  display: block;
  position: absolute;
  top: calc(50% + 30px);
  left: 50%;
  transform: translateX(-50%);
  font-size: 0.74rem;
  font-family: monospace;
  letter-spacing: 0.04em;
  color: var(--text);
  font-weight: bold;
  pointer-events: none;
  white-space: nowrap;
  text-shadow:
    0 0 4px #000,
    0 0 8px rgba(0, 0, 0, 0.9),
    0 0 0.4rem rgba(103, 240, 255, 0.4);
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
