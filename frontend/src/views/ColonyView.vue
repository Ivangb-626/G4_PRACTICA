<template>
  <div class="colony-window">
    <header class="colony-head">
      <div>
        <p class="eyebrow">COLONIA</p>
        <h2 class="title">{{ colonyLabel || 'Cargando...' }}</h2>
        <p class="subtitle" v-if="colony">
          <span :class="['planet-tag', `tag-${planetInfo?.type || ''}`]">{{ planetInfo?.type || '?' }}</span>
          · {{ planetInfo?.size || '?' }}
          · {{ planetInfo?.minerals || '?' }}
          · pob {{ colony.population?.total || 0 }}/{{ colony.population?.max || 0 }}
        </p>
      </div>
      <div class="head-actions">
        <button class="retro-btn" type="button" @click="reload" :disabled="loading">REFRESH</button>
        <button class="retro-btn" type="button" @click="goSystem">SISTEMA</button>
        <button class="retro-btn" type="button" @click="goBack">MAPA</button>
      </div>
    </header>

    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="info" class="info">{{ info }}</p>

    <div v-if="colony" class="body">
      <section class="stats-grid">
        <article class="stat-card stat-food">
          <span class="stat-label">COMIDA</span>
          <strong class="stat-value">{{ previewStats?.food !== null ? previewStats.food : colony.food_output || 0 }}</strong>
          <small class="stat-foot">surplus {{ colony.food_surplus || 0 }}</small>
        </article>
        <article class="stat-card stat-industry">
          <span class="stat-label">INDUSTRIA</span>
          <strong class="stat-value">{{ previewStats?.industry !== null ? previewStats.industry : colony.industry_output || 0 }}</strong>
          <small class="stat-foot">PP / turno</small>
        </article>
        <article class="stat-card stat-research">
          <span class="stat-label">CIENCIA</span>
          <strong class="stat-value">{{ previewStats?.research !== null ? previewStats.research : colony.research_output || 0 }}</strong>
          <small class="stat-foot">RP / turno</small>
        </article>
        <article class="stat-card stat-bc">
          <span class="stat-label">CREDITOS</span>
          <strong class="stat-value">{{ colony.bc_output || 0 }}</strong>
          <small class="stat-foot">BC / turno</small>
        </article>
      </section>

      <div class="split">
        <section class="panel">
          <header class="panel-head">
            <h3>TRABAJADORES</h3>
            <button class="retro-btn ok" type="button" @click="savePopulation" :disabled="!popDirty || saving">
              {{ saving ? '...' : 'APLICAR' }}
            </button>
          </header>
          <p class="panel-sub">
            asignados {{ totalAssigned }} / {{ colony.population?.total || 0 }}
            <span v-if="totalAssigned !== (colony.population?.total || 0)" class="warn">
              · {{ (colony.population?.total || 0) - totalAssigned }} sin asignar
            </span>
          </p>

          <div class="slider-row">
            <label>Agricultores: {{ pop.farmers }}</label>
            <input v-model.number="pop.farmers" type="range" min="0" :max="colony.population?.total || 0" @input="rebalance('farmers')" />
          </div>
          <div class="slider-row">
            <label>Trabajadores: {{ pop.workers }}</label>
            <input v-model.number="pop.workers" type="range" min="0" :max="colony.population?.total || 0" @input="rebalance('workers')" />
          </div>
          <div class="slider-row">
            <label>Cientificos: {{ pop.scientists }}</label>
            <input v-model.number="pop.scientists" type="range" min="0" :max="colony.population?.total || 0" @input="rebalance('scientists')" />
          </div>

          <div class="meta-row">
            <small>Moral: <strong>{{ moraleLabel }}</strong></small>
            <small>Defensa: <strong>{{ colony.ground_defense || 0 }}</strong></small>
            <small>Orbital: <strong>{{ colony.orbital_defense || 0 }}</strong></small>
          </div>
        </section>

        <section class="panel">
          <header class="panel-head">
            <h3>ESTRUCTURAS</h3>
            <span class="panel-sub">{{ builtBuildings.length }} construida(s)</span>
          </header>
          <ul v-if="builtBuildings.length" class="bld-list">
            <li v-for="b in builtBuildings" :key="b.id">
              <Tooltip :title="b.name || b.id" :description="b.description">
                <span class="bld-icon"></span>
                <div>
                  <strong>{{ b.name || b.id }}</strong>
                  <small v-if="b.description">{{ b.description }}</small>
                </div>
              </Tooltip>
            </li>
          </ul>
          <p v-else class="empty">Aun no hay edificios construidos.</p>
        </section>
      </div>

      <div class="split">
        <section class="panel">
          <header class="panel-head">
            <h3>COLA DE CONSTRUCCION</h3>
            <span class="panel-sub">{{ colony.build_queue?.length || 0 }} en cola</span>
          </header>
          <ul v-if="colony.build_queue?.length" class="queue-list">
            <li v-for="(item, idx) in colony.build_queue" :key="idx">
              <div style="flex:1;">
                <strong>{{ item.name || item.item_id }}</strong>
                <small>{{ item.progress || 0 }}/{{ item.cost || 0 }} PP</small>
                <div class="progress-bar">
                  <div class="progress-fill" :style="{ width: queuePercent(item) + '%' }"></div>
                </div>
              </div>
              <button class="retro-btn danger" type="button" @click="removeQueue(idx)">X</button>
            </li>
          </ul>
          <p v-else class="empty">La cola esta vacia.</p>
        </section>

        <section class="panel">
          <header class="panel-head">
            <h3>PROYECTOS</h3>
          </header>
          <div class="bld-grid" v-if="availableBuildings.length">
            <Tooltip
              v-for="b in availableBuildings"
              :key="b.id"
              :title="b.name"
              :description="b.description"
            >
              <button
                class="bld-card"
                type="button"
                @click="addBuilding(b.id)"
              >
                <strong>{{ b.name }}</strong>
                <small>{{ b.cost }} PP</small>
              </button>
            </Tooltip>
          </div>
          <p v-else class="empty">No hay edificios desbloqueados.</p>

          <header class="panel-head" style="margin-top: 0.6rem;">
            <h3>NAVES</h3>
          </header>
          <div class="bld-grid" v-if="availableShips.length">
            <Tooltip
              v-for="s in availableShips"
              :key="s.type"
              :title="s.name || s.type"
              :description="s.description"
            >
              <button
                class="bld-card"
                type="button"
                @click="addShip(s.type)"
              >
                <strong>{{ s.name || s.type }}</strong>
                <small>{{ s.cost }} PP</small>
              </button>
            </Tooltip>
          </div>
          <p v-else class="empty">No hay naves disponibles.</p>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api/client'
