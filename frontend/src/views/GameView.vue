<template>
  <div class="game-view">
    <header class="hud">
      <div>
        <h2>Partida {{ gameId }}</h2>
        <p class="turn" v-if="gameState">Turno {{ gameState.turn }}</p>
      </div>
      <div class="hud-actions">
        <button class="btn" @click="reloadGame" :disabled="loading">{{ loading ? 'Cargando...' : 'Recargar' }}</button>
        <button class="btn primary" @click="endTurn" :disabled="endingTurn">{{ endingTurn ? 'Procesando...' : 'End Turn' }}</button>
      </div>
    </header>

    <nav class="tabs">
      <router-link :to="`/game/${gameId}/galaxy`">Galaxy</router-link>
      <router-link :to="`/game/${gameId}/tech`">Tech</router-link>
      <router-link :to="`/game/${gameId}/fleets`">Fleets</router-link>
      <router-link :to="`/game/${gameId}/diplomacy`">Diplomacia</router-link>
    </nav>

    <p v-if="error" class="error">{{ error }}</p>

    <router-view />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../services/api'

const route = useRoute()
const gameId = computed(() => route.params.id as string)

const gameState = ref<any | null>(null)
const loading = ref(false)
const endingTurn = ref(false)
const error = ref('')

async function reloadGame() {
  loading.value = true
  error.value = ''
  try {
    const res = await api.loadGame(gameId.value)
    gameState.value = res.game_state || null
  } catch (e) {
    console.error(e)
    const err = e as Error
    error.value = err.message || 'No se pudo cargar la partida.'
  } finally {
    loading.value = false
  }
}

async function endTurn() {
  endingTurn.value = true
  error.value = ''
  try {
    await api.endTurn(gameId.value)
    await reloadGame()
  } catch (e) {
    console.error(e)
    const err = e as Error
    error.value = err.message || 'No se pudo finalizar el turno.'
  } finally {
    endingTurn.value = false
  }
}

onMounted(async () => {
  await reloadGame()
})
</script>

<style scoped>
.game-view {
  color: var(--text);
  border: 1px solid var(--panel-border);
  background: var(--panel);
  border-radius: 10px;
  box-shadow: var(--shadow-neon);
  padding: 0.9rem;
}
.hud {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}
.turn {
  margin-top: 0.25rem;
  color: var(--text-muted);
}
.hud-actions {
  display: flex;
  gap: 0.5rem;
}
.tabs {
  margin: 0.8rem 0 1rem;
  display: flex;
  gap: 0.8rem;
  flex-wrap: wrap;
}
.tabs a {
  color: var(--text-muted);
  text-decoration: none;
  border-bottom: 1px solid transparent;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  font-size: 0.78rem;
}
.tabs a.router-link-active {
  color: var(--primary-strong);
  border-bottom-color: var(--primary-strong);
}
.btn {
  border: 1px solid var(--primary);
  background: linear-gradient(180deg, rgba(79, 180, 255, 0.2), rgba(79, 180, 255, 0.05));
  color: var(--text);
  padding: 0.4rem 0.7rem;
  border-radius: 6px;
  cursor: pointer;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-size: 0.72rem;
}
.btn:hover {
  border-color: var(--primary-strong);
  box-shadow: 0 0 0.65rem rgba(103, 240, 255, 0.45);
}
.btn:disabled {
  opacity: 0.6;
  cursor: default;
}
.btn.primary {
  background: linear-gradient(180deg, rgba(79, 180, 255, 0.4), rgba(79, 180, 255, 0.18));
}
.btn.primary:hover {
  background: linear-gradient(180deg, rgba(103, 240, 255, 0.45), rgba(79, 180, 255, 0.22));
}
.error {
  color: var(--danger);
}
</style>
