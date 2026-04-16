<template>
  <section class="panel">
    <header class="head">
      <h3>Tech Tree</h3>
      <button class="btn" @click="loadTree" :disabled="loading">{{ loading ? 'Cargando...' : 'Recargar' }}</button>
    </header>
    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="currentTech"><strong>Investigación actual:</strong> {{ currentTech }}</p>
    <div v-for="field in fields" :key="field.field" class="field">
      <h4>{{ field.field }}</h4>
      <div v-for="level in field.levels" :key="`${field.field}-${level.level}`" class="level">
        <strong>Nivel {{ level.level }}:</strong>
        <span v-for="opt in level.options" :key="opt.tech_id" class="opt">
          {{ opt.name }} ({{ opt.status }})
        </span>
      </div>
    </div>
    <p v-if="!fields.length && !loading">No hay datos de tecnología.</p>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../services/api'

const route = useRoute()
const gameId = route.params.id as string
const loading = ref(false)
const error = ref('')
const fields = ref<any[]>([])
const currentTech = ref('')

async function loadTree() {
  loading.value = true
  error.value = ''
  try {
    const res = await api.getTechTree(gameId)
    fields.value = Array.isArray(res?.fields) ? res.fields : []
    currentTech.value = res?.current_research?.tech_id || ''
  } catch (e) {
    const err = e as Error
    error.value = err.message || 'No se pudo cargar el árbol tecnológico.'
    fields.value = []
  } finally {
    loading.value = false
  }
}

onMounted(loadTree)
</script>

<style scoped>
.panel { border: 1px solid var(--panel-border); border-radius: 8px; padding: 0.8rem; background: rgba(6, 13, 34, 0.5); color: var(--text); box-shadow: var(--shadow-neon); }
.head { display: flex; justify-content: space-between; align-items: center; }
.field { margin-top: 0.8rem; }
.level { margin-top: 0.2rem; }
.opt { margin-left: 0.5rem; color: var(--text-muted); }
.btn { border: 1px solid var(--primary); background: linear-gradient(180deg, rgba(79, 180, 255, 0.2), rgba(79, 180, 255, 0.05)); color: var(--text); border-radius: 6px; padding: 0.3rem 0.6rem; cursor: pointer; text-transform: uppercase; letter-spacing: 0.06em; font-size: 0.72rem; }
.btn:hover { border-color: var(--primary-strong); box-shadow: 0 0 0.65rem rgba(103, 240, 255, 0.45); }
.error { color: var(--danger); }
</style>
