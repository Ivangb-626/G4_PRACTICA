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

interface Leader {
  id: string;
  uid?: string;
  name: string;
  title: string;
  type: string;
  description: string;
  bonuses: Record<string, number>;
  hire_cost: number;
  upkeep: number;
  assigned_to?: string | null;
}

const hiredLeaders = ref<Leader[]>([])
const availableLeaders = ref<Leader[]>([])
const error = ref('')
const loading = ref(false)

const fetchLeaders = async () => {
  try {
    loading.value = true
    const [hiredRes, availableRes] = await Promise.all([
      api.get(`/api/game/${gameId}/leaders`, { headers: { Authorization: `Bearer ${authStore.token}` } }),
      api.get(`/api/game/${gameId}/leaders/available`, { headers: { Authorization: `Bearer ${authStore.token}` } })
    ])
    hiredLeaders.value = hiredRes.data.leaders || []
    availableLeaders.value = availableRes.data.available_leaders || []
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Failed to load leaders'
  } finally {
    loading.value = false
  }
}

const hireLeader = async (templateId: string) => {
  try {
    loading.value = true
    await api.post(`/api/game/${gameId}/leaders/hire`, { leader_template_id: templateId }, {
      headers: { Authorization: `Bearer ${authStore.token}` }
    })
    await fetchLeaders()
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Failed to hire leader. Ensure enough BC.'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchLeaders()
})
</script>

<template>
  <div class="leaders-view p-6 bg-gray-900 text-white min-h-screen">
    <h2 class="text-3xl text-cyan-400 mb-6 font-bold border-b border-cyan-800 pb-2">Leadership Administration</h2>
    
    <ErrorAlert v-if="error" :message="error" @close="error = ''" class="mb-4" />

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <!-- Available Leaders -->
      <div class="panel bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h3 class="text-xl font-semibold text-gray-200 mb-4">Available for Hire</h3>
        
        <div v-if="loading && availableLeaders.length === 0" class="text-center py-4">Loading market...</div>
        <div v-else-if="availableLeaders.length === 0" class="text-gray-500 text-center py-4">No candidates available.</div>
        
        <div v-else class="space-y-4 max-h-[500px] overflow-y-auto pr-2 custom-scrollbar">
          <div v-for="ld in availableLeaders" :key="ld.id" class="p-4 rounded border border-gray-600 bg-gray-900 flex justify-between items-center hover:border-cyan-500 transition-colors">
            <div>
              <div class="font-bold text-lg text-white">{{ ld.name }}</div>
              <div class="text-sm text-cyan-400">{{ ld.title }} ({{ ld.type === 'fleet' ? 'Fleet Admiral' : 'Colony Admin' }})</div>
              <div class="text-xs text-gray-400 mt-1 italic">{{ ld.description }}</div>
              <ul class="text-xs text-gray-300 mt-2 list-disc ml-4">
                <li v-for="(val, key) in ld.bonuses" :key="key" class="capitalize">
                  +{{ val }} {{ key.replace(/_pct/g, '%').replace(/_/g, ' ') }}
                </li>
              </ul>
            </div>
            <div class="text-right ml-4 flex flex-col justify-between items-end h-full">
              <div class="my-2">
                <div class="text-yellow-400 text-sm font-bold">{{ ld.hire_cost }} BC cost</div>
                <div class="text-red-400 text-xs">{{ ld.upkeep }} BC/turn</div>
              </div>
              <BaseButton @click="hireLeader(ld.id)" :disabled="loading" variant="primary">Hire</BaseButton>
            </div>
          </div>
        </div>
      </div>

      <!-- Hired Leaders -->
      <div class="panel bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h3 class="text-xl font-semibold text-gray-200 mb-4">Hired Leaders</h3>
        
        <div v-if="hiredLeaders.length === 0" class="text-gray-500 text-center py-4 italic">
          No leaders hired yet. Hire candidates from the market to boost your empire.
        </div>
        
        <div v-else class="space-y-4 max-h-[500px] overflow-y-auto pr-2 custom-scrollbar">
          <div v-for="ld in hiredLeaders" :key="ld.uid" class="p-4 rounded border border-cyan-700 bg-gray-900">
            <div class="flex justify-between">
              <div class="font-bold text-lg text-white">{{ ld.name }}</div>
              <div class="text-sm text-gray-400 border border-gray-600 px-2 py-0.5 rounded">{{ ld.uid?.slice(0,8) }}</div>
            </div>
            <div class="text-sm text-cyan-400 mb-2">{{ ld.title }}</div>
            
            <div v-if="!ld.assigned_to" class="text-sm text-yellow-400 mt-4">Status: Unassigned</div>
            <div v-else class="text-sm text-green-400 mt-4">Assigned to: {{ ld.assigned_to }}</div>
            <!-- In a fully fleshed out UI, this is where assigning logic happens -->
          </div>
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
