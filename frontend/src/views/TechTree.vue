<template>
  <section class="retro-panel tech-panel">
    <header class="panel-head">
      <div>
        <h3>Arbol tecnologico</h3>
        <p class="subtitle">
          {{ currentResearch ? `Proyecto actual: ${currentResearch.tech_id}` : 'Sin investigacion activa' }}
        </p>
      </div>
      <button class="retro-btn" type="button" @click="loadTree" :disabled="loading">
        {{ loading ? 'Cargando...' : 'Actualizar' }}
      </button>
    </header>

    <p v-if="error" class="error">{{ error }}</p>

    <div class="field-list">
      <section v-for="field in fields" :key="field.field" class="field-card">
        <header class="field-head">
          <h4>{{ field.field }}</h4>
        </header>

        <div v-for="level in field.levels" :key="`${field.field}-${level.level}`" class="level-row">
          <p class="level-title">Nivel {{ level.level }}</p>

          <div class="option-grid">
            <article
              v-for="option in level.options"
              :key="option.tech_id"
              class="option-card"
              :class="option.status"
            >
              <div>
                <strong>{{ option.name }}</strong>
                <p>{{ option.description || 'Tecnologia base del campo.' }}</p>
                <small>Coste: {{ option.research_cost }} RP</small>
              </div>

              <button
                v-if="option.status === 'available'"
                class="retro-btn"
                type="button"
                @click="selectTechnology(option)"
                :disabled="selectingTechId === option.tech_id"
              >
                {{ selectingTechId === option.tech_id ? 'Seleccionando...' : 'Investigar' }}
              </button>
              <span v-else class="status-badge">{{ labelForStatus(option.status) }}</span>
            </article>
          </div>
        </div>
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../services/api'
import type { TechField, TechOption } from '../types/game'

const route = useRoute()
const gameId = String(route.params.id || '')

const fields = ref<TechField[]>([])
const currentResearch = ref<{ tech_id: string } | null>(null)
const loading = ref(false)
const selectingTechId = ref('')
const error = ref('')

function labelForStatus(status: TechOption['status']) {
  switch (status) {
    case 'researched':
      return 'Investigada'
    case 'current':
      return 'En curso'
    case 'discarded':
      return 'Descartada'
    case 'locked':
      return 'Bloqueada'
    default:
      return 'Disponible'
  }
}

async function loadTree() {
  loading.value = true
  error.value = ''
  try {
    const response = await api.getTechTree(gameId)
    fields.value = Array.isArray(response?.fields) ? response.fields : []
    currentResearch.value = response?.current_research || null
  } catch (err) {
    fields.value = []
    currentResearch.value = null
    error.value = (err as Error).message || 'No se pudo cargar el arbol tecnologico.'
  } finally {
    loading.value = false
  }
}

async function selectTechnology(option: TechOption) {
  selectingTechId.value = option.tech_id
  error.value = ''
  try {
    await api.selectResearch(gameId, {
      field: option.field,
      level: option.level,
      tech_id: option.tech_id,
    })
    await loadTree()
  } catch (err) {
    error.value = (err as Error).message || 'No se pudo seleccionar la tecnologia.'
  } finally {
    selectingTechId.value = ''
  }
}

onMounted(loadTree)
</script>

<style scoped>
.tech-panel {
  padding: 1rem;
}

.panel-head,
.field-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}

.subtitle {
  margin: 0.25rem 0 0;
  color: var(--text-muted);
}

.field-list {
  display: grid;
  gap: 1rem;
}

.field-card {
  padding: 0.9rem;
  border: 1px solid rgba(89, 170, 255, 0.2);
  border-radius: 10px;
  background: rgba(6, 13, 34, 0.58);
}

.field-head {
  margin-bottom: 0.75rem;
}

.level-row + .level-row {
  margin-top: 0.9rem;
}

.level-title {
  margin: 0 0 0.55rem;
  color: var(--primary-strong);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 0.75rem;
}

.option-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
}

.option-card {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.85rem;
  border-radius: 8px;
  border: 1px solid rgba(112, 166, 214, 0.18);
  background: rgba(7, 15, 36, 0.72);
}

.option-card p {
  margin: 0.25rem 0;
  color: var(--text-muted);
  font-size: 0.84rem;
}

.option-card.available {
  border-color: rgba(103, 240, 255, 0.35);
}

.option-card.current {
  border-color: rgba(255, 212, 71, 0.45);
}

.option-card.researched {
  border-color: rgba(141, 246, 191, 0.4);
}

.option-card.discarded {
  opacity: 0.65;
}

.status-badge {
  align-self: flex-start;
  padding: 0.25rem 0.55rem;
  border-radius: 999px;
  background: rgba(81, 99, 124, 0.5);
  font-size: 0.76rem;
  white-space: nowrap;
}

.error {
  color: var(--danger);
  margin: 0.8rem 0;
}

@media (max-width: 860px) {
  .option-grid {
    grid-template-columns: 1fr;
  }

  .option-card {
    flex-direction: column;
  }
}
</style>
