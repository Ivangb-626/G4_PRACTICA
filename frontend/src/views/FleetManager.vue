<template>
  <div :style="styles.panel">
    <div :style="styles.head">
      <div>
        <h2 :style="styles.title">FLEET ADMIRALTY</h2>
        <p :style="styles.subtitle">Mando y movimiento de las flotas imperiales.</p>
      </div>
      <button :style="styles.btn" @click="reload">REFRESH</button>
    </div>

    <div :style="styles.controlRow">
      <input v-model.trim="fleetQuery" :style="styles.searchInput" type="search" placeholder="Filtrar flota, sistema o nave..." />
      <select v-model="statusFilter" :style="styles.select">
        <option value="all">TODAS</option>
        <option value="idle">EN ORBITA</option>
        <option value="moving">EN TRANSITO</option>
        <option value="colony">CON COLONIZADORA</option>
      </select>
    </div>

    <p v-if="error" :style="styles.error">{{ error }}</p>
    <p v-if="!filteredFleets.length" :style="styles.empty">No hay flotas que coincidan con el filtro.</p>

    <section v-if="selectedFleet" :style="styles.detailsPanel">
      <strong>{{ selectedFleet.name }}</strong>
      <span>{{ selectedFleetStats }}</span>
      <span v-if="selectedFleet.destination">Destino: {{ getSystemName(selectedFleet.destination) }} · ETA {{ selectedFleet.eta_turns ?? '?' }}T</span>
      <span v-else>Disponible en {{ getSystemName(selectedFleet.star_system_id) }}</span>
    </section>

    <div :style="styles.fleetGrid">
      <div
        v-for="fleet in filteredFleets"
        :key="fleet.id"
        :style="getFleetCardStyle(fleet)"
        @click="selectedFleetId = fleet.id"
      >
        <div :style="styles.cardHead">
          <div :style="{ flex: 1, minWidth: 0 }">
            <div v-if="renamingFleetId === fleet.id" :style="{ display: 'flex', gap: '0.3rem' }" @click.stop>
              <input
                v-model="renameDraft"
                :style="styles.input"
                maxlength="60"
                @keyup.enter="confirmRename(fleet.id)"
                @keyup.esc="cancelRename"
              />
              <button :style="styles.btnSmall" type="button" @click.stop="confirmRename(fleet.id)">OK</button>
              <button :style="styles.btnSmall" type="button" @click.stop="cancelRename">×</button>
            </div>
            <h4 v-else :style="styles.fleetName" @dblclick.stop="startRename(fleet)" title="Doble clic para renombrar">
              {{ fleet.name }}
            </h4>
            <p :style="styles.subtitle">Sistema: {{ getSystemName(fleet.star_system_id) }}</p>
            <p :style="styles.subtitle">Naves: {{ totalShips(fleet) }} · Grupos: {{ fleet.ships?.length || 0 }}</p>
          </div>
          <span :style="getStatusStyle(fleet)">
            {{ fleet.destination ? `EN TRANSITO ${fleet.eta_turns ?? '?'}T` : 'EN ORBITA' }}
          </span>
        </div>

        <div :style="styles.shipList">
          <div v-for="(ship, idx) in fleet.ships" :key="idx" :style="styles.shipItem">
            {{ ship.count }}× {{ ship.type }}
          </div>
        </div>

        <div v-if="!fleet.destination" :style="styles.actions">
          <select v-model="moves[fleet.id]" :style="styles.select">
            <option value="">DESTINO</option>
            <option v-for="conn in connectionsFor(fleet.star_system_id)" :key="conn.id" :value="conn.id">
              {{ conn.name }}
            </option>
          </select>
          <button :style="styles.btnSmall" @click.stop="requestMove(fleet.id)" :disabled="!moves[fleet.id]">SALTAR</button>
          <button :style="styles.btnSmall" @click.stop="startRename(fleet)">RENOMBRAR</button>
          <button :style="styles.btnSmall" @click.stop="openSystem(fleet.star_system_id)">SISTEMA</button>
          <button
            :style="styles.btnSmall"
            v-if="systemMates(fleet).length"
            @click.stop="openTransfer(fleet.id)"
          >TRASPASAR</button>
          <button :style="styles.btnSmall" v-if="canColonize(fleet)" @click.stop="requestColonize(fleet.id)">COLONIZAR</button>
          <button :style="styles.btnDanger" @click.stop="requestDisband(fleet.id)">ELIMINAR</button>
        </div>
      </div>
    </div>

    <div v-if="transferState" class="fleet-modal">
      <div class="fleet-modal-card">
        <header>
          <strong>Traspasar naves</strong>
          <button type="button" @click="transferState = null">×</button>
        </header>
        <p>Desde <em>{{ transferState.fromFleet?.name }}</em> a:</p>
        <select v-model="transferState.toFleetId" :style="styles.select">
          <option value="">Selecciona flota destino</option>
          <option v-for="mate in systemMates(transferState.fromFleet)" :key="mate.id" :value="mate.id">
            {{ mate.name }} ({{ totalShips(mate) }} naves)
          </option>
        </select>

        <div :style="{ display: 'flex', flexDirection: 'column', gap: '0.4rem', marginTop: '0.8rem' }">
          <div
            v-for="ship in (transferState.fromFleet?.ships || [])"
            :key="ship.type"
            :style="{ display: 'flex', gap: '0.5rem', alignItems: 'center' }"
          >
            <span :style="{ flex: 1 }">{{ ship.type }} (max {{ ship.count }})</span>
            <input
              type="number"
              :min="0"
              :max="ship.count"
              v-model.number="transferState.amounts[ship.type]"
              :style="styles.input"
            />
          </div>
        </div>

        <div class="fleet-modal-actions">
          <button :style="styles.btnSmall" type="button" @click="transferState = null">CANCELAR</button>
          <button :style="styles.btnSmall" type="button" :disabled="!transferReady" @click="confirmTransfer">CONFIRMAR</button>
        </div>
      </div>
    </div>

    <div v-if="pendingAction" class="fleet-modal">
      <div class="fleet-modal-card">
        <header>
          <strong>{{ pendingAction.title }}</strong>
          <button type="button" @click="pendingAction = null">×</button>
        </header>
        <p>{{ pendingAction.body }}</p>
        <div class="fleet-modal-actions">
          <button :style="styles.btnSmall" type="button" @click="pendingAction = null">CANCELAR</button>
          <button :style="styles.btnSmall" type="button" @click="confirmPendingAction">CONFIRMAR</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useGameStore } from '../store/gameStore'
