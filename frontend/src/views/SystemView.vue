<template>
  <div class="system-window">
    <header class="system-head">
      <div>
        <p class="eyebrow">SISTEMA</p>
        <h2 class="title">{{ system?.name || 'Cargando...' }}</h2>
        <p class="subtitle">
          <span :class="['star-tag', `tag-${system?.star_type || 'yellow'}`]">{{ system?.star_type || '?' }}</span>
          · {{ system?.planets?.length || 0 }} planeta(s)
          · rango {{ gameStore.maxJumps }} salto(s)
        </p>
      </div>
      <div class="head-actions">
        <button class="retro-btn" type="button" @click="reload" :disabled="loading">REFRESH</button>
        <button class="retro-btn" type="button" @click="goBack">VOLVER</button>
      </div>
    </header>

    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="info" class="info">{{ info }}</p>

    <div class="system-body" v-if="system">
      <!-- Pixel-art system lane: star + planets in a row -->
      <div class="lane">
        <div :class="['star-px', `star-${system.star_type || 'yellow'}`]" :title="system.star_type"></div>

        <button
          v-for="(planet, idx) in system.planets"
          :key="planet.index ?? idx"
          :class="['planet-px', `planet-${planet.type}`, planetStateClass(planet), selected?.index === planet.index ? 'is-selected' : '']"
          :title="planetTitle(planet)"
          type="button"
          @click="selectPlanet(planet)"
        >
          <span class="px-block"></span>
          <span class="px-name">{{ shortName(planet) }}</span>
        </button>
      </div>

      <!-- Detail / action panel -->
      <aside class="planet-panel" v-if="selected">
        <header class="panel-head">
          <h3>{{ selected.name }}</h3>
          <button class="close-btn" type="button" @click="selected = null">×</button>
        </header>
        <ul class="planet-stats">
          <li><span>Clima</span><strong>{{ selected.type }}</strong></li>
          <li><span>Tamano</span><strong>{{ selected.size }}</strong></li>
          <li><span>Minerales</span><strong>{{ selected.minerals }}</strong></li>
          <li><span>Gravedad</span><strong>{{ selected.gravity }}</strong></li>
          <li><span>Pob. max</span><strong>{{ selected.max_population }}</strong></li>
          <li><span>Dueno</span><strong :class="ownerClass(selected)">{{ selected.colonized_by || 'libre' }}</strong></li>
        </ul>

        <div v-if="selected.colonized_by === 'player'" class="hint">Es tuya. Pulsa "Ver colonia" para gestionarla.</div>
        <div v-else-if="selected.colonized_by" class="warn">
          Pertenece a {{ selected.colonized_by }}.
          <span v-if="canAssault">Puedes asaltar con marines.</span>
        </div>
        <div v-else>
          <div v-if="canColonizeThisPlanet" class="ok-hint">Tu nave colonizadora esta aqui.</div>
          <div v-else-if="!isHabitable" class="warn">Inhabitable sin tecnologia "Tolerante".</div>
          <div v-else-if="!playerColonyShipFleet" class="warn">No hay nave colonizadora en este sistema.</div>
        </div>

        <div class="actions">
          <button
            class="retro-btn ok"
            type="button"
            v-if="selected.colonized_by === 'player'"
            @click="goToColony"
          >
            VER COLONIA
          </button>
          <button
            class="retro-btn ok"
            type="button"
            :disabled="!canColonizeThisPlanet || busy"
            v-if="!selected.colonized_by"
            @click="colonize"
          >
            {{ busy ? 'COLONIZANDO...' : 'COLONIZAR' }}
          </button>
          <button
            class="retro-btn danger"
            type="button"
            :disabled="!canAssault || busy"
            v-if="selected.colonized_by && selected.colonized_by !== 'player'"
            @click="assault"
          >
            ASALTAR
          </button>
        </div>
      </aside>
    </div>

    <!-- Fleets in system -->
    <section class="fleets-here" v-if="system">
      <h3>Flotas en orbita</h3>
      <div v-if="!fleetsHere.length" class="empty">No hay flotas tuyas en este sistema.</div>
      <div v-else class="fleet-list">
        <article v-for="fleet in fleetsHere" :key="fleet.id" class="fleet-card">
          <div>
            <strong>{{ fleet.name }}</strong>
            <small>{{ fleet.ships?.length || 0 }} grupo(s)</small>
          </div>
          <ul>
            <li v-for="(ship, i) in fleet.ships" :key="i">{{ ship.count }}× {{ ship.type }}</li>
          </ul>
        </article>
      </div>

      <h3 class="travel-heading">
        Mover flota aqui
        <small>(rango {{ gameStore.maxJumps }})</small>
      </h3>
      <div class="move-row" v-if="movableFleets.length">
        <select v-model="moveDraft.fleetId">
          <option value="">selecciona flota</option>
          <option v-for="f in movableFleets" :key="f.id" :value="f.id">
            {{ f.name }} ({{ getSystemName(f.star_system_id) }})
          </option>
        </select>
        <button class="retro-btn" type="button" :disabled="!moveDraft.fleetId" @click="moveHere">SALTAR AQUI</button>
      </div>
      <p v-else class="empty">Ninguna flota tuya alcanza este sistema con tu tecnologia actual.</p>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api/client'
