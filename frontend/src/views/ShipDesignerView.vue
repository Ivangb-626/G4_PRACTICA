<template>
  <div :style="styles.panel">
    <div :style="styles.head">
      <div>
        <h2 :style="styles.title">DISENADOR DE NAVES</h2>
        <p :style="styles.subtitle">Define cascos, armas y sistemas especiales para la flota.</p>
      </div>
      <button :style="styles.btn" @click="reload">REFRESH</button>
    </div>

    <p v-if="error" :style="styles.error">{{ error }}</p>
    <p v-if="info" :style="styles.info">{{ info }}</p>

    <div :style="styles.mainGrid">
      <!-- Designer form -->
      <div :style="styles.innerPanel">
        <h3 :style="styles.innerTitle">NUEVO DISENO</h3>

        <label :style="styles.label">NOMBRE</label>
        <input v-model="form.name" :style="styles.input" placeholder="Disenador X" />

        <label :style="styles.label">CASCO</label>
        <select v-model="form.hull" :style="styles.input">
          <option value="">selecciona casco</option>
          <template v-for="h in hulls" :key="h.type">
            <Tooltip :title="h.name" :description="h.description" :details="{ 'Espacio': h.hull_space, 'Coste': h.cost }">
              <option :value="h.type">{{ h.name }} (espacio {{ h.hull_space }}, coste {{ h.cost }})</option>
            </Tooltip>
          </template>
        </select>

        <label :style="styles.label">ARMAS</label>
        <div :style="styles.weaponPicker">
          <select v-model="weaponDraft.id" :style="styles.input">
            <option value="">arma</option>
            <optgroup v-for="(group, name) in weapons" :key="name" :label="String(name).toUpperCase()">
              <template v-for="w in group" :key="w.id">
                <Tooltip :title="w.name" :description="w.description" :details="{ 'Espacio': w.size }">
                  <option :value="w.id">{{ w.name }} ({{ w.size }} sp)</option>
                </Tooltip>
              </template>
            </optgroup>
          </select>
          <input v-model.number="weaponDraft.count" :style="styles.inputSmall" type="number" min="1" />
          <button :style="styles.btnSmall" @click="addWeapon">+</button>
        </div>
        <ul :style="styles.list">
          <li v-for="(w, i) in form.weapons" :key="i" :style="styles.listItem">
            {{ w.count }}× {{ w.id }}
            <button :style="styles.btnTiny" @click="form.weapons.splice(i, 1)">×</button>
          </li>
        </ul>

        <label :style="styles.label">SISTEMAS ESPECIALES</label>
        <div :style="styles.weaponPicker">
          <select v-model="systemDraft" :style="styles.input">
            <option value="">sistema</option>
            <template v-for="s in shipSystems" :key="s.id">
              <Tooltip :title="s.name" :description="s.description" :details="{ 'Espacio': s.size }">
                <option :value="s.id">{{ s.name }} ({{ s.size }} sp)</option>
              </Tooltip>
            </template>
          </select>
          <button :style="styles.btnSmall" @click="addSystem">+</button>
        </div>
        <ul :style="styles.list">
          <li v-for="(s, i) in form.specials" :key="i" :style="styles.listItem">
            {{ s }}
            <button :style="styles.btnTiny" @click="form.specials.splice(i, 1)">×</button>
          </li>
        </ul>

        <button :style="styles.btn" @click="createDesign">CREAR DISENO</button>
      </div>

      <!-- Existing designs -->
      <div :style="styles.innerPanel">
        <h3 :style="styles.innerTitle">DISENOS GUARDADOS</h3>
        <p v-if="!designs.length" :style="styles.empty">Aun no has creado disenos.</p>
        <div :style="styles.list">
          <div v-for="d in designs" :key="d.id" :style="styles.designCard">
            <div :style="styles.designHead">
              <strong :style="{ color: '#fff' }">{{ d.name }}</strong>
              <span :style="{ color: '#aaaacc', fontSize: '0.75rem' }">{{ d.hull }}</span>
            </div>
            <div :style="styles.designMeta">
              {{ d.size_used }}/{{ d.size_max }} sp · {{ d.cost }} BC · {{ d.command_points }} CP
            </div>
            <div :style="styles.designMeta">
              Armas: {{ (d.weapons || []).map((w: any) => `${w.count}×${w.id}`).join(', ') || 'ninguna' }}
            </div>
            <div :style="styles.designMeta">
              Sistemas: {{ (d.specials || []).join(', ') || 'ninguno' }}
            </div>
            <button :style="styles.btnDanger" @click="deleteDesign(d.id)">ELIMINAR</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useGameStore } from '../store/gameStore'
import { api } from '../api/client'
import { Theme, createPanelStyle, btnStyle } from '../styles/styleSystem'
import Tooltip from '../components/Tooltip.vue' // Import the Tooltip component
import Tooltip from '../components/Tooltip.vue' // Import the Tooltip component
import Tooltip from '../components/Tooltip.vue' // Import the Tooltip component
import Tooltip from '../components/Tooltip.vue' // Import the Tooltip component
import Tooltip from '../components/Tooltip.vue' // Import the Tooltip component
import Tooltip from '../components/Tooltip.vue' // Import the Tooltip component
import Tooltip from '../components/Tooltip.vue' // Import the Tooltip component

