<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../services/api'
import BaseButton from './BaseButton.vue'
import ErrorAlert from './ErrorAlert.vue'

const route = useRoute()
const gameId = route.params.id as string

interface Spy {
  id: string
  name: string
  level: number
  level_name: string
  skill: number
  salary: number
  status: string
  mission: string | null
  mission_type?: string | null
  assigned_to: string | null
  turns_remaining?: number
  detection_risk?: number
}

interface SpyLevelInfo {
  name: string
  detect_min: number
  detect_max: number
  effectiveness: number
  cost: number
  salary: number
}

const spies = ref<Spy[]>([])
const error = ref('')
const loading = ref(false)
const message = ref('')

const spyLevels = ref<Record<number, SpyLevelInfo>>({})
const missionTypes = ref<string[]>([])

const selectedSpyId = ref<string | null>(null)
const selectedMission = ref('info_probe')
const targetPlayer = ref('')
const recruitLevel = ref<1 | 2 | 3 | 4>(1)

const missionLabels: Record<string, string> = {
  info_probe: 'Sondeo de información (riesgo bajo)',
  tech_espionage: 'Espionaje tecnológico (riesgo medio)',
  economic_sabotage: 'Sabotaje económico (riesgo alto)',
  military_sabotage: 'Sabotaje militar (riesgo muy alto)',
  scientific_sabotage: 'Sabotaje científico (riesgo alto)',
  political_espionage: 'Espionaje político (riesgo medio)',
  sabotage: 'Sabotaje (legacy)',
  steal_tech: 'Robar tech (legacy)',
  assassinate: 'Asesinar líder (legacy)',
  incite_revolt: 'Incitar revuelta (legacy)',
}

const selectedSpy = computed(() => spies.value.find((s) => s.id === selectedSpyId.value))

const fetchSpies = async () => {
  try {
    loading.value = true
    const res = await api.getEspionage(gameId)
    spies.value = res.spies || []
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Failed to fetch spies'
  } finally {
    loading.value = false
  }
}

const fetchLevels = async () => {
  try {
    const res = await api.getSpyLevels(gameId)
    spyLevels.value = res.levels || {}
    missionTypes.value = res.missions || []
    if (missionTypes.value.length && !missionTypes.value.includes(selectedMission.value)) {
      selectedMission.value = missionTypes.value[0]
    }
  } catch (err: any) {
    error.value = err.response?.data?.error || 'No se pudieron cargar niveles'
  }
}

const recruitSpy = async () => {
  try {
    loading.value = true
    error.value = ''
    await api.recruitSpy(gameId, recruitLevel.value)
    message.value = `Espía nivel ${recruitLevel.value} reclutado.`
    await fetchSpies()
  } catch (err: any) {
    error.value = err.response?.data?.error || 'No se pudo reclutar espía.'
  } finally {
    loading.value = false
  }
}

const assignMission = async () => {
  if (!selectedSpyId.value || !targetPlayer.value) {
    error.value = 'Selecciona un espía y un objetivo.'
    return
  }
  try {
    loading.value = true
    const res = await api.assignSpyMission(
      gameId,
      selectedSpyId.value,
      targetPlayer.value,
      selectedMission.value,
    )
    message.value = `Misión asignada. Riesgo estimado: ${res.estimated_risk ?? '?'}%, duración ${res.duration ?? 1}t`
    await fetchSpies()
  } catch (err: any) {
    error.value = err.response?.data?.error || 'No se pudo asignar misión.'
  } finally {
    loading.value = false
  }
}

const assignDefense = async () => {
  if (!selectedSpyId.value) return
  try {
    loading.value = true
    await api.assignSpyDefense(gameId, selectedSpyId.value)
    message.value = 'Espía asignado a contraespionaje.'
    await fetchSpies()
  } catch (err: any) {
    error.value = err.response?.data?.error || 'No se pudo asignar defensa.'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchSpies()
  fetchLevels()
})
</script>

