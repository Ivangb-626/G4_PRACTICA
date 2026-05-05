<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '../store/authStore'
import { httpClient as api } from '../types/httpClient'
import BaseButton from './BaseButton.vue'
import ErrorAlert from './ErrorAlert.vue'

const route = useRoute()
const authStore = useAuthStore()
const gameId = route.params.id as string

interface Spy {
  id: string;
  name: string;
  skill: number;
  status: string;
  mission: string | null;
  assigned_to: string | null;
}

const spies = ref<Spy[]>([])
const error = ref('')
const loading = ref(false)

const missionTypes = ['sabotage', 'steal_tech', 'assassinate', 'incite_revolt']
const selectedSpyId = ref<string | null>(null)
const selectedMission = ref(missionTypes[0])
const targetPlayer = ref('')

const fetchSpies = async () => {
  try {
    loading.value = true
    const res = await api.get(`/api/game/${gameId}/espionage`, {
      headers: { Authorization: `Bearer ${authStore.token}` }
    })
    spies.value = res.data.spies || []
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Failed to fetch spies'
  } finally {
    loading.value = false
  }
}

const recruitSpy = async () => {
  try {
    loading.value = true
    await api.post(`/api/game/${gameId}/espionage/recruit`, {}, {
      headers: { Authorization: `Bearer ${authStore.token}` }
    })
    await fetchSpies()
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Failed to recruit spy. Ensure you have 50 BC.'
  } finally {
    loading.value = false
  }
}

const assignMission = async () => {
  if (!selectedSpyId.value || !targetPlayer.value) {
    error.value = 'Please select a spy and a target player.'
    return
  }
  
  try {
    loading.value = true
    await api.post(`/api/game/${gameId}/espionage/mission`, {
      spy_id: selectedSpyId.value,
      target_id: targetPlayer.value,
      mission_type: selectedMission.value
    }, {
      headers: { Authorization: `Bearer ${authStore.token}` }
    })
    await fetchSpies()
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Failed to assign mission.'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchSpies()
})
</script>

<template>
  <div class="espionage-view p-6 bg-gray-900 text-white min-h-screen">
    <h2 class="text-3xl text-cyan-400 mb-6 font-bold border-b border-cyan-800 pb-2">Intelligence Network</h2>
    
    <ErrorAlert v-if="error" :message="error" @close="error = ''" class="mb-4" />

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <!-- Roster panel -->
      <div class="panel bg-gray-800 rounded-lg p-6 border border-gray-700">
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-xl font-semibold text-gray-200">Active Agents</h3>
          <BaseButton @click="recruitSpy" :disabled="loading" variant="primary">
            Recruit Agent (50 BC)
          </BaseButton>
        </div>

        <div v-if="loading && spies.length === 0" class="text-center py-4">Loading agents...</div>
        
        <div v-else-if="spies.length === 0" class="text-gray-500 text-center py-4">
          No spies recruited yet. Hire an agent to begin espionage operations.
        </div>
        
        <div v-else class="space-y-3 max-h-[500px] overflow-y-auto pr-2 custom-scrollbar">
          <div 
            v-for="spy in spies" 
            :key="spy.id"
            @click="selectedSpyId = spy.id"
            :class="['spy-card p-4 rounded border cursor-pointer transition-colors', selectedSpyId === spy.id ? 'border-cyan-500 bg-gray-700' : 'border-gray-600 bg-gray-800 hover:border-gray-500']"
          >
            <div class="flex justify-between">
              <span class="font-bold text-lg">{{ spy.name }}</span>
              <span class="text-cyan-400">Skill: {{ spy.skill }}</span>
            </div>
            <div class="mt-2 text-sm">
              <span v-if="spy.status === 'idle'" class="text-green-400">● Idle</span>
              <span v-else class="text-yellow-400">
                ● On Mission ({{ spy.mission }}) against {{ spy.assigned_to }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Command panel -->
      <div class="panel bg-gray-800 rounded-lg p-6 border border-gray-700 opacity-90">
        <h3 class="text-xl font-semibold text-gray-200 mb-6">Mission Command</h3>
        
        <div v-if="!selectedSpyId" class="text-gray-500 italic mb-4">
          Select an agent from your roster to assign a mission.
        </div>
        
        <div v-else class="space-y-6">
          <div>
            <label class="block text-gray-400 mb-2">Target Empire ID:</label>
            <input 
              v-model="targetPlayer" 
              type="text" 
              placeholder="e.g., ai_0" 
              class="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-white focus:outline-none focus:border-cyan-500"
            />
          </div>
          
          <div>
            <label class="block text-gray-400 mb-2">Operation Type:</label>
            <select 
              v-model="selectedMission"
              class="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-white focus:outline-none focus:border-cyan-500 capitalize"
            >
              <option v-for="m in missionTypes" :key="m" :value="m">{{ m.replace('_', ' ') }}</option>
            </select>
          </div>
          
          <BaseButton 
            @click="assignMission" 
            :disabled="loading || !targetPlayer" 
            variant="danger" 
            class="w-full mt-4"
          >
            Initiate Operation
          </BaseButton>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: #1f2937;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #4b5563;
  border-radius: 3px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #6b7280;
}
</style>
