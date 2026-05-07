<template>
  <div :style="styles.panel">
    <div :style="styles.head">
      <div>
        <h2 :style="styles.title">SENADO GALACTICO</h2>
        <p :style="styles.subtitle">Distribucion de votos y candidatura para Gobernante Supremo.</p>
      </div>
      <div>
        <button :style="styles.btn" @click="reload">REFRESH</button>
        <button :style="styles.btnSmall" @click="convene">CONVOCAR</button>
      </div>
    </div>

    <p v-if="error" :style="styles.error">{{ error }}</p>
    <p v-if="info" :style="styles.info">{{ info }}</p>

    <div v-if="council">
      <p :style="styles.summary">
        Total de votos en juego: <strong>{{ council.total ?? 0 }}</strong>
        · Mayoria 2/3 necesaria: <strong>{{ Math.ceil(council.needed_two_thirds || 0) }}</strong>
      </p>

      <table :style="styles.table">
        <thead>
          <tr>
            <th :style="styles.th">FACCION</th>
            <th :style="styles.th">VOTOS</th>
            <th :style="styles.th">% TOTAL</th>
            <th :style="styles.th">VOTAR POR</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in voteRows" :key="row.faction">
            <td :style="styles.td"><strong>{{ row.faction.toUpperCase() }}</strong></td>
            <td :style="styles.td">{{ row.votes }}</td>
            <td :style="styles.td">{{ Math.round(row.percent) }}%</td>
            <td :style="styles.td">
              <button :style="styles.btnSmall" @click="vote(row.faction)">VOTAR</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <p v-else :style="styles.empty">Aun no se ha convocado al Senado.</p>
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

const council = computed<any>(() => gameStore.council)

const voteRows = computed(() => {
  if (!council.value?.votes) return []
  const total = council.value.total || 1
  return Object.entries(council.value.votes).map(([faction, votes]) => ({
    faction,
    votes: votes as number,
    percent: ((votes as number) / total) * 100,
  }))
})

const styles = {
  panel: createPanelStyle(),
  head: { display: 'flex', justifyContent: 'space-between', marginBottom: '1.5rem', borderBottom: `1px solid ${Theme.colors.border}`, paddingBottom: '1rem' },
  title: { margin: 0, fontSize: '1.6rem', color: Theme.colors.primary, letterSpacing: '0.18em' },
  subtitle: { margin: '0.3rem 0 0', color: Theme.colors.textMuted, fontSize: '0.85rem' },
  summary: { color: Theme.colors.text, marginBottom: '0.7rem', fontSize: '0.9rem' },
  table: { width: '100%', borderCollapse: 'collapse' as const },
  th: { textAlign: 'left' as const, padding: '0.5rem', color: Theme.colors.textMuted, fontSize: '0.75rem', textTransform: 'uppercase' as const, borderBottom: `1px solid ${Theme.colors.border}` },
  td: { padding: '0.5rem', borderBottom: '1px solid rgba(89, 170, 255, 0.15)', fontSize: '0.85rem' },
  btn: btnStyle(),
  btnSmall: { ...btnStyle(), padding: '0.3rem 0.6rem', fontSize: '0.75rem', marginLeft: '0.4rem' },
  error: { color: Theme.colors.danger, marginBottom: '0.6rem' },
  info: { color: Theme.colors.ok, marginBottom: '0.6rem' },
  empty: { color: Theme.colors.textMuted, fontStyle: 'italic' as const, marginTop: '0.5rem' },
}

async function reload() {
  error.value = ''
  info.value = ''
  if (!gameStore.gameId) return
  try {
    await gameStore.fetchCouncil()
  } catch (err: any) {
    error.value = err.message
  }
}

async function convene() {
  try {
    const res = await api.council.convene(gameStore.gameId!)
    info.value = res?.convened ? 'Senado convocado' : (res?.reason || 'No se pudo convocar')
    await reload()
  } catch (err: any) {
    error.value = err.message
  }
}

async function vote(candidate: string) {
  try {
    const res = await gameStore.voteCouncil(candidate)
    info.value = res?.success ? `Voto por ${candidate} registrado` : 'No se pudo votar'
  } catch (err: any) {
    error.value = err.message
  }
}

onMounted(reload)
</script>