import { api } from '../api/client'
import { Theme, createPanelStyle, btnStyle } from '../styles/styleSystem'

const gameStore = useGameStore()
const router = useRouter()
const error = ref('')

const moves = ref<Record<string, string>>({})
const fleetQuery = ref('')
const statusFilter = ref<'all' | 'idle' | 'moving' | 'colony'>('all')
const selectedFleetId = ref('')
const pendingAction = ref<null | { type: 'move' | 'colonize' | 'disband'; fleetId: string; title: string; body: string }>(null)
const transferState = ref<null | { fromFleet: any; toFleetId: string; amounts: Record<string, number> }>(null)
const renamingFleetId = ref<string | null>(null)
const renameDraft = ref('')

const transferReady = computed(() => {
  const t = transferState.value
  if (!t || !t.toFleetId) return false
  return Object.values(t.amounts).some((n) => Number(n) > 0)
})

const fleets = computed<any[]>(() => gameStore.fleets || [])
const systems = computed<any[]>(() => gameStore.galaxy?.star_systems || [])
const selectedFleet = computed(() => fleets.value.find((fleet) => fleet.id === selectedFleetId.value) || filteredFleets.value[0] || null)
const filteredFleets = computed(() => {
  const query = fleetQuery.value.toLowerCase()
  return fleets.value.filter((fleet) => {
    const matchesStatus =
      statusFilter.value === 'all' ||
      (statusFilter.value === 'idle' && !fleet.destination) ||
      (statusFilter.value === 'moving' && !!fleet.destination) ||
      (statusFilter.value === 'colony' && hasColonyShip(fleet))
    if (!matchesStatus) return false
    if (!query) return true
    const haystack = [
      fleet.name,
      fleet.id,
      getSystemName(fleet.star_system_id),
      fleet.destination ? getSystemName(fleet.destination) : '',
      ...(fleet.ships || []).map((ship: any) => ship.type),
    ].join(' ').toLowerCase()
    return haystack.includes(query)
  })
})
const selectedFleetStats = computed(() => {
  const fleet = selectedFleet.value
  if (!fleet) return ''
  return `${totalShips(fleet)} nave(s), ${fleet.ships?.length || 0} grupo(s), ${fleet.command_points_used || 0} CP`
})

