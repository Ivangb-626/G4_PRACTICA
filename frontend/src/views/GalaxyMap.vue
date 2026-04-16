<template>
  <div class="galaxy-map-container" @keydown.prevent="handleKeydown" tabindex="0" ref="mapContainer">
    <div class="hud">
      <div>
        <h2>Galaxy Map</h2>
        <p>Turno: {{ gameData?.turn || '—' }} · Posición actual: {{ currentLocationName }}</p>
      </div>
      <div class="actions">
        <button @click="focusPlayerPosition" class="btn sci-fi">Ir a mi posición</button>
        <button @click="endTurn" class="btn sci-fi">End Turn (T)</button>
        <button @click="saveGame" class="btn sci-fi">Save Game (F10)</button>
      </div>
    </div>

    <div class="legend retro-panel" v-if="gameData">
      <span><i class="dot mine"></i> Tu colonia</span>
      <span><i class="dot fleet"></i> Tu flota</span>
      <span><i class="dot selected"></i> Sistema seleccionado</span>
    </div>

    <div class="map-view" v-if="gameData">
      <div class="map-frame">
        <svg class="connections" width="100%" height="100%">
          <g v-for="conn in connections" :key="conn.id">
            <line :x1="conn.x1+'%'" :y1="conn.y1+'%'" :x2="conn.x2+'%'" :y2="conn.y2+'%'" stroke="rgba(0,212,255,0.2)" stroke-width="1.5" />
          </g>
        </svg>

        <div v-for="system in gameData.systems" :key="system.id"
             class="star-system"
             :class="{ 'is-selected': selectedSystemId === system.id }"
             :style="{ left: system.x + '%', top: system.y + '%' }"
             @click="openSystem(system.id)">
          <div class="star-icon"
               :class="[system.star_type, { 'is-mine': system.has_player_colony, 'has-fleet': system.has_player_fleet }]"></div>
          <span class="system-name">{{ system.name }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../services/api'
import type { GameState } from '../types/game'

const route = useRoute()
const router = useRouter()
const gameId = route.params.id as string

const gameData = ref<GameState | null>(null)
const mapContainer = ref<HTMLElement | null>(null)

type GalaxySystem = {
  id: string
  name: string
  x: number
  y: number
  star_type: string
  neighbors: string[]
  has_player_colony?: boolean
  has_player_fleet?: boolean
}

function normalizeGalaxy(raw: any): GameState {
  const stars = Array.isArray(raw?.star_systems) ? raw.star_systems : []
  const systems: GalaxySystem[] = stars.map((s: any) => ({
    id: s.id,
    name: s.name,
    x: Math.min(98, Math.max(2, s?.position?.x ?? 0)),
    y: Math.min(96, Math.max(4, s?.position?.y ?? 0)),
    star_type: s.star_type || 'yellow',
    neighbors: Array.isArray(s.connections) ? s.connections : [],
    has_player_colony: Boolean(s.has_player_colony),
    has_player_fleet: Boolean(s.has_player_fleet)
  }))
  return {
    id: gameId,
    name: 'Galaxy',
    turn: 0,
    systems,
    fleets: [],
    players: []
  }
}

const connections = computed(() => {
  if (!gameData.value) return []
  const conns = []
  const systemsMap = new Map(gameData.value.systems.map(s => [s.id, s]))
  
  for (const system of gameData.value.systems) {
    if (system.neighbors) {
      for (const neighborId of system.neighbors) {
        const neighbor = systemsMap.get(neighborId)
        if (neighbor) {
          conns.push({
            id: `${system.id}-${neighbor.id}`,
            x1: system.x, y1: system.y,
            x2: neighbor.x, y2: neighbor.y
          })
        }
      }
    }
  }
  return conns
})

const selectedSystemId = ref<string>('')
const playerSystems = computed(() =>
  (gameData.value?.systems || []).filter((s: any) => s.has_player_colony || s.has_player_fleet)
)
const currentLocationName = computed(() => {
  const selected = gameData.value?.systems.find((s) => s.id === selectedSystemId.value)
  if (selected) return selected.name
  return playerSystems.value[0]?.name || 'Sin datos'
})

const fetchGalaxy = async () => {
  try {
    const res = await api.getGalaxy(gameId)
    gameData.value = normalizeGalaxy(res?.state || res)
    if (!selectedSystemId.value) {
      selectedSystemId.value = playerSystems.value[0]?.id || gameData.value.systems[0]?.id || ''
    }
  } catch (error) {
    console.error('Failed to load galaxy', error)
  }
}

const selectSystem = (sysId: string) => {
  selectedSystemId.value = sysId
}

const openSystem = (sysId: string) => {
  selectSystem(sysId)
  goToSystem(sysId)
}

const goToSystem = (sysId: string) => {
  router.push(`/game/${gameId}/system/${sysId}`)
}

const focusPlayerPosition = () => {
  if (playerSystems.value[0]?.id) {
    selectedSystemId.value = playerSystems.value[0].id
  }
}

const endTurn = async () => {
  try {
    await api.endTurn(gameId)
    await fetchGalaxy()
  } catch(error) {
    console.error(error)
  }
}

const saveGame = async () => {
  try {
    await api.saveGame(gameId)
    alert('Game saved!')
  } catch (error) {
    console.error(error)
  }
}

const handleKeydown = (e: KeyboardEvent) => {
  const t = e.target as HTMLElement
  if (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA') return

  switch (e.key.toLowerCase()) {
    case 't':
      endTurn()
      break
    case 'enter':
      if (selectedSystemId.value) goToSystem(selectedSystemId.value)
      break
    case 'f10':
      saveGame()
      break
    // Añadir atajos extra C, F, P...
  }
}

onMounted(() => {
  fetchGalaxy()
  mapContainer.value?.focus()
})
</script>

<style scoped>
.galaxy-map-container {
  position: relative;
  display: flex;
  flex-direction: column;
  width: 100%;
  height: clamp(640px, 84vh, 980px);
  background: #0a0a1a url('/assets/stars-bg.png') repeat;
  color: #fff;
  outline: none;
  border: 1px solid var(--panel-border);
  border-radius: 10px;
  overflow: hidden;
}
.hud {
  position: relative;
  width: 100%;
  padding: 0.7rem 0.9rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.6rem;
  flex-wrap: wrap;
  background: rgba(0,0,0,0.7);
  border-bottom: 1px solid #00d4ff;
  z-index: 10;
}
.btn.sci-fi {
  background: #1a1a3e;
  border: 1px solid #00d4ff;
  color: #00d4ff;
  padding: 0.5rem 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-left: 0.5rem;
}
.btn.sci-fi:hover {
  background: #00d4ff;
  color: #0a0a1a;
  box-shadow: 0 0 10px #00d4ff;
}
.legend {
  margin: 0.45rem 0.7rem 0;
  width: auto;
  display: flex;
  gap: 1rem;
  align-items: center;
  padding: 0.4rem 0.7rem;
  font-size: 0.78rem;
  flex-wrap: wrap;
}
.dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-right: 0.35rem;
}
.dot.mine { background: #6ef7b2; box-shadow: 0 0 8px #6ef7b2; }
.dot.fleet { background: #67e8f9; box-shadow: 0 0 8px #67e8f9; }
.dot.selected { background: #ffd700; box-shadow: 0 0 8px #ffd700; }
.map-view {
  display: grid;
  place-items: center;
  width: 100%;
  flex: 1;
  min-height: 0;
  padding: 0.55rem 0.7rem 0.7rem;
}
.map-frame {
  position: relative;
  width: 100%;
  height: 100%;
  border: 1px solid rgba(89, 170, 255, 0.5);
  border-radius: 10px;
  background: rgba(4, 10, 24, 0.65);
  overflow: hidden;
}
.connections {
  position: absolute;
  top: 0; left: 0;
  pointer-events: none;
}
.star-system {
  position: absolute;
  transform: translate(-50%, -50%);
  cursor: pointer;
  text-align: center;
  z-index: 5;
}
.star-system.is-selected .system-name {
  color: #ffe082;
}
.star-icon {
  position: relative;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: white;
  margin: 0 auto;
  box-shadow: 0 0 12px white;
  transition: transform 0.2s;
}
.star-system:hover .star-icon {
  transform: scale(1.35);
}
.star-icon.is-mine {
  outline: 2px solid #6ef7b2;
  outline-offset: 2px;
}
.star-icon.has-fleet::after {
  content: '';
  position: absolute;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #67e8f9;
  transform: translate(13px, -2px);
  box-shadow: 0 0 8px #67e8f9;
}
.system-name {
  font-family: monospace;
  font-size: 0.72rem;
  text-shadow: 0 0 5px black;
}
/* Tipos de estrellas */
.red { background: #ff3366; box-shadow: 0 0 15px #ff3366; }
.blue { background: #00d4ff; box-shadow: 0 0 15px #00d4ff; }
.yellow { background: #ffd700; box-shadow: 0 0 15px #ffd700; }
</style>
