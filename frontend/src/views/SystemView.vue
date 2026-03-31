<template>
  <div class="system-view" v-if="system">
    <div class="hud">
      <h2>System: {{ system.name }}</h2>
      <button @click="backToGalaxy" class="btn sci-fi">Back to Galaxy</button>
    </div>
    
    <div class="solar-system">
      <div class="sun" :class="system.star_type"></div>
      
      <div v-for="(planet, index) in system.planets" :key="index" class="orbit" :style="{ width: `${200 + index * 100}px`, height: `${200 + index * 100}px` }">
        <div class="planet" :class="planet.type" @click="handlePlanetClick(planet)">
          <div class="planet-info" v-if="hoverPlanet === index">
            {{ planet.type }} - Size: {{ planet.size }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../services/api'
import type { StarSystem, Planet } from '../types/game'

const route = useRoute()
const router = useRouter()
const gameId = route.params.id as string
const sysId = route.params.sysId as string

const system = ref<StarSystem | null>(null)
const hoverPlanet = ref<number | null>(null)

const fetchSystem = async () => {
  try {
    const res = await api.getGalaxy(gameId) // O un endpoint específico
    const sys = (res.state || res).systems.find((s: any) => s.id === sysId)
    if (sys) system.value = sys
  } catch (error) {
    console.error(error)
  }
}

const backToGalaxy = () => {
  router.push(`/game/${gameId}/galaxy`)
}

const handlePlanetClick = (planet: Planet) => {
  if (planet.colony) {
    router.push(`/game/${gameId}/colony/${planet.colony.id}`)
  } else {
    alert('Planet is not colonized. Future: Implement colonization dialog.')
  }
}

onMounted(() => {
  fetchSystem()
})
</script>

<style scoped>
.system-view {
  width: 100vw;
  height: 100vh;
  background: #0a0a1a;
  color: white;
  position: relative;
  overflow: hidden;
}
.hud {
  position: absolute;
  top: 0; left: 0; right: 0;
  padding: 1rem;
  display: flex;
  justify-content: space-between;
  background: rgba(0,0,0,0.5);
  z-index: 10;
}
.solar-system {
  position: absolute;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  align-items: center;
  justify-content: center;
}
.sun {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: yellow;
  box-shadow: 0 0 50px yellow;
  z-index: 5;
}
.orbit {
  position: absolute;
  border: 1px dashed rgba(255,255,255,0.2);
  border-radius: 50%;
  animation: spin 20s linear infinite;
}
.planet {
  width: 20px;
  height: 20px;
  background: cyan;
  border-radius: 50%;
  position: absolute;
  top: 0; left: 50%;
  transform: translate(-50%, -50%);
  cursor: pointer;
}
.btn.sci-fi {
  background: transparent;
  border: 1px solid #00d4ff;
  color: #00d4ff;
  padding: 0.5rem 1rem;
  cursor: pointer;
}
.btn.sci-fi:hover {
  background: #00d4ff;
  color: #0a0a1a;
}
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
