<template>
  <div :style="styles.container" ref="containerRef">
    <canvas
      ref="canvasRef"
      @mousedown="handleMouseDown"
      @mousemove="handleMouseMove"
      @mouseup="handleMouseUp"
      @mouseleave="handleMouseUp"
      @click="handleClick"
      @wheel.prevent="handleWheel"
      :style="styles.canvas"
    ></canvas>

    <div :style="styles.mapToolbar">
      <input
        v-model.trim="systemQuery"
        :style="styles.searchInput"
        list="galaxy-systems"
        placeholder="Buscar sistema..."
        type="search"
        @keydown.enter="selectFirstMatch"
      />
      <datalist id="galaxy-systems">
        <option v-for="system in allSystems" :key="system.id" :value="system.name" />
      </datalist>
      <button class="retro-btn map-btn" type="button" @click="selectFirstMatch">Ir</button>
      <button class="retro-btn map-btn" type="button" @click="zoomOut">-</button>
      <button class="retro-btn map-btn" type="button" @click="resetView">Reset</button>
      <button class="retro-btn map-btn" type="button" @click="zoomIn">+</button>
    </div>

    <!-- Selected system overlay -->
    <div v-if="selectedInfo" :style="styles.systemPanel">
      <div :style="styles.systemTitle">{{ selectedInfo.name }}</div>
      <div :style="styles.systemMeta">
        {{ selectedInfo.star_type }} · {{ selectedInfo.planets?.length || 0 }} planeta(s)
      </div>
      <ul :style="styles.planetList" v-if="selectedInfo.planets?.length">
        <li v-for="p in selectedInfo.planets" :key="p.index">
          <strong>{{ p.name }}</strong> · {{ p.type }} · {{ p.minerals }}
          <em v-if="p.colonized_by">[{{ p.colonized_by }}]</em>
        </li>
      </ul>
      <div :style="styles.actionRow">
        <button class="retro-btn" type="button" @click="goToSystem" v-if="selectedInfo.id">Ver sistema</button>
        <button class="retro-btn" type="button" @click="travelMode = !travelMode" v-if="canTravelHere">
          {{ travelMode ? 'Cancelar' : 'Viajar aqui' }}
        </button>
      </div>
      <p v-if="!canTravelHere && selectedInfo.id && cantTravelReason" :style="styles.warn">
        {{ cantTravelReason }}
      </p>

      <!-- Fleet picker -->
      <div v-if="travelMode" :style="styles.travelBox">
        <p :style="styles.travelTitle">Selecciona la flota:</p>
        <div v-if="travelableFleets.length">
          <label v-for="fleet in travelableFleets" :key="fleet.id" :style="styles.fleetOption">
            <input type="radio" :value="fleet.id" v-model="chosenFleetId" />
            <span>
              <strong>{{ fleet.name }}</strong>
              <small> ({{ getSystemName(fleet.star_system_id) }})</small>
              <small> {{ fleet.ships?.length || 0 }} grupo(s)</small>
            </span>
          </label>
        </div>
        <p v-else :style="styles.warn">Ninguna flota tuya alcanza este sistema.</p>
        <button class="retro-btn" type="button" :disabled="!chosenFleetId || launching" @click="launchTravel">
          {{ launching ? 'EN MARCHA...' : 'PREVISUALIZAR VIAJE' }}
        </button>
        <p v-if="chosenFleetId" :style="styles.travelImpact">{{ travelPreview }}</p>
        <p v-if="travelMessage" :style="styles.travelMsg">{{ travelMessage }}</p>
      </div>
    </div>

    <div v-if="hoveredInfo" :style="hoverTooltipStyle">
      <strong>{{ hoveredInfo.name }}</strong>
      <span>{{ hoveredInfo.star_type }} · {{ hoveredInfo.planets?.length || 0 }} planeta(s)</span>
      <span v-if="hoveredInfo.has_player_colony">Colonia propia detectada</span>
      <span v-else-if="hoveredInfo.has_enemy_fleet">Actividad hostil detectada</span>
      <span v-else>Click para seleccionar</span>
    </div>

    <!-- Zoom indicator (overrides parent zoom indicator visually) -->
    <div :style="styles.zoomOverlay">
      ZOOM: {{ Math.round(zoom * 100) }}%
    </div>

    <div v-if="error" :style="styles.error">{{ error }}</div>
    <div v-if="loading" :style="styles.loading">SCANNING SECTOR...</div>

    <div v-if="confirmTravelOpen" class="map-modal">
      <div class="map-modal-card">
        <header>
          <strong>Confirmar movimiento</strong>
          <button type="button" @click="confirmTravelOpen = false">×</button>
        </header>
        <p>{{ travelPreview }}</p>
        <ul>
          <li>La flota quedara en transito y no podra actuar hasta llegar.</li>
          <li>El destino puede activar combate si hay fuerzas hostiles.</li>
        </ul>
        <div class="map-modal-actions">
          <button class="retro-btn" type="button" @click="confirmTravelOpen = false">Cancelar</button>
          <button class="retro-btn" type="button" :disabled="launching" @click="confirmLaunchTravel">Confirmar</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useGameStore } from '../store/gameStore'