import { useGameStore } from '../store/gameStore'

type PopKey = 'farmers' | 'workers' | 'scientists'

const route = useRoute()
const router = useRouter()
const gameStore = useGameStore()

const colony = ref<any>(null)
const availableBuildings = ref<any[]>([])
const availableShips = ref<any[]>([])
const error = ref('')
const info = ref('')
const loading = ref(false)
const saving = ref(false)
const popDirty = ref(false)

const pop = reactive<Record<PopKey, number>>({ farmers: 0, workers: 0, scientists: 0 })

const colId = computed(() => String(route.params.colId || ''))
const gameId = computed(() => String(route.params.id || gameStore.gameId || ''))

const totalAssigned = computed(() => pop.farmers + pop.workers + pop.scientists)

const moraleLabel = computed(() => {
  const m = colony.value?.morale
  if (typeof m === 'number') return m > 0 ? `+${m}` : String(m)
  return m || 'estable'
})

const planetInfo = computed(() => {
  const sys = (gameStore.galaxy?.star_systems || []).find((s: any) => s.id === colony.value?.star_system_id)
  if (!sys) return null
  return sys.planets?.[colony.value?.planet_index] || null
})

const colonyLabel = computed(() => {
  const planetName = planetInfo.value?.name || colony.value?.planet_name || colony.value?.name || ''
  if (!planetName) return 'Colonia'
  if (/^Colonia:\s*".*"$/.test(colony.value?.name || '')) return colony.value?.name || ''
  return `Colonia: "${planetName}"`
})