import { useGameStore } from '../store/gameStore'
import { reachableSystems } from '../store/reachable'

const route = useRoute()
const router = useRouter()
const gameStore = useGameStore()

const system = ref<any>(null)
const selected = ref<any>(null)
const error = ref('')
const info = ref('')
const loading = ref(false)
const busy = ref(false)
const moveDraft = ref<{ fleetId: string }>({ fleetId: '' })

const sysId = computed(() => String(route.params.sysId || ''))
const gameId = computed(() => String(route.params.id || gameStore.gameId || ''))

const allSystems = computed<any[]>(() => gameStore.galaxy?.star_systems || [])
const playerFleets = computed<any[]>(() => gameStore.fleets || [])
const fleetsHere = computed<any[]>(() => playerFleets.value.filter((f) => f.star_system_id === sysId.value && !f.destination))

const playerColonyShipFleet = computed<any | null>(() =>
  fleetsHere.value.find((f) => (f.ships || []).some((s: any) => s.type === 'colony_ship' && s.count > 0)) || null,
)
const playerTransportFleet = computed<any | null>(() =>
  fleetsHere.value.find((f) => (f.ships || []).some((s: any) => s.type === 'transport' && s.count > 0)) || null,
)

const playerFlags = computed<any>(() => gameStore.game?.player?.race?.traits?.flags || {})
const isHabitable = computed(() => isPlanetHabitable(selected.value))
const canColonizeThisPlanet = computed(() => {
  if (!selected.value) return false
  if (selected.value.colonized_by) return false
  if (!isPlanetHabitable(selected.value)) return false
  return !!playerColonyShipFleet.value
})
const canAssault = computed(() => !!playerTransportFleet.value && selected.value?.colonized_by && selected.value.colonized_by !== 'player')

const movableFleets = computed<any[]>(() => {
  const jumps = gameStore.maxJumps
  return playerFleets.value.filter((f) => {
    if (f.destination) return false
    if (f.star_system_id === sysId.value) return false
    const reach = reachableSystems(allSystems.value, f.star_system_id, jumps)
    return reach.has(sysId.value)
  })
})

function isPlanetHabitable(planet: any) {
  if (!planet) return false
  const inhospitable = ['toxic', 'radiated', 'barren']
  if (playerFlags.value?.tolerant) return planet.type !== 'asteroid_belt' && planet.type !== 'gas_giant'
  return !inhospitable.includes(planet.type)
}

function planetStateClass(planet: any) {
  if (planet.colonized_by === 'player') return 'is-mine'
  if (planet.colonized_by) return 'is-enemy'
  return 'is-free'
}

function ownerClass(planet: any) {
  if (planet.colonized_by === 'player') return 'owner-mine'
  if (planet.colonized_by) return 'owner-enemy'
  return 'owner-free'
}

function planetTitle(planet: any) {
  return `${planet.name} · ${planet.type} · ${planet.minerals}${planet.colonized_by ? ' · ' + planet.colonized_by : ''}`
}

