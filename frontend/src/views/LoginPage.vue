<template>
  <section class="auth-wrap">
    <div class="auth-card retro-panel">
      <h2>Login</h2>
      <p class="subtitle">Accede al mando de tu imperio.</p>
      <form @submit.prevent="onSubmit" class="auth-form">
        <label>Usuario<input class="retro-input" v-model="username" required /></label>
        <label>Contraseña<input class="retro-input" type="password" v-model="password" required /></label>
        <button class="retro-btn" type="submit">Entrar</button>
      </form>
    </div>
    <p v-if="error" class="error">{{ error }}</p>
    <p class="help">¿No tienes cuenta? <router-link to="/register">Regístrate</router-link></p>
  </section>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../services/api'
import { useAuthStore } from '../store/authStore'

const username = ref('')
const password = ref('')
const error = ref('')
const router = useRouter()
const auth = useAuthStore()

async function onSubmit() {
  try {
    const res = await api.login(username.value, password.value)
    auth.setAuth(res.token, res.username)
    router.push('/dashboard')
  } catch (e: any) {
    error.value = e.message || 'Error de login'
  }
}
</script>

<style scoped>
.auth-wrap {
  max-width: 480px;
  margin: 7vh auto 0;
}
.auth-card {
  padding: 1rem 1.1rem;
}
.subtitle {
  margin: 0.25rem 0 0.9rem;
  color: var(--text-muted);
}
.auth-form {
  display: grid;
  gap: 0.75rem;
}
label {
  display: grid;
  gap: 0.35rem;
  color: var(--text-muted);
  font-size: 0.86rem;
}
.help {
  margin-top: 0.7rem;
  color: var(--text-muted);
}
.error {
  color: var(--danger);
  margin-top: 0.65rem;
}
</style>
