<template>
  <section class="diplomacy-panel">
    <div class="diplomacy-header">
      <h3>Diplomacia</h3>
      <div class="tabs">
        <button :class="['tab', { active: tab === 'relations' }]" @click="tab = 'relations'">Relaciones</button>
        <button :class="['tab', { active: tab === 'intel' }]" @click="tab = 'intel'">Inteligencia</button>
        <button :class="['tab', { active: tab === 'trade' }]" @click="tab = 'trade'">Tech Trade</button>
        <button :class="['tab', { active: tab === 'gift' }]" @click="tab = 'gift'">Regalos</button>
        <button :class="['tab', { active: tab === 'demand' }]" @click="tab = 'demand'">Demandas</button>
      </div>
      <button class="btn" @click="loadAll" :disabled="loading">
        {{ loading ? 'Actualizando...' : 'Actualizar' }}
      </button>
    </div>

    <p v-if="message" class="message">{{ message }}</p>
    <p v-if="error" class="error">{{ error }}</p>

    <!-- ─── RELATIONS ─── -->
    <div v-if="tab === 'relations'">
      <table v-if="relations.length">
        <thead>
          <tr>
            <th>Facción</th>
            <th>Relación</th>
            <th>Estatus</th>
            <th>Tratados</th>
            <th>Tributo</th>
            <th>Paciencia</th>
            <th>Proponer</th>
            <th>Guerra</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in relations" :key="row.other">
            <td>{{ row.other }}</td>
            <td :class="relationClass(row.value)">{{ row.value }}</td>
            <td>{{ statusLabel(row.status) }}</td>
            <td>{{ row.treaties.length ? row.treaties.join(', ') : '—' }}</td>
            <td>{{ row.tribute_percent > 0 ? `${row.tribute_percent}% / ${row.tribute_turns_left}t` : '—' }}</td>
            <td>{{ row.patience }}/100</td>
            <td>
              <select v-model="selectedTreaty[row.other]">
                <option value="peace">peace</option>
                <option value="non_aggression">non-agg.</option>
                <option value="trade">trade</option>
                <option value="research">research</option>
                <option value="alliance">alliance</option>
              </select>
              <button class="btn" @click="proposeTreaty(row.other)" :disabled="pending === row.other">Proponer</button>
            </td>
            <td>
              <button class="btn danger" @click="declareWar(row.other)" :disabled="pending === row.other">Guerra</button>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-else>No hay contactos diplomáticos disponibles todavía.</p>
    </div>

    <!-- ─── INTELLIGENCE / SCOUTING (DIPLOMACY sec 14) ─── -->
    <div v-if="tab === 'intel'" class="intel-section">
      <p class="hint">La diplomacia revela inteligencia según el nivel de relación. Abrir diálogo refresca los datos.</p>
      <div class="intel-controls">
        <select v-model="intelTarget">
          <option value="">— elige facción —</option>
          <option v-for="r in relations" :key="r.other" :value="r.other">{{ r.other }}</option>
        </select>
        <button class="btn" @click="fetchIntel" :disabled="!intelTarget">Ver inteligencia</button>
        <button class="btn" @click="openDialogue" :disabled="!intelTarget">Abrir diálogo</button>
      </div>
      <div v-if="intel" class="intel-card">
        <div class="intel-row"><strong>Objetivo:</strong> {{ intel.target }}</div>
        <div class="intel-row"><strong>Raza:</strong> {{ intel.race }}</div>
        <div class="intel-row"><strong>Estatus:</strong> {{ statusLabel(intel.relation_status) }}</div>
        <div class="intel-row"><strong>Frescura:</strong> <span :class="`freshness-${intel.freshness}`">{{ intel.freshness }}</span></div>
        <div class="intel-row"><strong>Último contacto:</strong> turno {{ intel.last_contact_turn }}</div>
        <div v-if="intel.population_total !== undefined" class="intel-row">
          <strong>Población total:</strong> {{ intel.population_total }}
        </div>
        <div v-if="intel.fleet_count !== undefined" class="intel-row">
          <strong>Flotas:</strong> {{ intel.fleet_count }} ({{ intel.fleet_power }} poder)
        </div>
        <div v-if="intel.current_research" class="intel-row">
          <strong>Investigación actual:</strong> {{ JSON.stringify(intel.current_research) }}
        </div>
        <div v-if="intel.known_techs?.length" class="intel-row">
          <strong>Tecnologías conocidas:</strong> {{ intel.known_techs.join(', ') }}
        </div>
        <div v-if="intel.full_visibility" class="intel-row alliance-banner">★ Visibilidad total (alianza)</div>
      </div>
    </div>

    <!-- ─── TECH TRADE (DIPLOMACY sec 3) ─── -->
    <div v-if="tab === 'trade'" class="trade-section">
      <div class="form-row">
        <label>Objetivo
          <select v-model="tradeTarget">
            <option value="">— elige facción —</option>
            <option v-for="r in relations" :key="r.other" :value="r.other">{{ r.other }}</option>
          </select>
        </label>
        <label>Mi tecnología (ofrezco)
          <input v-model="tradeOffered" placeholder="ej. physics_lvl2" />
        </label>
        <label>Su tecnología (pido)
          <input v-model="tradeRequested" placeholder="ej. computers_lvl2" />
        </label>
        <button class="btn" @click="tradeTech" :disabled="!tradeTarget || !tradeOffered || !tradeRequested">Intercambiar</button>
      </div>
    </div>

    <!-- ─── GIFTS (DIPLOMACY sec 8) ─── -->
    <div v-if="tab === 'gift'" class="gift-section">
      <div class="form-row">
        <label>Objetivo
          <select v-model="giftTarget">
            <option value="">— elige facción —</option>
            <option v-for="r in relations" :key="r.other" :value="r.other">{{ r.other }}</option>
          </select>
        </label>
        <label>Tipo
          <select v-model="giftType">
            <option value="gift_money">Dinero</option>
            <option value="gift_tech">Tecnología</option>
          </select>
        </label>
        <label v-if="giftType === 'gift_money'">Cantidad (BC)
          <input v-model.number="giftAmount" type="number" min="1" />
        </label>
        <label v-else>Tech ID
          <input v-model="giftTechId" placeholder="ej. physics_lvl2" />
        </label>
        <button class="btn" @click="giveGift" :disabled="!giftTarget">Regalar</button>
      </div>
    </div>

    <!-- ─── DEMANDS (DIPLOMACY sec 7 & 12) ─── -->
    <div v-if="tab === 'demand'" class="demand-section">
      <p class="hint">Las demandas se basan en el ratio de poder de flota. Riesgo de guerra si la facción se ofende.</p>
      <div class="form-row">
        <label>Objetivo
          <select v-model="demandTarget">
            <option value="">— elige facción —</option>
            <option v-for="r in relations" :key="r.other" :value="r.other">{{ r.other }}</option>
          </select>
        </label>
        <label>Tipo de demanda
          <select v-model="demandType">
            <optgroup label="Leves">
              <option value="stop_spying">Detener espionaje</option>
              <option value="remove_fleet">Retirar flota</option>
            </optgroup>
            <optgroup label="Moderadas">
              <option value="demand_money">Dinero</option>
              <option value="demand_tech">Tecnología</option>
              <option value="demand_tribute_5">Tributo 5%</option>
            </optgroup>
            <optgroup label="Severas">
              <option value="demand_tribute_10">Tributo 10%</option>
              <option value="demand_system">Cesión de sistema</option>
            </optgroup>
          </select>
        </label>
        <label v-if="demandType === 'demand_money'">Cantidad
          <input v-model.number="demandAmount" type="number" min="1" />
        </label>
        <label v-if="demandType === 'demand_tech'">Tech ID
          <input v-model="demandTechId" placeholder="ej. physics_lvl2" />
        </label>
        <button class="btn danger" @click="makeDemand" :disabled="!demandTarget || !demandType">Exigir</button>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../services/api'