function shortName(planet: any) {
  if (!planet?.name) return ''
  const idx = planet.name.lastIndexOf(' ')
  return idx > 0 ? planet.name.slice(idx + 1) : planet.name
}

function getSystemName(id: string) {
  return allSystems.value.find((s: any) => s.id === id)?.name || id
}

function selectPlanet(planet: any) {
  selected.value = planet
}

function goBack() {
  router.push(`/game/${gameId.value}/galaxy`)
}

function goToColony() {
  if (!selected.value) return
  const colId = `col_${sysId.value}_${selected.value.index}`
  router.push(`/game/${gameId.value}/colony/${colId}`)
}

async function reload() {
  loading.value = true
  error.value = ''
  info.value = ''
  try {
    if (!gameStore.galaxy) await gameStore.fetchGalaxy()
    if (!gameStore.fleets?.length) await gameStore.fetchFleets()
    system.value = await api.galaxy.getSystem(gameId.value, sysId.value)
  } catch (err: any) {
    error.value = err.message || 'No se pudo cargar el sistema'
    system.value = null
  } finally {
    loading.value = false
  }
}

async function colonize() {
  if (!canColonizeThisPlanet.value || !selected.value) return
  busy.value = true
  error.value = ''
  info.value = ''
  try {
    const fleet = playerColonyShipFleet.value
    await api.fleet.colonize(gameId.value, fleet.id, selected.value.index)
    info.value = `${selected.value.name} colonizado.`
    await Promise.all([reload(), gameStore.fetchFleets(), gameStore.fetchColonies(), gameStore.fetchGalaxy()])
    selected.value = system.value?.planets?.find((p: any) => p.index === selected.value.index) || null
  } catch (err: any) {
    error.value = err.message || 'No se pudo colonizar'
  } finally {
    busy.value = false
  }
}

async function assault() {
  if (!canAssault.value || !selected.value) return
  const fleet = playerTransportFleet.value
  busy.value = true
  error.value = ''
  info.value = ''
  try {
    const colonyId = `col_${sysId.value}_${selected.value.index}`
    const res = await api.ground.assault(gameId.value, fleet.id, colonyId, false)
    info.value = res?.colony_captured ? 'Colonia capturada' : 'Asalto resuelto'
    await Promise.all([reload(), gameStore.fetchFleets(), gameStore.fetchColonies()])
  } catch (err: any) {
    error.value = err.message || 'No se pudo asaltar'
  } finally {
    busy.value = false
  }
}

async function moveHere() {
  if (!moveDraft.value.fleetId) return
  busy.value = true
  error.value = ''
  info.value = ''
  try {
    await api.fleet.move(gameId.value, moveDraft.value.fleetId, sysId.value)
    info.value = 'Flota en transito'
    moveDraft.value.fleetId = ''
    await gameStore.fetchFleets()
  } catch (err: any) {
    error.value = err.message || 'No se pudo mover la flota'
  } finally {
    busy.value = false
  }
}

watch(sysId, reload)

onMounted(reload)
</script>

<style scoped>
.system-window {
  padding: 0.7rem;
  border: 2px solid #44ee44;
  background: #04081a;
  font-family: 'Courier New', monospace;
  color: #cfffd4;
  image-rendering: pixelated;
}
.system-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 0.6rem;
  flex-wrap: wrap;
  margin-bottom: 0.6rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px dashed #1a3a1a;
}
.eyebrow {
  margin: 0;
  font-size: 0.65rem;
  letter-spacing: 0.18em;
  color: #5b8a5b;
  text-transform: uppercase;
}
.title {
  margin: 0.15rem 0 0;
  color: #88ff88;
  letter-spacing: 0.06em;
  font-size: 1.05rem;
  text-shadow: 2px 2px 0 #000;
}
.subtitle {
  margin: 0.25rem 0 0;
  color: #6cc26c;
  font-size: 0.72rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
  align-items: center;
}
.head-actions { display: flex; gap: 0.4rem; }