const builtBuildings = computed(() => {
  const list = colony.value?.buildings || []
  return list.map((b: any) => {
    if (typeof b === 'string') {
      const found = availableBuildings.value.find((x: any) => x.id === b)
      return found || { id: b, name: b }
    }
    return b
  })
})

function queuePercent(item: any) {
  if (!item || !item.cost) return 0
  return Math.min(100, ((item.progress || 0) / item.cost) * 100)
}

function syncPop() {
  const p = colony.value?.population
  if (!p) {
    pop.farmers = 0
    pop.workers = 0
    pop.scientists = 0
    return
  }
  pop.farmers = p.farmers || 0
  pop.workers = p.workers || 0
  pop.scientists = p.scientists || 0
  popDirty.value = false
}

function rebalance(changed: PopKey) {
  popDirty.value = true
  const total = colony.value?.population?.total || 0
  let sum = pop.farmers + pop.workers + pop.scientists
  if (sum <= total) return
  const others: PopKey[] = (['farmers', 'workers', 'scientists'] as PopKey[]).filter((k) => k !== changed)
  for (const k of others) {
    const diff = sum - total
    if (diff <= 0) break
    const reduce = Math.min(pop[k], diff)
    pop[k] -= reduce
    sum -= reduce
  }
}

const previewStats = computed(() => {
  if (!colony.value || !planetInfo.value) return null;
  const tempColony = JSON.parse(JSON.stringify(colony.value));
  tempColony.population.farmers = pop.farmers;
  tempColony.population.workers = pop.workers;
  tempColony.population.scientists = pop.scientists;

  // This would ideally call a backend service or a local pure function
  // to calculate production based on the new assignments without saving.
  // For now, it's a simplified placeholder.
  return {
    food: (pop.farmers * (planetInfo.value.food_per_farmer || 1)) + (tempColony.food_output - colony.value.food_output),
    industry: (pop.workers * (planetInfo.value.industry_per_worker || 1)) + (tempColony.industry_output - colony.value.industry_output),
    research: (pop.scientists * (planetInfo.value.research_per_scientist || 1)) + (tempColony.research_output - colony.value.research_output),
  };
});

async function reload() {
  loading.value = true
  error.value = ''
  info.value = ''
  if (!gameStore.galaxy) await gameStore.fetchGalaxy().catch(() => undefined)
  try {
    const detail = await api.colony.get(gameId.value, colId.value)
    colony.value = detail.colony || detail
    availableBuildings.value = detail.available_buildings || []
    availableShips.value = detail.available_ships || []
    syncPop()
  } catch (err: any) {
    error.value = err?.message || 'No se pudo cargar la colonia'
    colony.value = null
  } finally {
    loading.value = false
  }
}

async function savePopulation() {
  if (!gameStore.gameId || !colId.value) return
  saving.value = true
  error.value = ''
  info.value = ''
  try {
    await api.colony.assign(gameStore.gameId, colId.value, { ...pop })
    info.value = 'Asignacion guardada'
    await reload()
  } catch (err: any) {
    error.value = err?.message || 'No se pudo guardar la asignacion'
  } finally {
    saving.value = false
  }
}

async function addBuilding(id: string) {
  if (!gameStore.gameId || !colId.value) return
  error.value = ''
  info.value = ''
  try {
    await api.colony.buildQueue(gameStore.gameId, colId.value, { item_type: 'building', item_id: id })
    info.value = `${id} en cola`
    await reload()
  } catch (err: any) {
    error.value = err?.message || 'No se pudo encolar'
  }
}