type Relation = {
  other: string
  value: number
  status: string
  treaties: string[]
  active_treaties: any[]
  patience: number
  tribute_percent: number
  tribute_turns_left: number
  last_contact_turn: number
  last_scouted_turn: number
}

type Intel = {
  target: string
  race: string
  relation_status: string
  freshness: 'fresh' | 'aging' | 'stale'
  last_contact_turn: number
  last_scouted_turn: number
  active_treaties?: string[]
  population_total?: number
  known_systems?: string[]
  known_techs?: string[]
  fleet_count?: number
  fleet_power?: number
  current_research?: any
  all_techs?: string[]
  full_visibility?: boolean
}

const route = useRoute()
const gameId = route.params.id as string

const tab = ref<'relations' | 'intel' | 'trade' | 'gift' | 'demand'>('relations')
const loading = ref(false)
const error = ref('')
const message = ref('')
const pending = ref('')
const relations = ref<Relation[]>([])
const selectedTreaty = ref<Record<string, string>>({})

// Intel state
const intelTarget = ref('')
const intel = ref<Intel | null>(null)

// Trade state
const tradeTarget = ref('')
const tradeOffered = ref('')
const tradeRequested = ref('')

// Gift state
const giftTarget = ref('')
const giftType = ref<'gift_money' | 'gift_tech'>('gift_money')
const giftAmount = ref(100)
const giftTechId = ref('')

