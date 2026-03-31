<template>
  <div class="colony-view" v-if="colony">
    <div class="hud">
      <h2>Colony Management</h2>
      <button @click="backToSystem" class="btn sci-fi">Back to System</button>
    </div>

    <div class="panels">
      <div class="panel">
        <h3>Population ({{ totalPop }})</h3>
        <div class="slider-group">
          <label>Farmers: {{ colony.population_farmers }}</label>
          <input type="range" v-model.number="colony.population_farmers" :max="totalPop" @input="balancePopulation('farmers')" />
        </div>
        <div class="slider-group">
          <label>Workers: {{ colony.population_workers }}</label>
          <input type="range" v-model.number="colony.population_workers" :max="totalPop" @input="balancePopulation('workers')" />
        </div>
        <div class="slider-group">
          <label>Scientists: {{ colony.population_scientists }}</label>
          <input type="range" v-model.number="colony.population_scientists" :max="totalPop" @input="balancePopulation('scientists')" />
        </div>
        <button @click="applyChanges" class="btn sci-fi">Apply Changes</button>
      </div>

      <div class="panel">
        <h3>Buildings</h3>
        <ul>
          <li v-for="b in colony.buildings" :key="b">{{ b }}</li>
        </ul>
      </div>

      <div class="panel">
        <h3>Build Queue</h3>
        <ul>
          <li v-for="(item, index) in colony.build_queue" :key="index">{{ item }}</li>
        </ul>
        <button @click="addToQueue('automated_factory')" class="btn sci-fi">Build Factory</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../services/api'
import type { Colony } from '../types/game'

const route = useRoute()
const router = useRouter()
const gameId = route.params.id as string
const colId = route.params.colId as string

const colony = ref<Colony | null>(null)

const fetchColony = async () => {
  try {
    const res = await api.getColony(gameId, colId)
    colony.value = res.colony || res
  } catch (error) {
    console.error(error)
  }
}

const totalPop = computed(() => colony.value?.population || 0)

const balancePopulation = (changed: 'farmers' | 'workers' | 'scientists') => {
  if (!colony.value) return
  const sum = colony.value.population_farmers + colony.value.population_workers + colony.value.population_scientists
  if (sum > totalPop.value) {
    // Basic logic to prevent exceeding total
    if (changed !== 'farmers') colony.value.population_farmers = Math.max(0, colony.value.population_farmers - (sum - totalPop.value))
    else if (changed !== 'workers') colony.value.population_workers = Math.max(0, colony.value.population_workers - (sum - totalPop.value))
    else colony.value.population_scientists = Math.max(0, colony.value.population_scientists - (sum - totalPop.value))
  }
}

const applyChanges = async () => {
  if (!colony.value) return
  try {
    await api.manageColony(gameId, colId, {
      population_allocation: {
        farmers: colony.value.population_farmers,
        workers: colony.value.population_workers,
        scientists: colony.value.population_scientists
      }
    })
    alert('Population changes applied!')
  } catch (err) {
    console.error(err)
  }
}

const addToQueue = async (item: string) => {
  // Aquí se invocaría el API real para construir. De momento mock local:
  if(colony.value) colony.value.build_queue.push(item)
}

const backToSystem = () => {
  if(colony.value) router.push(`/game/${gameId}/system/${colony.value.system_id}`)
  else router.push(`/game/${gameId}/galaxy`)
}

onMounted(() => {
  fetchColony()
})
</script>

<style scoped>
.colony-view {
  width: 100vw;
  height: 100vh;
  background: #0a0a1a;
  color: white;
  padding: 2rem;
  box-sizing: border-box;
}
.hud {
  display: flex;
  justify-content: space-between;
  margin-bottom: 2rem;
}
.panels {
  display: flex;
  gap: 2rem;
}
.panel {
  background: rgba(26, 26, 62, 0.8);
  border: 1px solid #00d4ff;
  border-radius: 8px;
  padding: 1rem;
  flex: 1;
}
.slider-group {
  margin-bottom: 1rem;
}
.slider-group label {
  display: block;
  margin-bottom: 0.5rem;
}
.btn.sci-fi {
  background: transparent;
  border: 1px solid #00d4ff;
  color: #00d4ff;
  padding: 0.5rem 1rem;
  cursor: pointer;
  margin-top: 1rem;
}
.btn.sci-fi:hover {
  background: #00d4ff;
  color: #0a0a1a;
}
</style>
