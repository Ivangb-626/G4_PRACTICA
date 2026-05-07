<template>
  <div :style="styles.panel">
    <div :style="styles.head">
      <div>
        <h2 :style="styles.title">RED DE ESPIONAJE</h2>
        <p :style="styles.subtitle">Reclutamiento de espias y operaciones encubiertas.</p>
      </div>
      <button :style="styles.btn" @click="reload">REFRESH</button>
    </div>

    <p v-if="error" :style="styles.error">{{ error }}</p>
    <p v-if="info" :style="styles.info">{{ info }}</p>

    <div :style="styles.mainGrid">
      <div :style="styles.innerPanel">
        <div :style="styles.innerHead">
          <h3 :style="styles.innerTitle">AGENTES ACTIVOS</h3>
          <button :style="styles.btnSmall" @click="recruit">RECLUTAR</button>
        </div>

        <div v-if="!spies.length" :style="styles.empty">No hay espias todavia.</div>
        <div :style="styles.spyList">
          <div v-for="spy in spies" :key="spy.id"
               :style="getSpyCardStyle(spy.id)"
               @click="selectedSpyId = spy.id">
            <div :style="styles.spyHead">
              <strong :style="{ color: '#fff' }">{{ spy.id }}</strong>
              <span :style="{ color: '#00ffff', fontSize: '0.75rem' }">EXP {{ spy.experience || 0 }}</span>
            </div>
            <div :style="styles.spyMeta">
              Asignado: <em>{{ spy.assignment || 'sin asignacion' }}</em>
              <span v-if="spy.mission"> · Mision: {{ spy.mission }}</span>
            </div>
          </div>
        </div>
      </div>

      <div :style="styles.innerPanel">
        <h3 :style="styles.innerTitle">CENTRO DE OPERACIONES</h3>
        <div v-if="!selectedSpyId" :style="styles.placeholder">Selecciona un agente para asignar mision.</div>
        <div v-else :style="styles.form">
          <label :style="styles.label">IMPERIO OBJETIVO</label>
          <select v-model="targetEmpire" :style="styles.input">
            <option value="">selecciona</option>
            <option v-for="ai in aiTargets" :key="ai" :value="ai">{{ ai }}</option>
          </select>

          <label :style="styles.label">OPERACION</label>
          <select v-model="selectedMission" :style="styles.input">
            <option v-for="m in missionTypes" :key="m" :value="m">{{ m.toUpperCase().replace('_', ' ') }}</option>
          </select>

          <div :style="{ display: 'flex', gap: '0.6rem', marginTop: '0.8rem', flexWrap: 'wrap' }">
            <button :style="styles.btnDanger" @click="assignMission">LANZAR MISION</button>
            <button :style="styles.btnSmall" @click="assignDefense">DEFENSA</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useGameStore } from '../store/gameStore'
import { Theme, createPanelStyle, btnStyle } from '../styles/styleSystem'

const gameStore = useGameStore()
const error = ref('')
const info = ref('')

const selectedSpyId = ref<string | null>(null)
const targetEmpire = ref<string>('')
const selectedMission = ref<string>('steal_tech')
const missionTypes = ['steal_tech', 'sabotage', 'incite_rebellion', 'frame']

const spies = computed<any[]>(() => gameStore.spies || [])
const aiTargets = computed<string[]>(() => {
  const game = gameStore.game as any
  const ais = (game?.ai_players || []).map((ai: any) => ai.id)
  return ais
})

const styles = {
  panel: createPanelStyle(),
  head: { display: 'flex', justifyContent: 'space-between', marginBottom: '1.5rem', borderBottom: `1px solid ${Theme.colors.border}`, paddingBottom: '1rem' },
  title: { margin: 0, fontSize: '1.6rem', color: Theme.colors.primary, letterSpacing: '0.18em' },
  subtitle: { margin: '0.3rem 0 0', color: Theme.colors.textMuted, fontSize: '0.85rem' },
  mainGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' },
  innerPanel: { padding: '0.9rem', backgroundColor: Theme.colors.bgDark, border: `1px solid ${Theme.colors.border}`, borderRadius: '8px' },
  innerHead: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.7rem' },
  innerTitle: { margin: 0, fontSize: '1rem', color: Theme.colors.secondary, letterSpacing: '0.1em' },
  spyList: { display: 'flex', flexDirection: 'column' as const, gap: '0.6rem' },
  spyHead: { display: 'flex', justifyContent: 'space-between' },
  spyMeta: { fontSize: '0.75rem', color: Theme.colors.textMuted, marginTop: '0.25rem' },
  empty: { color: Theme.colors.textMuted, fontStyle: 'italic' as const, marginTop: '0.4rem' },
  placeholder: { padding: '2rem', textAlign: 'center' as const, color: Theme.colors.textMuted, fontStyle: 'italic' as const },
  form: { display: 'flex', flexDirection: 'column' as const, gap: '0.5rem' },
  label: { fontSize: '0.75rem', color: Theme.colors.textMuted },
  input: { backgroundColor: '#070f24', color: Theme.colors.text, border: `1px solid ${Theme.colors.primary}`, padding: '0.4rem', borderRadius: '4px' },
  btn: btnStyle(),
  btnSmall: { ...btnStyle(), padding: '0.3rem 0.6rem', fontSize: '0.75rem' },
  btnDanger: { ...btnStyle(), borderColor: Theme.colors.danger, color: Theme.colors.danger, padding: '0.4rem 0.8rem', fontSize: '0.8rem' },
  error: { color: Theme.colors.danger, marginBottom: '0.5rem' },
  info: { color: Theme.colors.ok, marginBottom: '0.5rem' },
}

function getSpyCardStyle(id: string) {
  const isSelected = selectedSpyId.value === id
  return {
    padding: '0.6rem 0.7rem',
    backgroundColor: isSelected ? '#162244' : '#070f24',
    border: `1px solid ${isSelected ? Theme.colors.primary : Theme.colors.border}`,
    borderRadius: '4px',
    cursor: 'pointer',
    transition: 'all 0.15s',
  }
}

async function reload() {
  error.value = ''
  info.value = ''
  if (!gameStore.gameId) return
  try {
    await gameStore.fetchSpies()
  } catch (err: any) {
    error.value = err.message
  }
}

async function recruit() {
  error.value = ''
  info.value = ''
  try {
    const res = await gameStore.recruitSpy()
    if (res?.success) info.value = `Espia reclutado por ${res.cost} BC`
    else error.value = res?.reason || 'No se pudo reclutar'
  } catch (err: any) {
    error.value = err.message
  }
}

async function assignMission() {
  if (!selectedSpyId.value || !targetEmpire.value) return
  try {
    const res = await gameStore.assignSpy(selectedSpyId.value, targetEmpire.value, selectedMission.value)
    info.value = res?.success ? 'Mision asignada' : res?.reason || 'Falla al asignar mision'
  } catch (err: any) {
    error.value = err.message
  }
}

async function assignDefense() {
  if (!selectedSpyId.value) return
  try {
    await gameStore.assignSpy(selectedSpyId.value, '', 'defense')
    info.value = 'Asignado a defensa'
  } catch (err: any) {
    error.value = err.message
  }
}

onMounted(reload)
</script>