// Demand state
const demandTarget = ref('')
const demandType = ref('')
const demandAmount = ref(100)
const demandTechId = ref('')

function statusLabel(status: string) {
  return ({
    enemy_total: 'Enemistad total',
    hostile: 'Hostil',
    neutral: 'Neutral',
    friendly: 'Amistoso',
    very_friendly: 'Muy amistoso',
    loyal_ally: 'Aliado leal',
  } as Record<string, string>)[status] || status
}

function relationClass(value: number) {
  if (value <= -1) return 'rel-bad'
  if (value <= 50) return 'rel-neutral'
  if (value <= 100) return 'rel-good'
  return 'rel-great'
}

async function loadAll() {
  loading.value = true
  error.value = ''
  try {
    const res = await api.getRelations(gameId)
    relations.value = res?.relations || []
    const next: Record<string, string> = {}
    for (const r of relations.value) {
      next[r.other] = selectedTreaty.value[r.other] || 'trade'
    }
    selectedTreaty.value = next
  } catch (e) {
    error.value = (e as Error).message || 'No se pudo cargar diplomacia.'
  } finally {
    loading.value = false
  }
}

async function proposeTreaty(target: string) {
  pending.value = target
  message.value = ''
  error.value = ''
  try {
    const treaty = selectedTreaty.value[target] || 'trade'
    const res = await api.proposeTreaty(gameId, target, treaty)
    message.value = res?.message || (res?.success ? 'Aceptado.' : 'Rechazado.')
    await loadAll()
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    pending.value = ''
  }
}

async function declareWar(target: string) {
  if (!confirm(`¿Declarar guerra a ${target}?`)) return
  pending.value = target
  try {
    const res = await api.declareWar(gameId, target)
    message.value = res?.message || 'Guerra declarada.'
    await loadAll()
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    pending.value = ''
  }
}

async function fetchIntel() {
  if (!intelTarget.value) return
  error.value = ''
  try {
    const res = await api.getIntelligence(gameId, intelTarget.value)
    if (res?.success) {
      intel.value = res.intel
      message.value = 'Inteligencia obtenida.'
    } else {
      error.value = res?.reason || 'Sin información'
    }
  } catch (e) {
    error.value = (e as Error).message
  }
}

async function openDialogue() {
  if (!intelTarget.value) return
  try {
    const res = await api.openDialogue(gameId, intelTarget.value)
    if (res?.success) {
      intel.value = res.intel
      message.value = 'Diálogo abierto, inteligencia refrescada.'
    } else {
      error.value = res?.reason || 'No se pudo abrir el diálogo'
    }
  } catch (e) {
    error.value = (e as Error).message
  }
}

async function tradeTech() {
  error.value = ''
  try {
    const res = await api.tradeTech(gameId, tradeTarget.value, tradeOffered.value, tradeRequested.value)
    message.value = res?.message || (res?.success ? 'Trade aceptado' : 'Trade rechazado')
    await loadAll()
  } catch (e) {
    error.value = (e as Error).message
  }
}

