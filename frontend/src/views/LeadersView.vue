<template>
  <div :style="styles.panel">
    <div :style="styles.head">
      <div>
        <h2 :style="styles.title">ACADEMIA IMPERIAL</h2>
        <p :style="styles.subtitle">Reclutamiento de gobernadores planetarios y almirantes de flota.</p>
      </div>
      <button :style="styles.btn" @click="reload">REFRESH</button>
    </div>

    <p v-if="error" :style="styles.error">{{ error }}</p>
    <p v-if="info" :style="styles.info">{{ info }}</p>

    <div :style="styles.mainGrid">
      <div :style="styles.innerPanel">
        <h3 :style="styles.innerTitle">CANDIDATOS DISPONIBLES</h3>
        <div v-if="!availableLeaders.length" :style="styles.empty">No hay candidatos esperando.</div>
        <div :style="styles.list">
          <div v-for="ld in availableLeaders" :key="ld.id" :style="styles.card">
            <div>
              <strong :style="{ color: '#fff' }">{{ ld.name }}</strong>
              <div :style="{ color: '#00ffff', fontSize: '0.8rem' }">
                Nivel {{ ld.level }} · {{ ld.type === 'colony' ? 'Colonia' : 'Nave' }}
              </div>
              <div :style="styles.skills">
                <span v-for="(s, i) in ld.skills || []" :key="i" :style="styles.skillBadge">
                  {{ s.id }} +{{ s.value }}
                </span>
              </div>
            </div>
            <div :style="{ textAlign: 'right' as const }">
              <div :style="{ color: '#ffd700', fontSize: '0.9rem' }">{{ ld.hire_cost }} BC</div>
              <button :style="styles.btnSmall" @click="hire(ld.id)">RECLUTAR</button>
            </div>
          </div>
        </div>
      </div>

      <div :style="styles.innerPanel">
        <h3 :style="styles.innerTitle">PERSONAL ACTIVO</h3>
        <div v-if="!hiredLeaders.length" :style="styles.empty">No tienes lideres contratados.</div>
        <div :style="styles.list">
          <div v-for="ld in hiredLeaders" :key="ld.id" :style="styles.cardActive">
            <div>
              <strong :style="{ color: '#fff' }">{{ ld.name }}</strong>
              <div :style="{ color: '#00ffff', fontSize: '0.8rem' }">
                Nivel {{ ld.level }} · {{ ld.type === 'colony' ? 'Colonia' : 'Nave' }}
              </div>
              <div :style="styles.skills">
                <span v-for="(s, i) in ld.skills || []" :key="i" :style="styles.skillBadge">
                  {{ s.id }} +{{ s.value }}
                </span>
              </div>
              <div :style="styles.assignmentRow">
                <select v-model="assignments[ld.id]" :style="styles.select">
                  <option value="">sin asignacion</option>
                  <optgroup label="Colonias">
                    <option v-for="c in colonies" :key="c.id" :value="c.id">{{ c.name }}</option>
                  </optgroup>
                  <optgroup label="Flotas">
                    <option v-for="f in fleets" :key="f.id" :value="f.id">{{ f.name }}</option>
                  </optgroup>
                </select>
                <button :style="styles.btnSmall" @click="assign(ld.id)">ASIGNAR</button>
                <button :style="styles.btnDanger" @click="dismiss(ld.id)">DESPEDIR</button>
              </div>
            </div>
            <div :style="{ textAlign: 'right' as const, fontSize: '0.75rem', color: '#aaaacc' }">
              -{{ ld.upkeep_per_turn }} BC/T
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
import { api } from '../api/client'
import { Theme, createPanelStyle, btnStyle } from '../styles/styleSystem'

const gameStore = useGameStore()
const error = ref('')
const info = ref('')
const assignments = ref<Record<string, string>>({})

