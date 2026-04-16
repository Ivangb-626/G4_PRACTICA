<template>
  <section class="panel">
    <header class="head">
      <h3>Fleet Manager</h3>
      <button class="btn" @click="loadFleets" :disabled="loading">{{ loading ? 'Cargando...' : 'Recargar' }}</button>
    </header>
    <p v-if="error" class="error">{{ error }}</p>
    <table v-if="fleets.length">
      <thead>
        <tr>
          <th>Flota</th>
          <th>Sistema actual</th>
          <th>Destino</th>
          <th>ETA</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="f in fleets" :key="f.id">
          <td>{{ f.name || f.id }}</td>
          <td>{{ f.star_system_id || '—' }}</td>
          <td>{{ f.destination || '—' }}</td>
          <td>{{ f.eta_turns ?? '—' }}</td>
        </tr>
      </tbody>
    </table>
    <p v-else-if="!loading">No hay flotas disponibles.</p>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../services/api'

const route = useRoute()
const gameId = route.params.id as string
const loading = ref(false)
const error = ref('')
const fleets = ref<any[]>([])

async function loadFleets() {
  loading.value = true
  error.value = ''
  try {
    const res = await api.loadGame(gameId)
    fleets.value = res?.game_state?.player?.fleets || []
  } catch (e) {
    const err = e as Error
    error.value = err.message || 'No se pudieron cargar las flotas.'
    fleets.value = []
  } finally {
    loading.value = false
  }
}

onMounted(loadFleets)
</script>

<style scoped>
.panel { border: 1px solid var(--panel-border); border-radius: 8px; padding: 0.8rem; background: rgba(6, 13, 34, 0.5); color: var(--text); box-shadow: var(--shadow-neon); }
.head { display: flex; justify-content: space-between; align-items: center; }
.btn { border: 1px solid var(--primary); background: linear-gradient(180deg, rgba(79, 180, 255, 0.2), rgba(79, 180, 255, 0.05)); color: var(--text); border-radius: 6px; padding: 0.3rem 0.6rem; cursor: pointer; text-transform: uppercase; letter-spacing: 0.06em; font-size: 0.72rem; }
.btn:hover { border-color: var(--primary-strong); box-shadow: 0 0 0.65rem rgba(103, 240, 255, 0.45); }
table { width: 100%; border-collapse: collapse; margin-top: 0.6rem; }
th, td { text-align: left; padding: 0.45rem; border-bottom: 1px solid rgba(89, 170, 255, 0.24); }
th { color: var(--primary-strong); text-transform: uppercase; letter-spacing: 0.06em; font-size: 0.74rem; }
.error { color: var(--danger); }
</style>