async function giveGift() {
  error.value = ''
  try {
    const opts: { amount?: number; tech_id?: string } = {}
    if (giftType.value === 'gift_money') opts.amount = giftAmount.value
    else opts.tech_id = giftTechId.value
    const res = await api.giveGift(gameId, giftTarget.value, giftType.value, opts)
    message.value = res?.message || (res?.success ? 'Regalo entregado' : 'No se pudo entregar')
    await loadAll()
  } catch (e) {
    error.value = (e as Error).message
  }
}

async function makeDemand() {
  if (!confirm(`¿Exigir ${demandType.value} a ${demandTarget.value}? Puede provocar la guerra.`)) return
  error.value = ''
  try {
    const payload: Record<string, unknown> = {}
    if (demandType.value === 'demand_money') payload.amount = demandAmount.value
    if (demandType.value === 'demand_tech') payload.tech_id = demandTechId.value
    const res = await api.makeDemand(gameId, demandTarget.value, demandType.value, payload)
    message.value = res?.message || (res?.success ? 'Aceptaron' : 'Rechazaron')
    if (res?.war) error.value = '⚠ La facción te ha declarado la guerra.'
    await loadAll()
  } catch (e) {
    error.value = (e as Error).message
  }
}

onMounted(loadAll)
</script>

<style scoped>
.diplomacy-panel {
  border: 2px solid var(--panel-border);
  background: var(--panel);
  padding: 1rem;
  margin-bottom: 1rem;
  position: relative;
  box-shadow:
    0 0 0 2px var(--bg-0) inset,
    0 0 0.8rem rgba(51, 255, 102, 0.35);
}

.diplomacy-panel::before,
.diplomacy-panel::after {
  content: "";
  position: absolute;
  width: 6px;
  height: 6px;
  background: var(--primary);
  box-shadow: 0 0 0.4rem var(--primary);
}

.diplomacy-panel::before { top: -3px; left: -3px; }
.diplomacy-panel::after { bottom: -3px; right: -3px; }

.diplomacy-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.9rem;
  flex-wrap: wrap;
  gap: 0.6rem;
  border-bottom: 1px dashed var(--green-deep);
  padding-bottom: 0.6rem;
}

.diplomacy-header h3 {
  margin: 0;
}

.tabs {
  display: flex;
  gap: 0.4rem;
  flex-wrap: wrap;
}

.tab {
  font-family: var(--font-pixel);
  font-size: 0.6rem;
  letter-spacing: 0.08em;
  border: 2px solid var(--primary);
  background: var(--bg-1);
  color: var(--primary);
  padding: 0.5rem 0.8rem;
  border-radius: 0;
  cursor: pointer;
  text-transform: uppercase;
  text-shadow: 0 0 0.4rem rgba(51, 255, 102, 0.55);
  box-shadow:
    0 0 0 2px var(--bg-0),
    inset -2px -2px 0 var(--green-deep),
    inset 2px 2px 0 rgba(141, 255, 159, 0.18);
  image-rendering: pixelated;
}

.tab:hover {
  background: var(--green-deep);
  color: var(--primary-strong);
}

.tab.active {
  background: var(--primary);
  color: var(--bg-0);
  text-shadow: none;
  box-shadow:
    0 0 0 2px var(--bg-0),
    0 0 0.8rem var(--primary-strong),
    inset -2px -2px 0 var(--green-mid),
    inset 2px 2px 0 rgba(255, 255, 255, 0.4);
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.95rem;
}

th, td {
  text-align: left;
  padding: 0.55rem 0.6rem;
  border-bottom: 1px dashed var(--green-deep);
}

th {
  font-family: var(--font-pixel);
  font-size: 0.6rem;
  color: var(--primary);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  border-bottom: 2px solid var(--primary);
}

select, input {
  margin-right: 0.4rem;
  font-family: var(--font-mono);
  font-size: 1rem;
  background: var(--bg-0);
  color: var(--primary);
  border: 2px solid var(--green-mid);
  border-radius: 0;
  padding: 0.35rem 0.5rem;
  text-shadow: 0 0 0.3rem rgba(51, 255, 102, 0.4);
  box-shadow: inset 2px 2px 0 rgba(0, 0, 0, 0.6);
}