import { useUIStore } from '../store/uiStore'
import { renderGalaxy } from '../canvas/galaxyRenderer'
import { reachableSystems } from '../store/reachable'
import { api } from '../api/client'

const gameStore = useGameStore()
const uiStore = useUIStore()
const route = useRoute()
const router = useRouter()

const containerRef = ref<HTMLDivElement | null>(null)
const canvasRef = ref<HTMLCanvasElement | null>(null)

const zoom = ref(1.0)
const panX = ref(0)
const panY = ref(0)
const loading = ref(false)
const error = ref('')

const travelMode = ref(false)
const chosenFleetId = ref('')
const launching = ref(false)
const travelMessage = ref('')
const confirmTravelOpen = ref(false)
const systemQuery = ref('')
const hoveredInfo = ref<any | null>(null)
const hoverPos = ref({ x: 0, y: 0 })

const isDragging = ref(false)
const wasDragging = ref(false)
const lastMouseX = ref(0)
const lastMouseY = ref(0)

const styles = {
  container: {
    position: 'relative' as const,
    width: '100%',
    height: '60vh',
    minHeight: '420px',
    overflow: 'hidden',
    backgroundColor: '#000',
    border: '1px solid rgba(89, 170, 255, 0.25)',
    borderRadius: '8px',
  },
  canvas: { display: 'block', cursor: 'crosshair' },
  mapToolbar: {
    position: 'absolute' as const,
    top: '0.6rem',
    right: '0.6rem',
    display: 'flex',
    gap: '0.35rem',
    flexWrap: 'wrap' as const,
    justifyContent: 'flex-end' as const,
    maxWidth: 'min(520px, calc(100% - 1.2rem))',
    pointerEvents: 'auto' as const,
  },
  searchInput: {
    minWidth: '180px',
    background: 'rgba(0, 0, 0, 0.72)',
    border: '1px solid #00ffff',
    color: '#00ffff',
    padding: '0.35rem 0.5rem',
    fontFamily: 'monospace',
  },
  zoomOverlay: {
    position: 'absolute' as const,
    bottom: '0.6rem',
    right: '0.6rem',
    backgroundColor: 'rgba(0,0,0,0.7)',
    padding: '0.3rem 0.6rem',
    border: '1px solid #00ffff',
    color: '#00ffff',
    fontSize: '0.75rem',
    pointerEvents: 'none' as const,
  },
  systemPanel: {
    position: 'absolute' as const,
    top: '0.6rem',
    left: '0.6rem',
    minWidth: '220px',
    maxWidth: '320px',
    backgroundColor: 'rgba(8, 14, 32, 0.85)',
    border: '1px solid #44ee44',
    padding: '0.6rem 0.7rem',
    color: '#cfffd4',
    fontSize: '0.85rem',
    pointerEvents: 'auto' as const,
  },
  systemTitle: { fontWeight: 'bold' as const, color: '#88ff88', marginBottom: '0.25rem' },
  systemMeta: { color: '#aaaacc', marginBottom: '0.4rem', fontSize: '0.8rem' },
  planetList: { margin: '0.3rem 0', padding: '0 0 0 1rem', listStyle: 'disc' as const },
  actionRow: { display: 'flex', gap: '0.4rem', marginTop: '0.4rem', flexWrap: 'wrap' as const },
  warn: { color: '#ffaa66', fontSize: '0.75rem', marginTop: '0.4rem' },
  travelBox: { marginTop: '0.5rem', padding: '0.5rem', background: 'rgba(0,255,255,0.06)', border: '1px dashed rgba(0,255,255,0.4)', borderRadius: '4px' },
  travelTitle: { color: '#88ff88', margin: '0 0 0.3rem', fontSize: '0.8rem' },
  fleetOption: { display: 'flex', gap: '0.4rem', alignItems: 'flex-start', fontSize: '0.78rem', padding: '0.2rem 0', cursor: 'pointer' },
  travelMsg: { color: '#88ff88', fontSize: '0.75rem', marginTop: '0.35rem' },
  travelImpact: { color: '#ffeb66', fontSize: '0.74rem', margin: '0.4rem 0 0', lineHeight: 1.3 },
  error: {
    position: 'absolute' as const,
    top: '1rem',
    left: '50%',
    transform: 'translateX(-50%)',
    backgroundColor: 'rgba(255,0,0,0.8)',
    padding: '0.6rem 0.8rem',
    color: '#fff',
  },
  loading: {
    position: 'absolute' as const,
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    fontSize: '1.2rem',
    color: '#00ffff',
    textShadow: '0 0 10px #00ffff',
  },
}