const gameStore = useGameStore()
const error = ref('')
const info = ref('')

const catalog = ref<any>(null)
const designs = ref<any[]>([])

const form = ref<{ name: string; hull: string; weapons: any[]; specials: string[] }>({
  name: 'Disenador X',
  hull: '',
  weapons: [],
  specials: [],
})

const weaponDraft = ref({ id: '', count: 1 })
const systemDraft = ref('')

const hulls = computed(() => catalog.value?.hulls || [])
const weapons = computed(() => catalog.value?.weapons || {})
const shipSystems = computed(() => catalog.value?.ship_systems || [])

const styles = {
  panel: createPanelStyle(),
  head: { display: 'flex', justifyContent: 'space-between', marginBottom: '1.5rem', borderBottom: `1px solid ${Theme.colors.border}`, paddingBottom: '1rem' },
  title: { margin: 0, fontSize: '1.6rem', color: Theme.colors.primary, letterSpacing: '0.18em' },
  subtitle: { margin: '0.3rem 0 0', color: Theme.colors.textMuted, fontSize: '0.85rem' },
  mainGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' },
  innerPanel: { padding: '0.9rem', backgroundColor: Theme.colors.bgDark, border: `1px solid ${Theme.colors.border}`, borderRadius: '8px' },
  innerTitle: { margin: '0 0 0.7rem', fontSize: '1rem', color: Theme.colors.secondary, letterSpacing: '0.1em' },
  label: { display: 'block', fontSize: '0.7rem', color: Theme.colors.textMuted, marginTop: '0.6rem', marginBottom: '0.2rem' },
  input: { width: '100%', backgroundColor: '#070f24', color: Theme.colors.text, border: `1px solid ${Theme.colors.primary}`, padding: '0.35rem', borderRadius: '4px', fontSize: '0.85rem' },
  inputSmall: { width: '60px', backgroundColor: '#070f24', color: Theme.colors.text, border: `1px solid ${Theme.colors.primary}`, padding: '0.35rem', borderRadius: '4px' },
  weaponPicker: { display: 'flex', gap: '0.3rem', alignItems: 'center', marginBottom: '0.4rem' },
  list: { listStyle: 'none' as const, margin: '0 0 0.6rem', padding: 0 },
  listItem: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.25rem 0.5rem', backgroundColor: '#070f24', border: '1px solid rgba(89, 170, 255, 0.2)', borderRadius: '3px', marginBottom: '0.2rem', fontSize: '0.8rem' },
  designCard: { padding: '0.6rem 0.7rem', backgroundColor: '#070f24', border: `1px solid ${Theme.colors.border}`, borderRadius: '4px', display: 'flex', flexDirection: 'column' as const, gap: '0.2rem' },
  designHead: { display: 'flex', justifyContent: 'space-between' },
  designMeta: { fontSize: '0.75rem', color: '#aaaacc' },
  btn: { ...btnStyle(), marginTop: '0.5rem' },
  btnSmall: { ...btnStyle(), padding: '0.25rem 0.5rem', fontSize: '0.75rem' },
  btnTiny: { ...btnStyle(), padding: '0 0.3rem', fontSize: '0.7rem', borderColor: Theme.colors.danger, color: Theme.colors.danger },
  btnDanger: { ...btnStyle(), padding: '0.3rem 0.5rem', fontSize: '0.7rem', borderColor: Theme.colors.danger, color: Theme.colors.danger, marginTop: '0.4rem' },
  empty: { color: Theme.colors.textMuted, fontStyle: 'italic' as const },
  error: { color: Theme.colors.danger, marginBottom: '0.5rem' },
  info: { color: Theme.colors.ok, marginBottom: '0.5rem' },
}

function addWeapon() {
  if (!weaponDraft.value.id) return
  form.value.weapons.push({ id: weaponDraft.value.id, count: weaponDraft.value.count, mods: [] })
  weaponDraft.value = { id: '', count: 1 }
}

function addSystem() {
  if (!systemDraft.value) return
  if (!form.value.specials.includes(systemDraft.value)) {
    form.value.specials.push(systemDraft.value)
  }
  systemDraft.value = ''
}

async function reload() {
  error.value = ''
  info.value = ''
  if (!gameStore.gameId) return
  try {
    catalog.value = await api.shipDesign.catalog(gameStore.gameId)
    designs.value = await api.shipDesign.list(gameStore.gameId)
  } catch (err: any) {
    error.value = err.message
  }
}

async function createDesign() {
  if (!form.value.hull) {
    error.value = 'Selecciona un casco'
    return
  }
  try {
    await api.shipDesign.create(gameStore.gameId!, {
      name: form.value.name,
      hull: form.value.hull,
      weapons: form.value.weapons,
      specials: form.value.specials,
    })
    info.value = 'Diseno guardado'
    form.value = { name: 'Disenador X', hull: '', weapons: [], specials: [] }
    await reload()
  } catch (err: any) {
    error.value = err.message
  }
}

async function deleteDesign(id: string) {
  if (!confirm('Eliminar este diseno?')) return
  try {
    await api.shipDesign.delete(gameStore.gameId!, id)
    await reload()
  } catch (err: any) {
    error.value = err.message
  }
}

onMounted(reload)
</script>
