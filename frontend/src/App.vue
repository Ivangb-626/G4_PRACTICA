<template>
  <div id="app-shell">
    <header class="app-header retro-panel">
      <div>
        <p class="eyebrow">Galactic Command</p>
        <h1 class="brand">MasterDeHostias</h1>
      </div>

      <nav class="top-nav">
        <router-link v-if="!isLoggedIn" to="/login">Login</router-link>
        <router-link v-if="!isLoggedIn" to="/register">Registro</router-link>
        <router-link v-if="isLoggedIn" to="/dashboard">Dashboard</router-link>
        <span v-if="isLoggedIn" class="user-chip">{{ username || 'Commander' }}</span>
        <button v-if="isLoggedIn" class="retro-btn retro-btn-danger" type="button" @click="logout">
          Cerrar sesion
        </button>
      </nav>
    </header>

    <main class="page">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { useAuth } from './types/useAuth'

const { isLoggedIn, logout, username } = useAuth()
</script>

<style scoped>
#app-shell {
  min-height: 100vh;
  color: var(--text);
}

.app-header {
  margin: 0.8rem;
  padding: 0.85rem 1rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.eyebrow {
  margin: 0 0 0.25rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.18em;
  font-size: 0.68rem;
}

.brand {
  margin: 0;
  color: var(--primary-strong);
  text-transform: uppercase;
  letter-spacing: 0.14em;
  text-shadow: 0 0 0.8rem rgba(103, 240, 255, 0.45);
}

.top-nav {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.top-nav a {
  color: var(--text-muted);
  text-decoration: none;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 0.78rem;
  padding-bottom: 0.15rem;
  border-bottom: 1px solid transparent;
}

.top-nav a.router-link-active {
  color: var(--primary-strong);
  border-bottom-color: var(--primary-strong);
}

.user-chip {
  padding: 0.3rem 0.65rem;
  border: 1px solid rgba(112, 166, 214, 0.55);
  border-radius: 999px;
  background: rgba(7, 15, 36, 0.7);
  color: var(--text);
  font-size: 0.78rem;
}

.page {
  padding: 0 0.8rem 0.8rem;
}
</style>