const styles = {
  panel: createPanelStyle(),
  head: { display: 'flex', justifyContent: 'space-between', marginBottom: '1.5rem', borderBottom: `1px solid ${Theme.colors.border}`, paddingBottom: '1rem' },
  title: { margin: 0, fontSize: '1.6rem', color: Theme.colors.primary, letterSpacing: '0.18em' },
  subtitle: { margin: '0.3rem 0 0', color: Theme.colors.textMuted, fontSize: '0.85rem' },
  btn: btnStyle(),
  btnSmall: { ...btnStyle(), padding: '0.3rem 0.6rem', fontSize: '0.75rem' },
  btnDanger: { ...btnStyle(), padding: '0.3rem 0.6rem', fontSize: '0.75rem', borderColor: Theme.colors.danger, color: Theme.colors.danger },
  controlRow: { display: 'flex', gap: '0.5rem', flexWrap: 'wrap' as const, marginBottom: '0.9rem' },
  searchInput: { flex: 1, minWidth: '220px', backgroundColor: Theme.colors.bgDark, color: Theme.colors.primary, border: `1px solid ${Theme.colors.primary}`, padding: '0.45rem 0.55rem', fontSize: '0.85rem' },
  detailsPanel: { display: 'grid', gap: '0.25rem', marginBottom: '0.9rem', padding: '0.75rem', backgroundColor: 'rgba(0,255,255,0.06)', border: `1px solid ${Theme.colors.secondary}`, borderRadius: '6px', color: Theme.colors.text },
  fleetGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '1rem' },
  fleetCard: { padding: '0.9rem', backgroundColor: Theme.colors.bgDark, border: `1px solid ${Theme.colors.border}`, borderRadius: '8px' },
  cardHead: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.7rem' },
  fleetName: { margin: 0, fontSize: '1.05rem', color: Theme.colors.text },
  shipList: { margin: '0.6rem 0', padding: '0.6rem', backgroundColor: '#070f24', border: '1px solid rgba(89, 170, 255, 0.18)', borderRadius: '4px' },
  shipItem: { fontSize: '0.85rem', marginBottom: '0.2rem', color: Theme.colors.ok },
  actions: { display: 'flex', gap: '0.4rem', marginTop: '0.6rem', flexWrap: 'wrap' as const },
  select: { flex: 1, minWidth: '120px', backgroundColor: Theme.colors.bgDark, color: Theme.colors.primary, border: `1px solid ${Theme.colors.primary}`, padding: '0.3rem', fontSize: '0.8rem' },
  input: { width: '80px', backgroundColor: Theme.colors.bgDark, color: Theme.colors.text, border: `1px solid ${Theme.colors.primary}`, padding: '0.25rem 0.35rem', fontSize: '0.8rem' },
  empty: { color: Theme.colors.textMuted, fontStyle: 'italic' as const },
  error: { color: Theme.colors.danger, marginBottom: '0.6rem' },
}

function getSystemName(systemId: string) {
  return systems.value.find((s) => s.id === systemId)?.name || 'DESCONOCIDO'
}

function totalShips(fleet: any) {
  return (fleet?.ships || []).reduce((acc: number, ship: any) => acc + Number(ship?.count || 0), 0)
}

