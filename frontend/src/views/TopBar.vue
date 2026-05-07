<template>
  <header class="topbar">
    <div class="brand" @click="goDashboard">MASTER DE HOSTIAS</div>

    <nav class="links">
      <button class="topbar-btn" type="button" @click="toggleGames">
        PARTIDAS ({{ gameStore.games?.length || 0 }})
      </button>
      <button class="topbar-btn" type="button" @click="saveGame" :disabled="!gameStore.gameId || saving">
        {{ saving ? 'GUARDANDO...' : 'GUARDAR' }}
      </button>
      <button class="topbar-btn" type="button" @click="goDashboard">DASHBOARD</button>
      <span class="user" v-if="auth.username">{{ auth.username.toUpperCase() }}</span>
      <button class="topbar-btn danger" type="button" @click="logout">CERRAR SESION</button>
    </nav>

    <transition name="fade">
      <aside v-if="gamesOpen" class="games-panel">
        <header class="games-head">
          <strong>Partidas guardadas</strong>
          <button class="close-btn" type="button" @click="gamesOpen = false">×</button>
        </header>
        <ul class="games-list" v-if="gameStore.games?.length">
          <li v-for="g in gameStore.games" :key="g.game_id">
            <button class="game-row" type="button" @click="openGame(g.game_id)">
              <span class="game-name">{{ g.name }}</span>
              <span class="game-meta">T{{ g.turn || 1 }} · {{ g.player_race || '?' }}</span>
            </button>
          </li>
        </ul>
        <p v-else class="empty">Sin partidas guardadas.</p>
        <p v-if="message" class="msg">{{ message }}</p>
      </aside>
    </transition>
  </header>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useGameStore } from '../store/gameStore'
import { useAuthStore } from '../store/authStore'

const router = useRouter()
const gameStore = useGameStore()
const auth = useAuthStore()

const gamesOpen = ref(false)
const saving = ref(false)
const message = ref('')

async function refreshGames() {
  try {
    await gameStore.fetchGames()
  } catch {
    /* ignore */
  }
}

async function toggleGames() {
  gamesOpen.value = !gamesOpen.value
  if (gamesOpen.value) await refreshGames()
}

async function openGame(id: string) {
  gamesOpen.value = false
  message.value = ''
  await gameStore.loadGame(id)
  router.push(`/game/${id}/galaxy`)
}

async function saveGame() {
  if (!gameStore.gameId) return
  saving.value = true
  message.value = ''
  try {
    // Backend persists state on every action; reloading from server confirms persistence.
    await gameStore.loadGame(gameStore.gameId)
    message.value = 'Partida guardada'
    gamesOpen.value = true
    await refreshGames()
  } catch (e: any) {
    message.value = e?.message || 'No se pudo guardar'
  } finally {
    saving.value = false
  }
}

function goDashboard() {
  router.push('/dashboard')
}

function logout() {
  if (!confirm('Cerrar sesion?')) return
  gameStore.logout()
  router.push('/login')
}

onMounted(refreshGames)
</script>

<style scoped>
.topbar {
  position: sticky;
  top: 0;
  z-index: 80;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.55rem 1rem;
  background: linear-gradient(180deg, rgba(8, 17, 36, 0.95), rgba(7, 15, 36, 0.92));
  border-bottom: 1px solid rgba(0, 255, 255, 0.35);
  box-shadow: 0 2px 12px rgba(0, 255, 255, 0.12);
  backdrop-filter: blur(6px);
  font-family: monospace;
  position: relative;
}
.brand {
  font-weight: bold;
  color: #44ee88;
  letter-spacing: 0.18em;
  cursor: pointer;
  text-shadow: 0 0 8px rgba(68, 238, 136, 0.4);
}
.links {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}
.topbar-btn {
  background: transparent;
  color: #00ffff;
  border: 1px solid #00ffff;
  padding: 0.35rem 0.7rem;
  font-size: 0.75rem;
  letter-spacing: 0.06em;
  cursor: pointer;
  font-family: monospace;
  text-transform: uppercase;
  transition: background 0.15s, color 0.15s;
}
.topbar-btn:hover:not(:disabled) {
  background: #00ffff;
  color: #000;
}
.topbar-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.topbar-btn.danger {
  border-color: #ff5577;
  color: #ff5577;
}
.topbar-btn.danger:hover {
  background: #ff5577;
  color: #000;
}
.user {
  color: #aaaacc;
  font-size: 0.8rem;
  letter-spacing: 0.08em;
  padding: 0 0.5rem;
}
.games-panel {
  position: absolute;
  top: 100%;
  right: 1rem;
  margin-top: 0.4rem;
  width: 280px;
  background: #0a1326;
  border: 1px solid #00ffff;
  border-radius: 6px;
  padding: 0.6rem 0.7rem;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.6);
  z-index: 90;
}
.games-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #88ff88;
  margin-bottom: 0.5rem;
  border-bottom: 1px solid rgba(0, 255, 255, 0.25);
  padding-bottom: 0.3rem;
}
.close-btn {
  background: transparent;
  color: #aaaacc;
  border: none;
  font-size: 1.1rem;
  cursor: pointer;
}
.games-list {
  list-style: none;
  padding: 0;
  margin: 0;
  max-height: 300px;
  overflow-y: auto;
}
.game-row {
  width: 100%;
  display: flex;
  justify-content: space-between;
  background: transparent;
  color: #cfffd4;
  border: 1px solid rgba(0, 255, 255, 0.18);
  padding: 0.35rem 0.5rem;
  margin-bottom: 0.3rem;
  font-family: monospace;
  font-size: 0.78rem;
  cursor: pointer;
  text-align: left;
  transition: background 0.15s;
}
.game-row:hover {
  background: rgba(0, 255, 255, 0.08);
}
.game-name {
  color: #fff;
}
.game-meta {
  color: #aaaacc;
  font-size: 0.7rem;
}
.empty {
  color: #aaaacc;
  font-style: italic;
  margin: 0.3rem 0;
  font-size: 0.8rem;
}
.msg {
  color: #88ff88;
  font-size: 0.75rem;
  margin: 0.4rem 0 0;
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
