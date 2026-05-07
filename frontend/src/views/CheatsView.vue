<template>
  <div :style="styles.panel">
    <div :style="styles.head">
      <div>
        <h2 :style="styles.title">PANEL DE CHEATS</h2>
        <p :style="styles.subtitle">Atajos para depuracion y pruebas.</p>
      </div>
      <button :style="styles.btn" @click="reload">REFRESH</button>
    </div>

    <p v-if="error" :style="styles.error">{{ error }}</p>
    <p v-if="info" :style="styles.info">{{ info }}</p>

    <div :style="styles.grid">
      <button v-for="code in codes" :key="code" :style="styles.cheatBtn" @click="apply(code)">
        {{ code.toUpperCase().replace(/_/g, ' ') }}
      </button>
    </div>

    <p v-if="!codes.length" :style="styles.empty">No hay codigos disponibles.</p>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useGameStore } from '../store/gameStore'
import { api } from '../api/client'
import { Theme, createPanelStyle, btnStyle } from '../styles/styleSystem'

const gameStore = useGameStore()
const error = ref('')
const info = ref('')
const codes = ref<string[]>([])

const styles = {
  panel: createPanelStyle(),
  head: { display: 'flex', justifyContent: 'space-between', marginBottom: '1.5rem', borderBottom: `1px solid ${Theme.colors.border}`, paddingBottom: '1rem' },
  title: { margin: 0, fontSize: '1.6rem', color: Theme.colors.primary, letterSpacing: '0.18em' },
  subtitle: { margin: '0.3rem 0 0', color: Theme.colors.textMuted, fontSize: '0.85rem' },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '0.6rem' },
  cheatBtn: { ...btnStyle(), padding: '0.7rem', fontSize: '0.8rem', textAlign: 'left' as const },
  btn: btnStyle(),
  empty: { color: Theme.colors.textMuted, fontStyle: 'italic' as const, marginTop: '0.5rem' },
  error: { color: Theme.colors.danger, marginBottom: '0.5rem' },
  info: { color: Theme.colors.ok, marginBottom: '0.5rem' },
}

async function reload() {
  error.value = ''
  info.value = ''
  if (!gameStore.gameId) return
  try {
    codes.value = await api.cheat.codes(gameStore.gameId)
  } catch (err: any) {
    error.value = err.message
  }
}

async function apply(code: string) {
  try {
    const res = await gameStore.applyCheat(code)
    info.value = res?.message || `Cheat ${code} aplicado`
  } catch (err: any) {
    error.value = err.message
  }
}

onMounted(reload)
</script>