const selectedInfo = computed(() => {
  const id = uiStore.selectedSystemId
  if (!id || !gameStore.galaxy) return null
  return (gameStore.galaxy.star_systems || []).find((s: any) => s.id === id) || null
})

const allSystems = computed<any[]>(() => gameStore.galaxy?.star_systems || [])
const playerFleets = computed<any[]>(() => gameStore.fleets || [])
const selectedFleetForTravel = computed(() => playerFleets.value.find((fleet) => fleet.id === chosenFleetId.value) || null)
const filteredSystems = computed(() => {
  const query = systemQuery.value.toLowerCase()
  if (!query) return allSystems.value
  return allSystems.value.filter((system) => String(system?.name || system?.id || '').toLowerCase().includes(query))
})
const hoverTooltipStyle = computed(() => ({
  position: 'absolute' as const,
  left: `${hoverPos.value.x + 14}px`,
  top: `${hoverPos.value.y + 14}px`,
  display: 'grid',
  gap: '0.15rem',
  background: 'rgba(3, 12, 24, 0.94)',
  border: '1px solid #00ffff',
  color: '#cfffd4',
  padding: '0.45rem 0.55rem',
  fontSize: '0.75rem',
  pointerEvents: 'none' as const,
  zIndex: 20,
  boxShadow: '0 8px 22px rgba(0, 0, 0, 0.55)',
}))
const travelPreview = computed(() => {
  const fleet = selectedFleetForTravel.value
  const target = selectedInfo.value
  if (!fleet || !target) return 'Selecciona una flota para ver el impacto.'
  return `${fleet.name} viajara de ${getSystemName(fleet.star_system_id)} a ${target.name}. Rango actual: ${rangeLabel.value}.`
})

/** Sistema donde el jugador tiene su capital (planeta colonizado) — fallback. */
const originSystemId = computed<string | null>(() => {
  const colonyHere = (gameStore.game?.player?.colonies || [])[0]
  return colonyHere?.star_system_id || null
})

/** Flotas del jugador que pueden alcanzar el sistema seleccionado. */
const travelableFleets = computed<any[]>(() => {
  const target = uiStore.selectedSystemId
  if (!target) return []
  const jumps = gameStore.maxJumps
  return playerFleets.value.filter((f) => {
    if (f.destination) return false
    if (f.star_system_id === target) return false
    const reach = reachableSystems(allSystems.value, f.star_system_id, jumps)
    return reach.has(target)
  })
})

