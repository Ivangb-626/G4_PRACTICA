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
      <p v-if="!canTravelHere && selectedInfo.id !== originSystemId" :style="styles.warn">
        Fuera de rango ({{ gameStore.maxJumps }} saltos max).
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
          {{ launching ? 'EN MARCHA...' : 'INICIAR VIAJE' }}
        </button>
        <p v-if="travelMessage" :style="styles.travelMsg">{{ travelMessage }}</p>
      </div>
    </div>

    <!-- Zoom indicator (overrides parent zoom indicator visually) -->
    <div :style="styles.zoomOverlay">
      ZOOM: {{ Math.round(zoom * 100) }}%
    </div>

    <div v-if="error" :style="styles.error">{{ error }}</div>
    <div v-if="loading" :style="styles.loading">SCANNING SECTOR...</div>
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
    const reach = reachableSystems(allSystems.value, f.star_system_id, jumps)
    return reach.has(target)
  })
})

const canTravelHere = computed(() => {
  if (!uiStore.selectedSystemId) return false
  if (uiStore.selectedSystemId === originSystemId.value) return false
  return travelableFleets.value.length > 0
})

function getSystemName(id: string) {
  return allSystems.value.find((s) => s.id === id)?.name || id
}

async function launchTravel() {
  if (!chosenFleetId.value || !uiStore.selectedSystemId || !gameStore.gameId) return
  launching.value = true
  travelMessage.value = ''
  try {
    await api.fleet.move(gameStore.gameId, chosenFleetId.value, uiStore.selectedSystemId)
    travelMessage.value = `Flota ${chosenFleetId.value} en transito`
    chosenFleetId.value = ''
    travelMode.value = false
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
  }
}

const handleMouseUp = () => {
  isDragging.value = false
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

  const w = canvas.width
  const h = canvas.height
  const padX = 40
  const padY = 40
  const drawW = w - padX * 2
  const drawH = h - padY * 2

  const systems = gameStore.galaxy.star_systems || []
  let nearest: any = null
  let bestDist = 14 * 14

  for (const sys of systems) {
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
