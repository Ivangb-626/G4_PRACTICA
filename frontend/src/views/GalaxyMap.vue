<template>
  <div class="galaxy-map-container" @keydown.prevent="handleKeydown" tabindex="0" ref="mapContainer">
    <div class="hud">
      <h2>Galaxy Map</h2>
      <p>Turn: {{ gameData?.turn }}</p>
      <div class="actions">
        <button @click="endTurn" class="btn sci-fi">End Turn (T)</button>
        <button @click="saveGame" class="btn sci-fi">Save Game (F10)</button>
      </div>
    </div>
    
    <div class="map-view" v-if="gameData">
      <svg class="connections" width="100%" height="100%">
        <g v-for="conn in connections" :key="conn.id">
          <line :x1="conn.x1+'%'" :y1="conn.y1+'%'" :x2="conn.x2+'%'" :y2="conn.y2+'%'" stroke="rgba(0,212,255,0.2)" stroke-width="2" />
        </g>
      </svg>
      
      <div v-for="system in gameData.systems" :key="system.id" 
           class="star-system"
           :style="{ left: system.x + '%', top: system.y + '%' }"
           @click="goToSystem(system.id)">
        <div class="star-icon" :class="system.star_type"></div>
        <span class="system-name">{{ system.name }}</span>
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

const fetchGalaxy = async () => {
  try {
    const res = await api.getGalaxy(gameId)
    // Asumimos que la API devuelve algo que tiene las propiedades o el game object completo
    gameData.value = res.state || res
  } catch (error) {
    console.error('Failed to load galaxy', error)
  }
}

const goToSystem = (sysId: string) => {
  router.push(`/game/${gameId}/system/${sysId}`)
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
  width: 100vw;
  height: 100vh;
  background: #0a0a1a url('/assets/stars-bg.png') repeat;
  color: #fff;
  outline: none;
}
.hud {
  position: absolute;
  top: 0; left: 0;
  width: 100%;
  padding: 1rem;
  display: flex;
  justify-content: space-between;
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
.map-view {
  position: relative;
  width: 100%;
  height: 100%;
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
.star-icon {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: white;
  margin: 0 auto;
  box-shadow: 0 0 15px white;
  transition: transform 0.2s;
}
.star-system:hover .star-icon {
  transform: scale(1.5);
}
.system-name {
  font-family: monospace;
  font-size: 0.8rem;
  text-shadow: 0 0 5px black;
}
/* Tipos de estrellas */
.red { background: #ff3366; box-shadow: 0 0 15px #ff3366; }
.blue { background: #00d4ff; box-shadow: 0 0 15px #00d4ff; }
.yellow { background: #ffd700; box-shadow: 0 0 15px #ffd700; }
</style>