function hasColonyShip(fleet: any) {
  return (fleet?.ships || []).some((s: any) => s.type === 'colony_ship' && s.count > 0)
}

function connectionsFor(systemId: string) {
  const sys = systems.value.find((s) => s.id === systemId)
  if (!sys) return []
  return (sys.connections || [])
    .map((cid: string) => systems.value.find((s) => s.id === cid))
    .filter(Boolean)
}

function canColonize(fleet: any) {
  if (!fleet || fleet.destination) return false
  const sys = systems.value.find((s) => s.id === fleet.star_system_id)
  if (!sys) return false
  const hasColony = hasColonyShip(fleet)
  const hasUncolonized = (sys.planets || []).some((p: any) => !p.colonized_by)
  return hasColony && hasUncolonized
}

function getFleetCardStyle(fleet: any) {
  const selected = selectedFleet.value?.id === fleet.id
  return {
    ...styles.fleetCard,
    border: `1px solid ${selected ? Theme.colors.secondary : Theme.colors.border}`,
    boxShadow: selected ? `0 0 18px rgba(255, 215, 0, 0.25)` : 'none',
    cursor: 'pointer',
  }
}

function getStatusStyle(fleet: any) {
  return {
    fontSize: '0.7rem',
    padding: '0.2rem 0.5rem',
    backgroundColor: fleet.destination ? Theme.colors.secondary : Theme.colors.ok,
    color: '#000',
    borderRadius: '4px',
    fontWeight: 'bold' as const,
  }
}

function openSystem(systemId: string) {
  if (!gameStore.gameId) return
  router.push(`/game/${gameStore.gameId}/system/${systemId}`)
}

function requestMove(fleetId: string) {
  const dest = moves.value[fleetId]
  const fleet = fleets.value.find((f) => f.id === fleetId)
  if (!dest || !fleet) return
  pendingAction.value = {
    type: 'move',
    fleetId,
    title: 'Confirmar salto',
    body: `${fleet.name} saltara desde ${getSystemName(fleet.star_system_id)} a ${getSystemName(dest)}. La flota quedara en transito hasta resolver el movimiento.`,
  }
}

function requestColonize(fleetId: string) {
  const fleet = fleets.value.find((f) => f.id === fleetId)
  const sys = fleet ? systems.value.find((s) => s.id === fleet.star_system_id) : null
  const planet = (sys?.planets || []).find((p: any) => !p.colonized_by)
  if (!fleet || !planet) return
  pendingAction.value = {
    type: 'colonize',
    fleetId,
    title: 'Confirmar colonizacion',
    body: `${fleet.name} fundara una colonia en ${planet.name || `planeta ${planet.index}`}. Se consumira una nave colonizadora.`,
  }
}

function requestDisband(fleetId: string) {
  const fleet = fleets.value.find((f) => f.id === fleetId)
  if (!fleet) return
  pendingAction.value = {
    type: 'disband',
    fleetId,
    title: 'Eliminar flota',
    body: `${fleet.name} sera disuelta y todas sus naves se perderan. Esta accion no se puede deshacer.`,
  }
}

async function confirmPendingAction() {
  const action = pendingAction.value
  if (!action) return
  pendingAction.value = null
  if (action.type === 'move') await moveFleet(action.fleetId)
  if (action.type === 'colonize') await colonize(action.fleetId)
  if (action.type === 'disband') await disbandFleet(action.fleetId)
}

async function disbandFleet(fleetId: string) {
  if (!gameStore.gameId) return
  try {
    await api.fleet.disband(gameStore.gameId, fleetId)
    if (selectedFleetId.value === fleetId) selectedFleetId.value = ''
    await gameStore.fetchFleets()
  } catch (err: any) {
    error.value = err.message || 'No se pudo eliminar la flota'
  }
}

