<template>
  <div id="app">
    <header class="app-header retro-panel">
      <h1 class="brand">MasterDeHostias</h1>
      <nav>
        <router-link v-if="!isLoggedIn" to="/login">Login</router-link>
        <router-link v-if="!isLoggedIn" to="/register">Registro</router-link>
        <router-link v-if="isLoggedIn" to="/dashboard">Dashboard</router-link>
        <button v-if="isLoggedIn" class="logout-btn retro-btn retro-btn-danger" @click="onLogout">
          Cerrar sesión
        </button>
      </nav>
    </header>
    <main>
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from './store/authStore'

const auth = useAuthStore()
const router = useRouter()
const isLoggedIn = computed(() => Boolean(auth.token))

function onLogout() {
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
#app {
  min-height: 100vh;
  color: var(--text);
}
.app-header {
  display: flex;
  gap: 16px;
  align-items: center;
  justify-content: space-between;
  margin: 0.8rem;
  padding: 0.75rem 1rem;
}
.brand {
  margin: 0;
  font-size: 1.35rem;
  color: var(--primary-strong);
  text-transform: uppercase;
  letter-spacing: 0.12em;
  text-shadow: 0 0 0.8rem rgba(103, 240, 255, 0.5);
}
nav > * {
  margin-right: 0.9rem;
  color: var(--text-muted);
  text-decoration: none;
  text-transform: uppercase;
  font-size: 0.8rem;
  letter-spacing: 0.09em;
  padding-bottom: 0.2rem;
  border-bottom: 1px solid transparent;
}
.logout-btn {
  margin-right: 0;
}
nav > .router-link-active {
  color: var(--primary-strong);
  border-bottom-color: var(--primary-strong);
}
main {
  padding: 0.8rem;
}
</style>