select:focus, input:focus {
  outline: none;
  border-color: var(--primary-strong);
  box-shadow:
    inset 2px 2px 0 rgba(0, 0, 0, 0.6),
    0 0 0.6rem rgba(141, 255, 159, 0.5);
}

select option {
  background: var(--bg-0);
  color: var(--primary);
}

.btn {
  font-family: var(--font-pixel);
  font-size: 0.6rem;
  letter-spacing: 0.08em;
  border: 2px solid var(--primary);
  background: var(--bg-1);
  color: var(--primary);
  padding: 0.5rem 0.8rem;
  border-radius: 0;
  cursor: pointer;
  text-transform: uppercase;
  text-shadow: 0 0 0.4rem rgba(51, 255, 102, 0.55);
  box-shadow:
    0 0 0 2px var(--bg-0),
    inset -2px -2px 0 var(--green-deep),
    inset 2px 2px 0 rgba(141, 255, 159, 0.18);
  image-rendering: pixelated;
}

.btn:hover {
  background: var(--primary);
  color: var(--bg-0);
  text-shadow: none;
  box-shadow:
    0 0 0 2px var(--bg-0),
    0 0 0.9rem var(--primary-strong),
    inset -2px -2px 0 var(--green-mid),
    inset 2px 2px 0 rgba(255, 255, 255, 0.4);
}

.btn:disabled { opacity: 0.5; cursor: not-allowed; filter: grayscale(0.4); }

.btn.danger {
  border-color: var(--danger);
  color: var(--danger);
  text-shadow: 0 0 0.4rem rgba(255, 93, 108, 0.55);
  box-shadow:
    0 0 0 2px var(--bg-0),
    inset -2px -2px 0 #4a0d15,
    inset 2px 2px 0 rgba(255, 200, 200, 0.18);
}

.btn.danger:hover {
  background: var(--danger);
  color: var(--bg-0);
  text-shadow: none;
}

.message {
  color: var(--ok);
  margin: 0 0 0.6rem;
  padding: 0.4rem 0.6rem;
  border-left: 3px solid var(--ok);
  background: rgba(141, 255, 159, 0.08);
}

.error {
  color: var(--danger);
  margin: 0 0 0.6rem;
  padding: 0.4rem 0.6rem;
  border-left: 3px solid var(--danger);
  background: rgba(255, 93, 108, 0.08);
}

.hint {
  color: var(--text-muted);
  font-size: 0.95rem;
  font-style: italic;
  margin: 0.4rem 0;
}

.form-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.7rem;
  align-items: flex-end;
  margin-top: 0.7rem;
}

.form-row label {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-family: var(--font-pixel);
  font-size: 0.55rem;
  color: var(--primary);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.form-row label input,
.form-row label select {
  font-family: var(--font-mono);
  font-size: 1rem;
  text-transform: none;
  letter-spacing: normal;
}

.intel-controls {
  display: flex;
  gap: 0.4rem;
  margin: 0.5rem 0;
  flex-wrap: wrap;
}

.intel-card {
  border: 2px solid var(--green-deep);
  border-left: 3px solid var(--primary);
  border-radius: 0;
  padding: 0.8rem;
  background: rgba(10, 30, 18, 0.7);
  margin-top: 0.6rem;
}

.intel-row {
  padding: 0.3rem 0;
  border-bottom: 1px dashed var(--green-deep);
}

.intel-row:last-child {
  border-bottom: 0;
}

.intel-row strong {
  font-family: var(--font-pixel);
  font-size: 0.6rem;
  color: var(--primary);
  letter-spacing: 0.06em;
  margin-right: 0.5rem;
}

.alliance-banner {
  color: var(--primary-strong);
  font-weight: bold;
  padding-top: 0.5rem;
  text-shadow: 0 0 0.6rem var(--primary-strong);
}

.freshness-fresh { color: var(--primary-strong); }
.freshness-aging { color: #ffd447; }
.freshness-stale { color: var(--danger); }

.rel-bad { color: var(--danger); }
.rel-neutral { color: var(--text-muted); }
.rel-good { color: var(--primary-strong); }
.rel-great {
  color: #ffd447;
  text-shadow: 0 0 0.5rem rgba(255, 212, 71, 0.7);
}
</style>