.retro-btn {
  background: #04081a;
  color: #44ee44;
  border: 2px solid #44ee44;
  padding: 0.25rem 0.55rem;
  cursor: pointer;
  font-family: 'Courier New', monospace;
  font-size: 0.7rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  box-shadow: 2px 2px 0 #002200;
}
.retro-btn:hover:not(:disabled) {
  background: #44ee44;
  color: #04081a;
  box-shadow: 0 0 0 #002200;
  transform: translate(2px, 2px);
}
.retro-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.retro-btn.ok { border-color: #88ff88; color: #88ff88; }
.retro-btn.ok:hover:not(:disabled) { background: #88ff88; color: #04081a; }
.retro-btn.danger { border-color: #ff5577; color: #ff5577; box-shadow: 2px 2px 0 #220000; }
.retro-btn.danger:hover:not(:disabled) { background: #ff5577; color: #04081a; }

.error { color: #ff5577; margin: 0.3rem 0; font-size: 0.78rem; }
.info  { color: #88ff88; margin: 0.3rem 0; font-size: 0.78rem; }

.star-tag {
  padding: 0 0.35rem;
  font-size: 0.65rem;
  border: 1px solid currentColor;
  text-transform: uppercase;
}
.tag-red { color: #ff7070; }
.tag-orange { color: #ffaa44; }
.tag-yellow { color: #ffeb66; }
.tag-white { color: #d8d8ff; }
.tag-blue { color: #88aaff; }
.tag-black_hole { color: #aa55ff; }

.system-body {
  display: grid;
  grid-template-columns: 1fr 240px;
  gap: 0.6rem;
  align-items: stretch;
}

/* Pixel-art lane: star on the left, planets in a row */
.lane {
  position: relative;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 12px;
  min-height: 130px;
  background:
    repeating-linear-gradient(
      0deg,
      rgba(0, 30, 0, 0) 0,
      rgba(0, 30, 0, 0) 6px,
      rgba(34, 80, 34, 0.18) 6px,
      rgba(34, 80, 34, 0.18) 7px
    ),
    repeating-linear-gradient(
      90deg,
      rgba(0, 30, 0, 0) 0,
      rgba(0, 30, 0, 0) 6px,
      rgba(34, 80, 34, 0.18) 6px,
      rgba(34, 80, 34, 0.18) 7px
    ),
    #02060f;
  border: 2px solid #1a3a1a;
  overflow-x: auto;
  overflow-y: hidden;
  flex-wrap: nowrap;
}

.star-px {
  flex: 0 0 auto;
  width: 32px;
  height: 32px;
  background: var(--star-fill, #ffeb66);
  box-shadow:
    0 0 0 2px var(--star-glow, #d8aa22),
    8px 0 0 -4px var(--star-glow, #d8aa22),
    -8px 0 0 -4px var(--star-glow, #d8aa22),
    0 8px 0 -4px var(--star-glow, #d8aa22),
    0 -8px 0 -4px var(--star-glow, #d8aa22);
  image-rendering: pixelated;
}
.star-red    { --star-fill: #ff6666; --star-glow: #aa3322; }
.star-orange { --star-fill: #ffaa44; --star-glow: #cc6633; }
.star-yellow { --star-fill: #ffeb66; --star-glow: #d8aa22; }
.star-white  { --star-fill: #ffffff; --star-glow: #cfd8ff; }
.star-blue   { --star-fill: #88aaff; --star-glow: #3344cc; }
.star-black_hole { --star-fill: #220033; --star-glow: #aa55ff; }

.planet-px {
  flex: 0 0 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  background: transparent;
  border: none;
  padding: 0;
  cursor: pointer;
  font-family: 'Courier New', monospace;
}
.planet-px .px-block {
  width: 20px;
  height: 20px;
  display: block;
  background: #aaaacc;
  box-shadow:
    inset 0 0 0 2px rgba(255, 255, 255, 0.18),
    inset -3px -3px 0 0 rgba(0, 0, 0, 0.55),
    0 0 0 2px #000;
  image-rendering: pixelated;
}
.planet-px .px-name {
  font-size: 0.62rem;
  letter-spacing: 0.04em;
  color: #88ff88;
  text-shadow: 1px 1px 0 #000;
  white-space: nowrap;
  max-width: 60px;
  overflow: hidden;
  text-overflow: ellipsis;
}
.planet-px:hover .px-block {
  outline: 2px solid #00ffff;
  outline-offset: 1px;
}
.planet-px.is-selected .px-block {
  outline: 2px solid #ffff66;
  outline-offset: 2px;
}
.planet-px.is-mine .px-block { box-shadow: inset 0 0 0 2px #88ff88, inset -3px -3px 0 0 #2a6a2a, 0 0 0 2px #000; }
.planet-px.is-enemy .px-block { box-shadow: inset 0 0 0 2px #ff7799, inset -3px -3px 0 0 #6a1a2a, 0 0 0 2px #000; }

/* Planet color palette by climate (solid colors, no gradients) */
.planet-toxic    .px-block { background: #663355; }
.planet-barren   .px-block { background: #555566; }
.planet-radiated .px-block { background: #88aa44; }
.planet-desert   .px-block { background: #d4a25a; }
.planet-tundra   .px-block { background: #c0d0e8; }
.planet-arid     .px-block { background: #aa8855; }
.planet-swamp    .px-block { background: #557755; }
.planet-ocean    .px-block { background: #4488cc; }
.planet-terran   .px-block { background: #44aa66; }
.planet-gaia     .px-block { background: #88ffaa; }

/* Side panel */
.planet-panel {
  background: #051509;
  border: 2px solid #44ee44;
  padding: 0.5rem 0.6rem;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  font-size: 0.78rem;
}
.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px dashed #1a3a1a;
  padding-bottom: 0.3rem;
}
.panel-head h3 {
  margin: 0;
  color: #88ff88;
  font-size: 0.85rem;
  letter-spacing: 0.04em;
}
.close-btn { background: transparent; color: #6cc26c; border: none; font-size: 1rem; cursor: pointer; }

.planet-stats { list-style: none; padding: 0; margin: 0; display: grid; gap: 0.2rem; }
.planet-stats li { display: flex; justify-content: space-between; font-size: 0.72rem; color: #6cc26c; }
.planet-stats strong { color: #cfffd4; }
.owner-mine  { color: #88ff88; }
.owner-enemy { color: #ff7799; }
.owner-free  { color: #aaaacc; }

.hint     { color: #88ff88; font-size: 0.72rem; }
.ok-hint  { color: #44ee88; font-size: 0.72rem; }
.warn     { color: #ffaa66; font-size: 0.72rem; }
.actions  { margin-top: 0.4rem; display: flex; gap: 0.3rem; flex-wrap: wrap; }

/* Fleets section */
.fleets-here {
  margin-top: 0.7rem;
  padding-top: 0.6rem;
  border-top: 2px dashed #1a3a1a;
}
.fleets-here h3 { margin: 0 0 0.3rem; color: #ffeb66; font-size: 0.78rem; letter-spacing: 0.06em; text-transform: uppercase; }
.travel-heading { margin-top: 0.5rem; }
.travel-heading small { color: #6cc26c; font-weight: normal; margin-left: 0.3rem; font-size: 0.65rem; }
.empty { color: #5b8a5b; font-style: italic; font-size: 0.72rem; }
.fleet-list { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 0.4rem; }
.fleet-card {
  background: #02060f;
  border: 2px solid #1a3a1a;
  padding: 0.35rem 0.5rem;
  font-size: 0.72rem;
}
.fleet-card strong { color: #cfffd4; display: block; }
.fleet-card small { color: #5b8a5b; }
.fleet-card ul { list-style: none; padding: 0.15rem 0 0; margin: 0; color: #88ff88; font-size: 0.7rem; }
.move-row { display: flex; gap: 0.3rem; align-items: center; flex-wrap: wrap; }
.move-row select {
  background: #02060f;
  color: #44ee44;
  border: 2px solid #44ee44;
  padding: 0.25rem 0.4rem;
  font-family: 'Courier New', monospace;
  font-size: 0.7rem;
}

@media (max-width: 1024px) {
  .system-body { grid-template-columns: 1fr; }
  .planet-panel { order: -1; }
}
</style>