async function moveFleet(fleetId: string) {
  const dest = moves.value[fleetId]
  if (!dest || !gameStore.gameId) return
  try {
    await api.fleet.move(gameStore.gameId, fleetId, dest)
    await gameStore.fetchFleets()
  } catch (err: any) {
    error.value = err.message || 'No se pudo mover la flota'
  }
}

function startRename(fleet: any) {
  if (!fleet) return
  renamingFleetId.value = fleet.id
  renameDraft.value = fleet.name || ''
}

function cancelRename() {
  renamingFleetId.value = null
  renameDraft.value = ''
}

async function confirmRename(fleetId: string) {
  const trimmed = renameDraft.value.trim()
  if (!trimmed || !gameStore.gameId) {
    cancelRename()
    return
  }
  try {
    await api.fleet.rename(gameStore.gameId, fleetId, trimmed)
    await gameStore.fetchFleets()
  } catch (err: any) {
    error.value = err.message || 'No se pudo renombrar la flota'
  } finally {
    cancelRename()
  }
}

function systemMates(fleet: any) {
  if (!fleet || fleet.destination) return []
  return fleets.value.filter(
    (f) => f.id !== fleet.id && f.star_system_id === fleet.star_system_id && !f.destination,
  )
}

function openTransfer(fleetId: string) {
  const fleet = fleets.value.find((f) => f.id === fleetId)
  if (!fleet) return
  const amounts: Record<string, number> = {}
  for (const ship of fleet.ships || []) amounts[ship.type] = 0
  transferState.value = { fromFleet: fleet, toFleetId: '', amounts }
}

async function confirmTransfer() {
  const t = transferState.value
  if (!t || !t.fromFleet || !t.toFleetId || !gameStore.gameId) return
  const ships = Object.entries(t.amounts)
    .filter(([, count]) => Number(count) > 0)
    .map(([type, count]) => ({ type, count: Number(count) }))
  if (!ships.length) return
  try {
    await api.fleet.transfer(gameStore.gameId, t.fromFleet.id, t.toFleetId, ships)
    transferState.value = null
    await gameStore.fetchFleets()
  } catch (err: any) {
    error.value = err.message || 'No se pudieron traspasar las naves'
  }
}

async function colonize(fleetId: string) {
  if (!gameStore.gameId) return
  const fleet = fleets.value.find((f) => f.id === fleetId)
  const sys = fleet ? systems.value.find((s) => s.id === fleet.star_system_id) : null
  const planet = (sys?.planets || []).find((p: any) => !p.colonized_by)
  if (!planet) return
  try {
    await api.fleet.colonize(gameStore.gameId, fleetId, planet.index)
    await Promise.all([gameStore.fetchFleets(), gameStore.fetchGalaxy(), gameStore.fetchColonies()])
  } catch (err: any) {
    error.value = err.message || 'No se pudo colonizar'
  }
}

async function reload() {
  error.value = ''
  if (!gameStore.gameId) return
  try {
    await Promise.all([gameStore.fetchFleets(), gameStore.fetchGalaxy()])
  } catch (err: any) {
    error.value = err.message || 'No se pudo refrescar'
  }
}

onMounted(reload)
</script>

<style scoped>
.fleet-modal {
  position: fixed;
  inset: 0;
  z-index: 120;
  display: grid;
  place-items: center;
  background: rgba(0, 0, 0, 0.68);
}

.fleet-modal-card {
  width: min(92%, 520px);
  padding: 1rem;
  border: 1px solid #ffd700;
  background: rgba(5, 10, 25, 0.96);
  color: #e0e0ff;
  box-shadow: 0 0 28px rgba(255, 215, 0, 0.22);
}

.fleet-modal-card header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 0.5rem;
  margin-bottom: 0.6rem;
  border-bottom: 1px dashed rgba(255, 215, 0, 0.35);
}

.fleet-modal-card header button {
  background: transparent;
  border: 1px solid #ff5577;
  color: #ff5577;
  cursor: pointer;
}

.fleet-modal-card p {
  margin: 0 0 0.8rem;
  line-height: 1.4;
}

.fleet-modal-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
  flex-wrap: wrap;
}
</style>