async function addShip(shipType: string) {
  if (!gameStore.gameId || !colId.value) return
  error.value = ''
  info.value = ''
  try {
    await api.colony.buildQueue(gameStore.gameId, colId.value, { item_type: 'ship', item_id: shipType })
    info.value = `${shipType} en cola`
    await reload()
  } catch (err: any) {
    error.value = err?.message || 'No se pudo encolar la nave'
  }
}

async function removeQueue(idx: number) {
  if (!gameStore.gameId || !colId.value) return
  if (!confirm('¿Quitar este item de la cola de construcción?')) return
  try {
    await api.colony.removeQueueItem(gameStore.gameId, colId.value, idx)
    await reload()
  } catch (err: any) {
    error.value = err?.message || 'No se pudo quitar de la cola'
  }
}

function goBack() {
  router.push(`/game/${gameId.value}/galaxy`)
}

function goSystem() {
  if (!colony.value) return
  router.push(`/game/${gameId.value}/system/${colony.value.star_system_id}`)
}

watch(colId, reload)

onMounted(reload)
</script>

<style scoped>
.colony-window {
  padding: 0.7rem;
  border: 2px solid #44ee44;
  background: #04081a;
  font-family: 'Courier New', monospace;
  color: #cfffd4;
  image-rendering: pixelated;
}
.colony-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 0.6rem;
  flex-wrap: wrap;
  margin-bottom: 0.6rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px dashed #1a3a1a;
}
.eyebrow { margin: 0; font-size: 0.65rem; letter-spacing: 0.18em; color: #5b8a5b; text-transform: uppercase; }
.title { margin: 0.15rem 0 0; color: #88ff88; letter-spacing: 0.06em; font-size: 1.05rem; text-shadow: 2px 2px 0 #000; }
.subtitle { margin: 0.25rem 0 0; color: #6cc26c; font-size: 0.72rem; display: flex; flex-wrap: wrap; gap: 0.3rem; align-items: center; }
.head-actions { display: flex; gap: 0.4rem; flex-wrap: wrap; }

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

.planet-tag {
  padding: 0 0.35rem;
  font-size: 0.65rem;
  border: 1px solid currentColor;
  text-transform: uppercase;
}
.tag-toxic { color: #aa66cc; }
.tag-barren { color: #888899; }
.tag-radiated { color: #aaee44; }
.tag-desert { color: #d4a25a; }
.tag-tundra { color: #c0d0e8; }
.tag-arid { color: #aa8855; }
.tag-swamp { color: #88aa88; }
.tag-ocean { color: #66aaff; }
.tag-terran { color: #66dd88; }
.tag-gaia { color: #88ffaa; }

.body { display: flex; flex-direction: column; gap: 0.6rem; }

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.5rem;
}
.stat-card {
  background: #02060f;
  border: 2px solid #1a3a1a;
  padding: 0.45rem 0.55rem;
  text-align: center;
  box-shadow: 3px 3px 0 #000;
}
.stat-label { display: block; font-size: 0.65rem; letter-spacing: 0.1em; color: #5b8a5b; }
.stat-value { display: block; font-size: 1.4rem; color: #88ff88; text-shadow: 2px 2px 0 #000; margin-top: 0.15rem; line-height: 1; }
.stat-foot { display: block; font-size: 0.62rem; color: #6cc26c; margin-top: 0.2rem; }
.stat-food .stat-value     { color: #88ffaa; }
.stat-industry .stat-value { color: #ffaa44; }
.stat-research .stat-value { color: #88aaff; }
.stat-bc .stat-value       { color: #ffeb66; }

.split {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.6rem;
}

.panel {
  background: #051509;
  border: 2px solid #1a3a1a;
  padding: 0.55rem 0.6rem;
  font-size: 0.78rem;
}
.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.45rem;
  padding-bottom: 0.3rem;
  border-bottom: 1px dashed #1a3a1a;
}
.panel-head h3 {
  margin: 0;
  color: #88ff88;
  font-size: 0.78rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.panel-sub { color: #6cc26c; font-size: 0.7rem; }

.slider-row { display: grid; gap: 0.15rem; margin-bottom: 0.45rem; }
.slider-row label { color: #88ff88; font-size: 0.72rem; }
.slider-row input {
  appearance: none;
  width: 100%;
  height: 8px;
  background: #02060f;
  border: 2px solid #1a3a1a;
  outline: none;
  image-rendering: pixelated;
}
.slider-row input::-webkit-slider-thumb {
  appearance: none;
  width: 12px;
  height: 14px;
  background: #88ff88;
  border: 2px solid #04081a;
  cursor: pointer;
}
.slider-row input::-moz-range-thumb {
  width: 12px;
  height: 14px;
  background: #88ff88;
  border: 2px solid #04081a;
  cursor: pointer;
}
.meta-row {
  display: flex;
  gap: 0.6rem;
  flex-wrap: wrap;
  margin-top: 0.3rem;
  padding-top: 0.3rem;
  border-top: 1px dashed #1a3a1a;
  color: #6cc26c;
  font-size: 0.68rem;
}
.meta-row strong { color: #cfffd4; }
.warn { color: #ffaa66; }

.bld-list { list-style: none; padding: 0; margin: 0; display: grid; gap: 0.25rem; }
.bld-list li {
  display: flex;
  gap: 0.45rem;
  align-items: flex-start;
  padding: 0.3rem 0.4rem;
  background: #02060f;
  border: 1px solid #1a3a1a;
}
.bld-icon {
  flex: 0 0 auto;
  width: 14px;
  height: 14px;
  background: #88ff88;
  box-shadow: inset 0 0 0 2px #2a6a2a, 0 0 0 1px #000;
  margin-top: 2px;
  image-rendering: pixelated;
}
.bld-list strong { display: block; color: #cfffd4; font-size: 0.74rem; }
.bld-list small { display: block; color: #6cc26c; font-size: 0.66rem; }

.queue-list { list-style: none; padding: 0; margin: 0; display: grid; gap: 0.3rem; }
.queue-list li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.35rem 0.5rem;
  background: #02060f;
  border: 2px solid #ffeb66;
  gap: 0.5rem;
}
.queue-list strong { color: #cfffd4; display: block; font-size: 0.74rem; }
.queue-list small { color: #6cc26c; font-size: 0.65rem; }
.progress-bar {
  margin-top: 0.25rem;
  width: 100%;
  height: 6px;
  background: #04081a;
  border: 1px solid #1a3a1a;
  image-rendering: pixelated;
}
.progress-fill {
  height: 100%;
  background: #ffeb66;
  box-shadow: inset 0 -2px 0 #aa7711;
}

.bld-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 0.35rem;
}
.bld-card {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.15rem;
  padding: 0.4rem 0.5rem;
  background: #02060f;
  border: 2px solid #44ee44;
  color: #cfffd4;
  font-family: 'Courier New', monospace;
  cursor: pointer;
  text-align: left;
  font-size: 0.72rem;
  box-shadow: 2px 2px 0 #002200;
  transition: transform 0.06s, background 0.1s;
}
.bld-card:hover {
  background: #44ee44;
  color: #04081a;
  box-shadow: 0 0 0 #002200;
  transform: translate(2px, 2px);
}
.bld-card strong { font-size: 0.74rem; }
.bld-card small { color: #6cc26c; }
.bld-card:hover small { color: #04081a; }

.empty { color: #5b8a5b; font-style: italic; font-size: 0.72rem; }

@media (max-width: 1024px) {
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
  .split { grid-template-columns: 1fr; }
}
</style>