<template>
  <div class="espionage-view p-6 bg-gray-900 text-white min-h-screen">
    <h2 class="text-3xl text-cyan-400 mb-6 font-bold border-b border-cyan-800 pb-2">Red de Inteligencia</h2>

    <ErrorAlert v-if="error" :message="error" @close="error = ''" class="mb-4" />
    <p v-if="message" class="text-green-400 mb-4">{{ message }}</p>

    <!-- Spy levels reference -->
    <div class="bg-gray-800 rounded p-3 mb-6 border border-gray-700">
      <div class="text-cyan-300 text-sm mb-2">Niveles de Espía (DIPLOMACY sec 9)</div>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
        <div v-for="(lvl, key) in spyLevels" :key="key" class="bg-gray-900 p-2 rounded">
          <div class="font-bold text-cyan-400">Nivel {{ key }} — {{ lvl.name }}</div>
          <div>Detección: {{ lvl.detect_min }}–{{ lvl.detect_max }}%</div>
          <div>Eficacia: {{ lvl.effectiveness }}×</div>
          <div>Coste: {{ lvl.cost }} BC + {{ lvl.salary }}/turno</div>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <!-- Roster panel -->
      <div class="panel bg-gray-800 rounded-lg p-6 border border-gray-700">
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-xl font-semibold text-gray-200">Agentes Activos</h3>
          <div class="flex items-center gap-2">
            <select v-model.number="recruitLevel" class="bg-gray-900 border border-gray-600 rounded px-2 py-1 text-sm">
              <option :value="1">Nivel 1 (50)</option>
              <option :value="2">Nivel 2 (100)</option>
              <option :value="3">Nivel 3 (200)</option>
              <option :value="4">Nivel 4 (400)</option>
            </select>
            <BaseButton @click="recruitSpy" :disabled="loading" variant="primary">
              Reclutar
            </BaseButton>
          </div>
        </div>

        <div v-if="loading && spies.length === 0" class="text-center py-4">Cargando agentes...</div>

        <div v-else-if="spies.length === 0" class="text-gray-500 text-center py-4">
          No hay espías reclutados todavía.
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
              <span class="text-cyan-400">L{{ spy.level }} · {{ spy.level_name }} · skill {{ spy.skill }}</span>
            </div>
            <div class="mt-2 text-sm">
              <span v-if="spy.status === 'idle'" class="text-green-400">● Disponible</span>
              <span v-else-if="spy.mission === 'defense'" class="text-blue-400">● Contraespionaje</span>
              <span v-else-if="spy.status === 'compromised'" class="text-red-400">● Comprometido</span>
              <span v-else class="text-yellow-400">
                ● {{ spy.mission_type || spy.mission }} → {{ spy.assigned_to }}
                <span v-if="spy.turns_remaining"> ({{ spy.turns_remaining }}t)</span>
                <span v-if="spy.detection_risk"> · riesgo {{ spy.detection_risk }}%</span>
              </span>
            </div>
            <div class="text-xs text-gray-500">Salario: {{ spy.salary }} BC/turno</div>
          </div>
        </div>
      </div>

      <!-- Command panel -->
      <div class="panel bg-gray-800 rounded-lg p-6 border border-gray-700 opacity-90">
        <h3 class="text-xl font-semibold text-gray-200 mb-6">Centro de Mando</h3>

        <div v-if="!selectedSpy" class="text-gray-500 italic mb-4">
          Selecciona un agente del listado.
        </div>

        <div v-else class="space-y-6">
          <div class="text-sm text-gray-400">
            Operativo seleccionado: <span class="text-cyan-300">{{ selectedSpy.name }}</span>
            (L{{ selectedSpy.level }})
          </div>

          <div>
            <label class="block text-gray-400 mb-2">Imperio objetivo:</label>
            <input
              v-model="targetPlayer"
              type="text"
              placeholder="ej. ai_0"
              class="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-white focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div>
            <label class="block text-gray-400 mb-2">Tipo de operación:</label>
            <select
              v-model="selectedMission"
              class="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-white focus:outline-none focus:border-cyan-500"
            >
              <option v-for="m in missionTypes" :key="m" :value="m">{{ missionLabels[m] || m }}</option>
            </select>
          </div>

          <div class="flex gap-2">
            <BaseButton
              @click="assignMission"
              :disabled="loading || !targetPlayer"
              variant="danger"
              class="flex-1"
            >
              Iniciar misión
            </BaseButton>
            <BaseButton
              @click="assignDefense"
              :disabled="loading"
              variant="primary"
              class="flex-1"
            >
              Defensa
            </BaseButton>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 6px; }
.custom-scrollbar::-webkit-scrollbar-track { background: #1f2937; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #4b5563; border-radius: 3px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #6b7280; }
</style>
