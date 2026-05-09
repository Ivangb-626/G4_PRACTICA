<template>
  <div :style="styles.panel">
    <div :style="styles.head">
      <div>
        <h2 :style="styles.title">RESEARCH & DEVELOPMENT</h2>
        <p :style="styles.subtitle">
          {{ current ? `EN CURSO: ${current.tech_id} (${Math.round(currentProgress)}%)` : 'SIN PROYECTO ACTIVO' }}
        </p>
      </div>
      <button :style="styles.btn" @click="reload">REFRESH</button>
    </div>

    <div v-if="error" :style="styles.error">{{ error }}</div>

    <div v-if="current" :style="styles.breakthrough">
      <div :style="styles.progressLabel">PROGRESO: {{ current.progress }} / {{ current.total_cost }} RP</div>
      <div :style="styles.progressBar">
        <div :style="{ ...styles.progressFill, width: currentProgress + '%' }"></div>
      </div>
    </div>

    <div :style="styles.fieldList">
      <div v-for="field in fields" :key="field.field" :style="styles.fieldCard">
        <h3 :style="styles.fieldTitle">{{ String(field.field).toUpperCase() }}</h3>

        <div v-for="level in field.levels" :key="level.level" :style="styles.levelRow">
          <div :style="styles.levelLabel">NIVEL {{ level.level }}</div>
          <div :style="styles.optionGrid">
            <div v-for="opt in sortedOptions(level.options)" :key="opt.tech_id" :style="getOptionStyle(opt.status)">
              <Tooltip :title="opt.name?.toUpperCase()" :description="techTooltip(opt)" :details="techDetails(opt)">
              <div :style="{ flex: 1 }">
                <strong :style="{ color: '#fff' }">{{ opt.name?.toUpperCase() }}</strong>
                <p :style="styles.subtitle">{{ opt.description }}</p>
                <small :style="{ color: '#8888aa', fontSize: '0.7rem' }">COSTE: {{ opt.research_cost ?? opt.base_cost }} RP</small>
                <small v-if="opt.locked_reason" :style="styles.lockedReason">{{ opt.locked_reason }}</small>
              </div>
            </Tooltip>
              <button v-if="opt.status === 'available'" :style="styles.btnSmall" @click="selectTech(opt)">INVESTIGAR</button>
              <span v-else :style="styles.statusBadge">{{ opt.status?.toUpperCase() }}</span>
            </div>
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
import Tooltip from '../components/Tooltip.vue' // Import the Tooltip component

const gameStore = useGameStore()
const error = ref('')

const fields = computed<any[]>(() => gameStore.techState?.fields || [])
const current = computed(() => gameStore.techState?.current_research)
const currentProgress = computed(() => {
  const c = current.value
  if (!c) return 0
  return Math.min(100, ((c.progress || 0) / Math.max(c.total_cost || 1, 1)) * 100)
})

