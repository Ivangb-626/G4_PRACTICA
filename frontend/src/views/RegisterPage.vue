<template>
  <section>
    <h2>Registro</h2>
    <form @submit.prevent="onSubmit">
      <label>Usuario<input v-model="username" required /></label>
      <label>Email<input type="email" v-model="email" required /></label>
      <label>Contraseña<input type="password" v-model="password" required /></label>
      <label>Confirmar contraseña<input type="password" v-model="passwordCheck" required /></label>
      <button type="submit">Registrar</button>
    </form>
    <p v-if="error" class="error">{{ error }}</p>
  </section>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../services/api'

const username = ref('')
const email = ref('')
const password = ref('')
const passwordCheck = ref('')
const error = ref('')
const router = useRouter()

async function onSubmit() {
  if (password.value !== passwordCheck.value) {
    error.value = 'Las contraseñas no coinciden.'
    return
  }

  try {
    const res = await api.register(username.value, email.value, password.value)
    localStorage.setItem('token', res.token)
    router.push('/dashboard')
  } catch (e: any) {
    error.value = e.message || 'Error de registro'
  }
}
</script>

<style scoped>
.error { color: #ff7f7f; }
</style>
