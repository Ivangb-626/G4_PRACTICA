<template>
  <div id="app">
    <header class="app-header">
      <h1>MasterDeHostias</h1>
      <nav>
        <router-link to="/login">Login</router-link>
        <router-link to="/register">Registro</router-link>
        <router-link to="/dashboard">Dashboard</router-link>
      </nav>
    </header>
    <main>
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts"></script>

<style scoped>
#app {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  color: #d1e9ff;
  background: radial-gradient(circle at 50% 0%, #020617 0%, #060b20 90%);
  min-height: 100vh;
}
.app-header {
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid #1c3a85;
}
.app-header h1 {
  margin: 0;
  font-size: 1.5rem;
  color: #00d4ff;
}
nav > * {
  margin-right: 0.8rem;
  color: #a0b9ff;
}
main {
  padding: 1rem;
}
</style>