const rangeLabel = computed(() => {
  const j = gameStore.maxJumps
  if (!Number.isFinite(j)) return 'rango ilimitado'
  return `${j} salto${j === 1 ? '' : 's'} max`
})

const cantTravelReason = computed(() => {
  if (!uiStore.selectedSystemId) return ''
  const target = uiStore.selectedSystemId
  
  const idle = playerFleets.value.filter(f => !f.destination)
  if (idle.length === 0) return 'No tienes flotas libres disponibles.'
  
  const notHere = idle.filter(f => f.star_system_id !== target)
  if (notHere.length === 0) return 'Tus flotas libres ya están en este sistema.'
  
  if (travelableFleets.value.length === 0) {
      return `Fuera de rango (${rangeLabel.value}).`
  }
  
  return ''
})

const canTravelHere = computed(() => {
  return cantTravelReason.value === ''
})

function getSystemName(id: string) {
  return allSystems.value.find((s) => s.id === id)?.name || id
}

function zoomIn() {
  zoom.value = Math.min(6, zoom.value * 1.18)
  requestRender()
}

function zoomOut() {
  zoom.value = Math.max(0.3, zoom.value / 1.18)
  requestRender()
}

function resetView() {
  zoom.value = 1
  panX.value = 0
  panY.value = 0
  requestRender()
}

function selectFirstMatch() {
  const match = filteredSystems.value[0]
  if (!match?.id) return
  uiStore.selectSystem(match.id)
  systemQuery.value = match.name || match.id
  requestRender()
}

function launchTravel() {
  if (!chosenFleetId.value || !uiStore.selectedSystemId) return
  confirmTravelOpen.value = true
}

async function confirmLaunchTravel() {
  if (!chosenFleetId.value || !uiStore.selectedSystemId || !gameStore.gameId) return
  launching.value = true
  travelMessage.value = ''
  try {
    await api.fleet.move(gameStore.gameId, chosenFleetId.value, uiStore.selectedSystemId)
    travelMessage.value = `Flota ${chosenFleetId.value} en transito`
    chosenFleetId.value = ''
    travelMode.value = false
    confirmTravelOpen.value = false
    await gameStore.fetchFleets()
    requestRender()
  } catch (err: any) {
    travelMessage.value = err?.message || 'No se pudo iniciar el viaje'
  } finally {
    launching.value = false
  }
}

watch(() => uiStore.selectedSystemId, () => {
  travelMode.value = false
  chosenFleetId.value = ''
  travelMessage.value = ''
  confirmTravelOpen.value = false
})

const handleMouseDown = (e: MouseEvent) => {
  if (e.button === 0 || e.button === 1) {
    isDragging.value = true
    wasDragging.value = false
    lastMouseX.value = e.clientX
    lastMouseY.value = e.clientY
  }
}

const handleMouseMove = (e: MouseEvent) => {
  if (isDragging.value) {
    const dx = e.clientX - lastMouseX.value
    const dy = e.clientY - lastMouseY.value
    if (Math.abs(dx) > 2 || Math.abs(dy) > 2) wasDragging.value = true
    panX.value += dx
    panY.value += dy
    lastMouseX.value = e.clientX
    lastMouseY.value = e.clientY
    requestRender()
    hoveredInfo.value = null
    return
  }
  const canvas = canvasRef.value
  if (!canvas) return
  const rect = canvas.getBoundingClientRect()
  hoverPos.value = { x: e.clientX - rect.left, y: e.clientY - rect.top }
  hoveredInfo.value = findSystemAt(hoverPos.value.x, hoverPos.value.y, 18)
}

const handleMouseUp = () => {
  isDragging.value = false
}

