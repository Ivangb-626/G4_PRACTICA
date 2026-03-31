<template>
  <section>
    <h2>Login</h2>
    <form @submit.prevent="onSubmit">
      <label>Usuario<input v-model="username" required /></label>
      <label>Contraseña<input type="password" v-model="password" required /></label>
      <button type="submit">Entrar</button>
    </form>
    <p v-if="error" class="error">{{ error }}</p>
  </section>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../services/api'

const username = ref('')
const password = ref('')
const error = ref('')
const router = useRouter()

async function onSubmit() {
  try {
    const res = await api.login(username.value, password.value)
    localStorage.setItem('token', res.token)
    localStorage.setItem('username', res.username)
    router.push('/dashboard')
  } catch (e: any) {
    error.value = e.message || 'Error de login'
  }
}
</script>

<style scoped>
.error { color: #ff7f7f; }
</style>
