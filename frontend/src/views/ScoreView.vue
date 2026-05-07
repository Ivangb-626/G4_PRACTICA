<template>
  <div :style="styles.panel">
    <div :style="styles.head">
      <div>
        <h2 :style="styles.title">PUNTUACION FINAL</h2>
        <p :style="styles.subtitle">Resumen del rendimiento del imperio.</p>
      </div>
      <button :style="styles.btn" @click="reload">REFRESH</button>
    </div>

    <p v-if="error" :style="styles.error">{{ error }}</p>

    <div v-if="score">
      <div :style="styles.totalCard">
        <div :style="styles.totalLabel">PUNTUACION TOTAL</div>
        <div :style="styles.totalValue">{{ score.final }}</div>
        <div :style="styles.subLabel">
          subtotal {{ score.subtotal }} × multiplicador {{ score.custom_race_multiplier?.toFixed?.(2) || '1.00' }}
        </div>
      </div>

      <table :style="styles.table">
        <thead>
          <tr>
            <th :style="styles.th">CONCEPTO</th>
            <th :style="styles.th">PUNTOS</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in breakdownRows" :key="row.key">
            <td :style="styles.td">{{ row.label }}</td>
            <td :style="styles.tdNumber">{{ row.value }}</td>
          </tr>
          <tr :style="styles.tdTotal">
            <td :style="styles.td"><strong>SUBTOTAL</strong></td>
            <td :style="styles.tdNumber"><strong>{{ score.subtotal }}</strong></td>
          </tr>
        </tbody>
      </table>

      <p :style="styles.subtitle">
        Condicion de victoria: <strong :style="{ color: '#88ff88' }">
          {{ score.victory_condition || 'En curso' }}
        </strong>
      </p>
    </div>
    <p v-else :style="styles.empty">Sin datos de puntuacion todavia.</p>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useGameStore } from '../store/gameStore'
import { Theme, createPanelStyle, btnStyle } from '../styles/styleSystem'

const gameStore = useGameStore()
const route = useRoute()
const router = useRouter()
const error = ref('')

const score = computed(() => gameStore.score)

const labels: Record<string, string> = {
  base: 'Base (500 - turnos)',
  captured_colonists: 'Colonistas capturados (×2)',
  own_population: 'Poblacion propia (×1)',
  hyper_advanced_techs: 'Techs Hiper-Avanzadas (×5)',
  rivals_eliminated: 'Rivales eliminados (×50)',
  guardian_defeated: 'Guardian de Orion derrotado',
  antarans_defeated: 'Antaranos derrotados',
  galactic_ruler: 'Bonus Senado',
}

const breakdownRows = computed(() => {
  const b = score.value?.breakdown || {}
  return Object.entries(b).map(([key, value]) => ({
    key,
    label: labels[key] || key,
    value,
  }))
})

const styles = {
  panel: createPanelStyle(),
  head: { display: 'flex', justifyContent: 'space-between', marginBottom: '1.5rem', borderBottom: `1px solid ${Theme.colors.border}`, paddingBottom: '1rem' },
  title: { margin: 0, fontSize: '1.6rem', color: Theme.colors.primary, letterSpacing: '0.18em' },
  subtitle: { margin: '0.3rem 0 0', color: Theme.colors.textMuted, fontSize: '0.85rem' },
  totalCard: { padding: '1rem 1.2rem', backgroundColor: Theme.colors.bgDark, border: `2px solid ${Theme.colors.secondary}`, borderRadius: '8px', textAlign: 'center' as const, marginBottom: '1rem' },
  totalLabel: { color: Theme.colors.textMuted, fontSize: '0.75rem', letterSpacing: '0.1em' },
  totalValue: { color: Theme.colors.secondary, fontSize: '2.2rem', fontWeight: 'bold' as const, margin: '0.3rem 0' },
  subLabel: { color: Theme.colors.textMuted, fontSize: '0.75rem' },
  table: { width: '100%', borderCollapse: 'collapse' as const, marginBottom: '0.6rem' },
  th: { textAlign: 'left' as const, padding: '0.5rem', color: Theme.colors.textMuted, fontSize: '0.75rem', textTransform: 'uppercase' as const, borderBottom: `1px solid ${Theme.colors.border}` },
  td: { padding: '0.5rem', borderBottom: '1px solid rgba(89, 170, 255, 0.15)', fontSize: '0.85rem' },
  tdNumber: { padding: '0.5rem', borderBottom: '1px solid rgba(89, 170, 255, 0.15)', fontSize: '0.85rem', textAlign: 'right' as const, color: Theme.colors.ok },
  tdTotal: { backgroundColor: 'rgba(0, 255, 255, 0.07)' },
  btn: btnStyle(),
  error: { color: Theme.colors.danger, marginBottom: '0.6rem' },
  empty: { color: Theme.colors.textMuted, fontStyle: 'italic' as const, padding: '1rem' },
}

async function reload() {
  error.value = ''
  if (!gameStore.gameId) return
  try {
    await gameStore.fetchScore()
  } catch (err: any) {
    error.value = err.message
  }
}

onMounted(async () => {
  // La pantalla de puntuacion solo es accesible cuando la partida termina.
  if (!gameStore.isGameOver) {
    const id = String(route.params.id || gameStore.gameId || '')
    router.replace(id ? `/game/${id}/galaxy` : '/dashboard')
    return
  }
  await reload()
})
</script>
