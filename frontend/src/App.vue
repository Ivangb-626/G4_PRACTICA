<template>
  <div :style="styles.appShell">
    <TopBar v-if="auth.token && !isAuthRoute" />

    <main :style="styles.main">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from './store/authStore'
import { useGameStore } from './store/gameStore'
import { useUIStore } from './store/uiStore'
import TopBar from './views/TopBar.vue'

const auth = useAuthStore()
const gameStore = useGameStore()
const uiStore = useUIStore()
const route = useRoute()

const isAuthRoute = computed(() => ['/login', '/register'].includes(route.path))

const styles = {
  appShell: {
    minHeight: '100vh',
    backgroundColor: '#070f24',
    color: '#e0e0ff',
    fontFamily: 'monospace',
    display: 'flex',
    flexDirection: 'column' as const,
  },
  main: {
    flex: 1,
    padding: '1rem',
    overflow: 'auto',
  },
}

const handleKeyDown = (e: KeyboardEvent) => {
  if (['INPUT', 'TEXTAREA', 'SELECT'].includes((e.target as HTMLElement).tagName)) return
  if (!gameStore.gameId) return

  switch (e.key.toUpperCase()) {
    case 'T':
      gameStore.endTurn()
      break
    case 'ESCAPE':
      uiStore.closeEventLog()
      break
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeyDown)
  if (auth.token) {
    gameStore.fetchGames().catch(() => {
      /* ignore failed background refresh */
    })
  }
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
})
</script>