const hiredLeaders = computed<any[]>(() => gameStore.leaders || [])
const availableLeaders = computed<any[]>(() => gameStore.availableLeaders || [])
const colonies = computed<any[]>(() => gameStore.colonies || [])
const fleets = computed<any[]>(() => gameStore.fleets || [])

const styles = {
  panel: createPanelStyle(),
  head: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', borderBottom: `2px solid ${Theme.colors.primary}`, paddingBottom: '1rem' },
  title: { margin: 0, fontSize: '1.6rem', color: Theme.colors.primary, letterSpacing: '0.18em' },
  subtitle: { margin: '0.3rem 0 0', color: Theme.colors.textMuted, fontSize: '0.85rem' },
  mainGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' },
  innerPanel: { padding: '0.9rem', backgroundColor: Theme.colors.bgDark, border: `1px solid ${Theme.colors.border}`, borderRadius: '8px' },
  innerTitle: { margin: '0 0 0.8rem', fontSize: '1rem', color: Theme.colors.secondary, letterSpacing: '0.1em' },
  list: { display: 'flex', flexDirection: 'column' as const, gap: '0.6rem' },
  card: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', padding: '0.7rem', backgroundColor: '#070f24', border: '1px solid rgba(89, 170, 255, 0.18)', borderRadius: '4px', gap: '0.6rem' },
  cardActive: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', padding: '0.7rem', backgroundColor: '#162244', border: '1px solid #00ffff', borderRadius: '4px', gap: '0.6rem' },
  skills: { display: 'flex', flexWrap: 'wrap' as const, gap: '0.3rem', marginTop: '0.3rem' },
  skillBadge: { fontSize: '0.65rem', padding: '0.1rem 0.4rem', backgroundColor: '#152040', color: Theme.colors.ok, border: '1px solid rgba(68, 238, 68, 0.4)', borderRadius: '3px' },
  assignmentRow: { marginTop: '0.5rem', display: 'flex', gap: '0.3rem', flexWrap: 'wrap' as const },
  select: { backgroundColor: '#070f24', color: Theme.colors.primary, border: `1px solid ${Theme.colors.primary}`, padding: '0.25rem 0.4rem', fontSize: '0.75rem' },
  btn: btnStyle(),
  btnSmall: { ...btnStyle(), padding: '0.3rem 0.6rem', fontSize: '0.7rem' },
  btnDanger: { ...btnStyle(), padding: '0.3rem 0.6rem', fontSize: '0.7rem', borderColor: Theme.colors.danger, color: Theme.colors.danger },
  empty: { color: Theme.colors.textMuted, fontStyle: 'italic' as const, padding: '0.4rem' },
  error: { color: Theme.colors.danger, marginBottom: '0.6rem' },
  info: { color: Theme.colors.ok, marginBottom: '0.6rem' },
}

async function reload() {
  error.value = ''
  info.value = ''
  if (!gameStore.gameId) return
  try {
    await Promise.all([gameStore.fetchLeaders(), gameStore.fetchColonies(), gameStore.fetchFleets()])
  } catch (err: any) {
    error.value = err.message
  }
}

async function hire(leaderId: string) {
  try {
    const res = await gameStore.hireLeader(leaderId)
    info.value = res?.success ? `Lider ${leaderId} contratado` : res?.reason || 'No se pudo contratar'
  } catch (err: any) {
    error.value = err.message
  }
}

async function assign(leaderId: string) {
  const target = assignments.value[leaderId]
  if (!target) return
  try {
    await gameStore.assignLeader(leaderId, target)
    info.value = `Lider ${leaderId} asignado a ${target}`
  } catch (err: any) {
    error.value = err.message
  }
}

async function dismiss(leaderId: string) {
  if (!confirm('Despedir a este lider?')) return
  try {
    await api.leaders.dismiss(gameStore.gameId!, leaderId)
    await gameStore.fetchLeaders()
    info.value = `Lider ${leaderId} despedido`
  } catch (err: any) {
    error.value = err.message
  }
}

onMounted(reload)
</script>