function findSystemAt(cx: number, cy: number, radius = 14) {
  const canvas = canvasRef.value
  if (!canvas || !gameStore.galaxy) return null
  const w = canvas.width
  const h = canvas.height
  const padX = 40
  const padY = 40
  const drawW = w - padX * 2
  const drawH = h - padY * 2

  let nearest: any = null
  let bestDist = radius * radius
  for (const sys of gameStore.galaxy.star_systems || []) {
    if (!sys?.position) continue
    const sx = padX + (sys.position.x / 100) * drawW
    const sy = padY + (sys.position.y / 100) * drawH
    const zx = (sx - w / 2) * zoom.value + w / 2 + panX.value
    const zy = (sy - h / 2) * zoom.value + h / 2 + panY.value
    const dx = zx - cx
    const dy = zy - cy
    const dist = dx * dx + dy * dy
    if (dist < bestDist) {
      bestDist = dist
      nearest = sys
    }
  }
  return nearest
}

const handleClick = (e: MouseEvent) => {
  if (wasDragging.value) {
    wasDragging.value = false
    return
  }
  const canvas = canvasRef.value
  if (!canvas || !gameStore.galaxy) return
  const rect = canvas.getBoundingClientRect()
  const cx = e.clientX - rect.left
  const cy = e.clientY - rect.top
  const nearest = findSystemAt(cx, cy)
  if (nearest) {
    uiStore.selectSystem(nearest.id)
    requestRender()
  }
}

const handleWheel = (e: WheelEvent) => {
  const delta = e.deltaY > 0 ? 0.9 : 1.1
  zoom.value = Math.max(0.3, Math.min(6, zoom.value * delta))
  requestRender()
}

const requestRender = () => {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  renderGalaxy(
    ctx,
    gameStore.galaxy,
    canvas.width,
    canvas.height,
    uiStore.selectedSystemId,
    gameStore.fleets,
    zoom.value,
    panX.value,
    panY.value,
  )
}

const resize = () => {
  if (containerRef.value && canvasRef.value) {
    canvasRef.value.width = containerRef.value.clientWidth
    canvasRef.value.height = containerRef.value.clientHeight
    requestRender()
  }
}

const goToSystem = () => {
  const id = uiStore.selectedSystemId
  const gameId = String(route.params.id || gameStore.gameId || '')
  if (id && gameId) router.push(`/game/${gameId}/system/${id}`)
}

onMounted(async () => {
  window.addEventListener('resize', resize)
  resize()
  if (!gameStore.galaxy) {
    loading.value = true
    try {
      await gameStore.fetchGalaxy()
    } catch (err) {
      error.value = (err as Error).message || 'No se pudo cargar la galaxia.'
    } finally {
      loading.value = false
    }
  }
  if (!gameStore.fleets?.length) {
    try {
      await gameStore.fetchFleets()
    } catch {
      /* ignore */
    }
  }
  requestRender()
})

onUnmounted(() => {
  window.removeEventListener('resize', resize)
})

watch(() => gameStore.galaxy, requestRender, { deep: true })
watch(() => gameStore.fleets, requestRender, { deep: true })
watch(() => uiStore.selectedSystemId, requestRender)
</script>

<style scoped>
.map-btn {
  padding: 0.35rem 0.55rem;
  font-size: 0.58rem;
}

.map-modal {
  position: absolute;
  inset: 0;
  z-index: 40;
  display: grid;
  place-items: center;
  background: rgba(0, 0, 0, 0.62);
}

.map-modal-card {
  width: min(92%, 460px);
  padding: 0.85rem;
  border: 1px solid #00ffff;
  background: rgba(4, 8, 26, 0.96);
  color: #cfffd4;
  box-shadow: 0 0 28px rgba(0, 255, 255, 0.24);
}

.map-modal-card header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px dashed rgba(0, 255, 255, 0.35);
  padding-bottom: 0.45rem;
  margin-bottom: 0.55rem;
}

.map-modal-card header button {
  background: transparent;
  border: 1px solid #ff5577;
  color: #ff5577;
  cursor: pointer;
}

.map-modal-card p {
  margin: 0 0 0.5rem;
  color: #ffeb66;
}

.map-modal-card ul {
  margin: 0 0 0.8rem;
  padding-left: 1.1rem;
  color: #aaaacc;
}

.map-modal-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
  flex-wrap: wrap;
}
</style>
