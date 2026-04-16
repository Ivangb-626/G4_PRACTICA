<template>
  <section class="auth-wrap">
    <div class="auth-card retro-panel">
      <h2>Registro</h2>
      <p class="subtitle">Crea tu comandante y entra a la galaxia.</p>
      <form @submit.prevent="onSubmit" class="auth-form">
        <label>Usuario<input class="retro-input" v-model="username" required /></label>
        <label>Email<input class="retro-input" type="email" v-model="email" required /></label>
        <label>Contraseña<input class="retro-input" type="password" v-model="password" required /></label>
        <label>Confirmar contraseña<input class="retro-input" type="password" v-model="passwordCheck" required /></label>
        <button class="retro-btn" type="submit">Registrar</button>
      </form>
    </div>
    <p v-if="error" class="error">{{ error }}</p>
    <p class="help">¿Ya tienes cuenta? <router-link to="/login">Inicia sesión</router-link></p>
  </section>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../services/api'
import { useAuthStore } from '../store/authStore'

const username = ref('')
const email = ref('')
const password = ref('')
const passwordCheck = ref('')
const error = ref('')
const router = useRouter()
const auth = useAuthStore()

async function onSubmit() {
  const cleanUsername = username.value.trim()
  const cleanEmail = email.value.trim()
  if (!/^[A-Za-z0-9_-]{3,30}$/.test(cleanUsername)) {
    error.value = 'Usuario inválido: usa 3-30 caracteres (letras, números, _ o -).'
    return
  }
  if (password.value.length < 8) {
    error.value = 'La contraseña debe tener al menos 8 caracteres.'
    return
  }
  if (password.value !== passwordCheck.value) {
    error.value = 'Las contraseñas no coinciden.'
    return
  }

  try {
    const res = await api.register(cleanUsername, cleanEmail, password.value)
    auth.setAuth(res.token, cleanUsername)
    router.push('/dashboard')
  } catch (e: any) {
    error.value = e.message || 'Error de registro'
  }
}
</script>

<style scoped>
.auth-wrap {
  max-width: 480px;
  margin: 6vh auto 0;
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
