<template>
  <section class="diplomacy-panel">
    <div class="diplomacy-header">
      <h3>Diplomacia</h3>
      <button class="btn" @click="loadDiplomacy" :disabled="diplomacyLoading">
        {{ diplomacyLoading ? 'Actualizando...' : 'Actualizar' }}
      </button>
    </div>

    <p v-if="diplomacyMessage" class="message">{{ diplomacyMessage }}</p>
    <p v-if="error" class="error">{{ error }}</p>

    <table v-if="diplomacyRows.length">
      <thead>
        <tr>
          <th>Facción</th>
          <th>Relación</th>
          <th>Tratados</th>
          <th>Proponer tratado</th>
          <th>Guerra</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in diplomacyRows" :key="row.targetId">
          <td>{{ row.targetId }}</td>
          <td>{{ row.value }}</td>
          <td>{{ row.treaties.length ? row.treaties.join(', ') : '—' }}</td>
          <td>
            <select v-model="selectedTreaty[row.targetId]">
              <option value="peace">peace</option>
              <option value="trade">trade</option>
              <option value="alliance">alliance</option>
            </select>
            <button class="btn" @click="proposeTreaty(row.targetId)" :disabled="pendingTarget === row.targetId">Proponer</button>
          </td>
          <td>
            <button class="btn danger" @click="declareWar(row.targetId)" :disabled="pendingTarget === row.targetId">Declarar guerra</button>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-else>No hay contactos diplomáticos disponibles todavía.</p>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../services/api'

type DiplomacyRow = {
  relationKey: string
  targetId: string
  value: number
  treaties: string[]
}

const route = useRoute()
const gameId = route.params.id as string

const diplomacyLoading = ref(false)
const error = ref('')
const diplomacyMessage = ref('')
const pendingTarget = ref('')
const diplomacyRows = ref<DiplomacyRow[]>([])
const selectedTreaty = ref<Record<string, string>>({})

function parseDiplomacy(raw: any): DiplomacyRow[] {
  const relations = raw?.relations || {}
  const rows: DiplomacyRow[] = []
  for (const [key, rel] of Object.entries(relations as Record<string, any>)) {
    const [a, b] = key.split(':')
    const targetId = a === 'player' ? b : (b === 'player' ? a : '')
    if (!targetId) continue
    rows.push({
      relationKey: key,
      targetId,
      value: rel?.value ?? 0,
      treaties: Array.isArray(rel?.treaties) ? rel.treaties : []
    })
  }
  return rows
}

async function loadDiplomacy() {
  diplomacyLoading.value = true
  error.value = ''
  try {
    const res = await api.getDiplomacy(gameId)
    diplomacyRows.value = parseDiplomacy(res)
    const next: Record<string, string> = {}
    for (const row of diplomacyRows.value) {
      next[row.targetId] = selectedTreaty.value[row.targetId] || 'trade'
    }
    selectedTreaty.value = next
  } catch (e) {
    const err = e as Error
    error.value = err.message || 'No se pudo cargar diplomacia.'
  } finally {
    diplomacyLoading.value = false
  }
}

async function proposeTreaty(target: string) {
  pendingTarget.value = target
  diplomacyMessage.value = ''
  error.value = ''
  try {
    const treaty = selectedTreaty.value[target] || 'trade'
    const res = await api.proposeTreaty(gameId, target, treaty)
    diplomacyMessage.value = res?.message || 'Propuesta enviada.'
    await loadDiplomacy()
  } catch (e) {
    const err = e as Error
    error.value = err.message || 'No se pudo proponer el tratado.'
  } finally {
    pendingTarget.value = ''
  }
}

async function declareWar(target: string) {
  if (!confirm(`¿Declarar guerra a ${target}?`)) return
  pendingTarget.value = target
  diplomacyMessage.value = ''
  error.value = ''
  try {
    const res = await api.declareWar(gameId, target)
    diplomacyMessage.value = res?.message || 'Guerra declarada.'
    await loadDiplomacy()
  } catch (e) {
    const err = e as Error
    error.value = err.message || 'No se pudo declarar la guerra.'
  } finally {
    pendingTarget.value = ''
  }
}

onMounted(loadDiplomacy)
</script>

<style scoped>
.diplomacy-panel {
  border: 1px solid var(--panel-border);
  background: rgba(6, 13, 34, 0.5);
  border-radius: 8px;
  padding: 0.8rem;
  margin-bottom: 1rem;
}
.diplomacy-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.6rem;
}
table {
  width: 100%;
  border-collapse: collapse;
}
th, td {
  text-align: left;
  padding: 0.55rem;
  border-bottom: 1px solid rgba(89, 170, 255, 0.24);
}
select {
  margin-right: 0.4rem;
  background: rgba(7, 15, 36, 0.8);
  color: var(--text);
  border: 1px solid rgba(112, 166, 214, 0.65);
  border-radius: 6px;
  padding: 0.25rem;
}
.btn {
  border: 1px solid var(--primary);
  background: linear-gradient(180deg, rgba(79, 180, 255, 0.2), rgba(79, 180, 255, 0.05));
  color: var(--text);
  padding: 0.4rem 0.7rem;
  border-radius: 6px;
  cursor: pointer;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-size: 0.72rem;
}
.btn:hover {
  border-color: var(--primary-strong);
  box-shadow: 0 0 0.65rem rgba(103, 240, 255, 0.45);
}
.btn:disabled {
  opacity: 0.6;
  cursor: default;
}
.btn.danger {
  border-color: var(--danger);
  color: #ffdbe3;
}
.btn.danger:hover {
  background: rgba(255, 107, 138, 0.14);
  box-shadow: 0 0 0.65rem rgba(255, 107, 138, 0.4);
}
.message {
  color: var(--ok);
  margin: 0 0 0.6rem;
}
.error {
  color: var(--danger);
}
</style>