const styles = {
  panel: createPanelStyle(),
  head: { display: 'flex', justifyContent: 'space-between', marginBottom: '1.4rem', borderBottom: `2px solid ${Theme.colors.primary}`, paddingBottom: '1rem' },
  title: { margin: 0, fontSize: '1.6rem', color: Theme.colors.primary, letterSpacing: '0.18em' },
  subtitle: { margin: '0.3rem 0 0', color: Theme.colors.textMuted, fontSize: '0.85rem' },
  btn: btnStyle(),
  btnSmall: { ...btnStyle(), padding: '0.3rem 0.6rem', fontSize: '0.75rem' },
  fieldList: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: '1rem' },
  fieldCard: { padding: '0.9rem', backgroundColor: Theme.colors.bgDark, border: `1px solid ${Theme.colors.border}`, borderRadius: '8px' },
  fieldTitle: { margin: '0 0 0.7rem', fontSize: '1rem', color: Theme.colors.secondary, borderBottom: `1px solid ${Theme.colors.secondary}`, paddingBottom: '0.3rem' },
  levelRow: { marginBottom: '0.8rem' },
  levelLabel: { fontSize: '0.7rem', color: Theme.colors.textMuted, marginBottom: '0.3rem', textTransform: 'uppercase' as const },
  optionGrid: { display: 'grid', gridTemplateColumns: '1fr', gap: '0.4rem' },
  statusBadge: { fontSize: '0.7rem', padding: '0.2rem 0.5rem', backgroundColor: Theme.colors.bgDark, color: Theme.colors.textMuted, border: `1px solid ${Theme.colors.border}`, borderRadius: '4px', alignSelf: 'center' as const },
  lockedReason: { display: 'block', marginTop: '0.25rem', color: '#ffaa66', fontSize: '0.72rem', lineHeight: 1.25 },
  breakthrough: { marginBottom: '1rem', padding: '0.7rem 0.9rem', backgroundColor: Theme.colors.bgDark, border: `1px solid ${Theme.colors.secondary}`, borderRadius: '6px' },
  progressLabel: { fontSize: '0.75rem', color: Theme.colors.secondary, marginBottom: '0.4rem' },
  progressBar: { width: '100%', height: '8px', backgroundColor: '#0a1530', border: `1px solid ${Theme.colors.border}`, borderRadius: '4px', overflow: 'hidden' as const },
  progressFill: { height: '100%', backgroundColor: Theme.colors.secondary, transition: 'width 0.3s ease' },
  error: { color: Theme.colors.danger, marginBottom: '0.6rem' },
}

function getOptionStyle(status: string) {
  let borderColor = 'rgba(112, 166, 214, 0.18)'
  let opacity = 1
  if (status === 'available') borderColor = '#00ffff'
  if (status === 'current') borderColor = '#ffd700'
  if (status === 'researched') borderColor = '#44ee44'
  if (status === 'discarded') {
    borderColor = '#553355'
    opacity = 0.55
  }
  if (status === 'locked') {
    borderColor = '#555566'
    opacity = 0.58
  }
  return {
    display: 'flex',
    gap: '0.5rem',
    justifyContent: 'space-between',
    alignItems: 'flex-start' as const,
    padding: '0.6rem',
    backgroundColor: '#070f24',
    border: `1px solid ${borderColor}`,
    borderRadius: '4px',
    opacity,
  }
}

function statusRank(status: string) {
  return ({ available: 0, current: 1, researched: 2, locked: 3, discarded: 4 } as Record<string, number>)[status] ?? 5
}

function sortedOptions(options: any[] = []) {
  return [...options].sort((a, b) => statusRank(a.status) - statusRank(b.status) || (a.research_cost || 0) - (b.research_cost || 0))
}

function techTooltip(opt: any) {
  if (opt?.status === 'locked' && opt.locked_reason) return `${opt.description || ''} Bloqueada: ${opt.locked_reason}`
  if (opt?.status === 'discarded' && opt.locked_reason) return `${opt.description || ''} ${opt.locked_reason}`
  return opt?.description || ''
}

function techDetails(opt: any) {
  const details: Record<string, string> = {
    Coste: `${opt.research_cost ?? opt.base_cost} RP`,
    Estado: String(opt.status || 'unknown'),
  }
  if (opt.locked_reason) details.Requisito = opt.locked_reason
  return details
}

async function selectTech(opt: any) {
  if (!gameStore.gameId || !opt) return
  try {
    await gameStore.selectResearch({ field: opt.field, level: opt.level, tech_id: opt.tech_id })
  } catch (err: any) {
    error.value = err.message || 'No se pudo seleccionar la tecnologia'
  }
}

async function reload() {
  error.value = ''
  try {
    await gameStore.fetchResearch()
  } catch (err: any) {
    error.value = err.message || 'No se pudo cargar el arbol tecnologico'
  }
}

onMounted(reload)
</script>
