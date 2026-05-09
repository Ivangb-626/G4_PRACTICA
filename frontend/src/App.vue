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
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from './store/authStore'
import { useGameStore } from './store/gameStore'
import { useUIStore } from './store/uiStore'
import TopBar from './views/TopBar.vue'

const auth = useAuthStore()
const gameStore = useGameStore()
const uiStore = useUIStore()
const route = useRoute()
const router = useRouter()

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
  const targetTag = (e.target as HTMLElement).tagName
  const typing = ['INPUT', 'TEXTAREA', 'SELECT'].includes(targetTag)
  if (typing && e.key !== 'Escape') return

  if (e.key === '?' || e.key.toUpperCase() === 'H') {
    e.preventDefault()
    uiStore.toggleShortcuts()
    window.dispatchEvent(new CustomEvent('ux:toggle-help'))
    return
  }

  if (e.key === 'Escape') {
    uiStore.closeEventLog()
    uiStore.closeShortcuts()
    window.dispatchEvent(new CustomEvent('ux:escape'))
    return
  }

  if (!gameStore.gameId) return

  const gamePath = (segment: string) => `/game/${gameStore.gameId}/${segment}`

  switch (e.key.toUpperCase()) {
    case 'B':
    case 'BACKSPACE':
      e.preventDefault()
      router.back()
      break
    case 'M':
      e.preventDefault()
      router.push(gamePath('galaxy'))
      break
    case 'F':
      e.preventDefault()
      router.push(gamePath('fleets'))
      break
    case 'C':
      e.preventDefault()
      window.dispatchEvent(new CustomEvent('ux:open-colonies'))
      break
    case 'R':
      e.preventDefault()
      router.push(gamePath('tech'))
      break
    case 'S':
      e.preventDefault()
      router.push(gamePath('ships'))
      break
    case 'D':
      e.preventDefault()
      router.push(gamePath('diplomacy'))
      break
    case 'E':
      e.preventDefault()
      router.push(gamePath('espionage'))
      break
    case 'L':
      e.preventDefault()
      router.push(gamePath('leaders'))
      break
    case 'O':
      e.preventDefault()
      uiStore.openEventLog()
      break
    case 'T':
      e.preventDefault()
      window.dispatchEvent(new CustomEvent('ux:request-end-turn'))
      break
    case '1':
      uiStore.setGameSpeed('lenta')
      break
    case '2':
      uiStore.setGameSpeed('normal')
      break
    case '3':
      uiStore.setGameSpeed('rapida')
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
