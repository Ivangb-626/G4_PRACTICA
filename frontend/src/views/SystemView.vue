<template>
  <div class="system-view" v-if="system">
    <div class="hud">
      <div>
        <h2>System: {{ system.name }}</h2>
        <p class="subtitle">Haz click en un planeta colonizado para abrir su colonia.</p>
      </div>
      <button @click="backToGalaxy" class="btn sci-fi">Back to Galaxy</button>
    </div>

    <div class="legend retro-panel">
      <span><i class="dot colonized"></i> Colonizado por jugador</span>
      <span><i class="dot free"></i> No colonizado</span>
    </div>

    <div class="system-stage">
      <div class="solar-system">
        <div class="sun" :class="system.star_type"></div>

        <div
          v-for="(planet, index) in system.planets"
          :key="index"
          class="orbit"
          :style="{ width: `${220 + index * 110}px`, height: `${220 + index * 110}px` }"
        >
          <div
            class="planet"
            :class="[planet.type, { colonized: planet.colonized_by === 'player' }]"
            @mouseenter="hoverPlanet = index"
            @mouseleave="hoverPlanet = null"
            @click="handlePlanetClick(planet)"
          >
            <div class="planet-info" v-if="hoverPlanet === index">
              {{ planet.name || `Planeta ${planet.index}` }} · {{ planet.type }} · {{ planet.size }}
            </div>
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
    const res = await api.getGalaxy(gameId)
    const stars = Array.isArray(res?.star_systems) ? res.star_systems : []
    const sys = stars.find((s: any) => s.id === sysId)
    if (sys) {
      system.value = {
        id: sys.id,
        name: sys.name,
        x: sys?.position?.x ?? 0,
        y: sys?.position?.y ?? 0,
        star_type: sys.star_type,
        planets: sys.planets || [],
        neighbors: sys.connections || [],
        owner: undefined
      }
    }
  } catch (error) {
    console.error(error)
  }
}

const backToGalaxy = () => {
  router.push(`/game/${gameId}/galaxy`)
}

const handlePlanetClick = (planet: Planet) => {
  const colonyId = `col_${sysId}_${planet.index}`
  if (planet.colonized_by === 'player') {
    router.push(`/game/${gameId}/colony/${colonyId}`)
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
  display: flex;
  flex-direction: column;
  width: 100%;
  height: clamp(640px, 84vh, 980px);
  background: #0a0a1a;
  color: white;
  position: relative;
  border: 1px solid var(--panel-border);
  border-radius: 10px;
  overflow: hidden;
}
.hud {
  position: relative;
  padding: 0.7rem 0.9rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.8rem;
  flex-wrap: wrap;
  background: rgba(0,0,0,0.5);
  border-bottom: 1px solid #00d4ff;
}
.subtitle {
  margin: 0.2rem 0 0;
  color: var(--text-muted);
  font-size: 0.8rem;
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
.dot.colonized { background: #6ef7b2; box-shadow: 0 0 8px #6ef7b2; }
.dot.free { background: #67e8f9; box-shadow: 0 0 8px #67e8f9; }
.system-stage {
  flex: 1;
  min-height: 0;
  display: grid;
  place-items: center;
  padding: 0.55rem 0.7rem 0.7rem;
}
.solar-system {
  position: relative;
  width: 100%;
  height: 100%;
  border: 1px solid rgba(89, 170, 255, 0.5);
  border-radius: 10px;
  background: rgba(4, 10, 24, 0.65);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.sun {
  width: 96px;
  height: 96px;
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
  width: 18px;
  height: 18px;
  background: cyan;
  border-radius: 50%;
  position: absolute;
  top: 0; left: 50%;
  transform: translate(-50%, -50%);
  cursor: pointer;
  box-shadow: 0 0 10px rgba(103, 232, 249, 0.8);
}
.planet.colonized {
  outline: 2px solid #6ef7b2;
  outline-offset: 2px;
}
.planet-info {
  position: absolute;
  top: -28px;
  left: 50%;
  transform: translateX(-50%);
  white-space: nowrap;
  font-size: 0.72rem;
  background: rgba(7, 15, 36, 0.9);
  border: 1px solid rgba(112, 166, 214, 0.65);
  border-radius: 6px;
  padding: 0.2rem 0.45rem;
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
