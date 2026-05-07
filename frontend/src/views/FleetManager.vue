<template>
  <div :style="styles.panel">
    <div :style="styles.head">
      <div>
        <h2 :style="styles.title">FLEET ADMIRALTY</h2>
        <p :style="styles.subtitle">Mando y movimiento de las flotas imperiales.</p>
      </div>
      <button :style="styles.btn" @click="reload">REFRESH</button>
    </div>

    <p v-if="error" :style="styles.error">{{ error }}</p>
    <p v-if="!fleets.length" :style="styles.empty">No hay flotas activas.</p>

    <div :style="styles.fleetGrid">
      <div v-for="fleet in fleets" :key="fleet.id" :style="styles.fleetCard">
        <div :style="styles.cardHead">
          <div>
            <h4 :style="styles.fleetName">{{ fleet.name }}</h4>
            <p :style="styles.subtitle">Sistema: {{ getSystemName(fleet.star_system_id) }}</p>
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
          <button :style="styles.btnSmall" @click="moveFleet(fleet.id)" :disabled="!moves[fleet.id]">SALTAR</button>
          <button :style="styles.btnSmall" v-if="canColonize(fleet)" @click="colonize(fleet.id)">COLONIZAR</button>
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

const gameStore = useGameStore()
const error = ref('')

const moves = ref<Record<string, string>>({})

const fleets = computed<any[]>(() => gameStore.fleets || [])
const systems = computed<any[]>(() => gameStore.galaxy?.star_systems || [])

const styles = {
  panel: createPanelStyle(),
  head: { display: 'flex', justifyContent: 'space-between', marginBottom: '1.5rem', borderBottom: `1px solid ${Theme.colors.border}`, paddingBottom: '1rem' },
  title: { margin: 0, fontSize: '1.6rem', color: Theme.colors.primary, letterSpacing: '0.18em' },
  subtitle: { margin: '0.3rem 0 0', color: Theme.colors.textMuted, fontSize: '0.85rem' },
  btn: btnStyle(),
  btnSmall: { ...btnStyle(), padding: '0.3rem 0.6rem', fontSize: '0.75rem' },
  fleetGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '1rem' },
  fleetCard: { padding: '0.9rem', backgroundColor: Theme.colors.bgDark, border: `1px solid ${Theme.colors.border}`, borderRadius: '8px' },
  cardHead: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.7rem' },
  fleetName: { margin: 0, fontSize: '1.05rem', color: Theme.colors.text },
  shipList: { margin: '0.6rem 0', padding: '0.6rem', backgroundColor: '#070f24', border: '1px solid rgba(89, 170, 255, 0.18)', borderRadius: '4px' },
  shipItem: { fontSize: '0.85rem', marginBottom: '0.2rem', color: Theme.colors.ok },
  actions: { display: 'flex', gap: '0.4rem', marginTop: '0.6rem', flexWrap: 'wrap' as const },
  select: { flex: 1, minWidth: '120px', backgroundColor: Theme.colors.bgDark, color: Theme.colors.primary, border: `1px solid ${Theme.colors.primary}`, padding: '0.3rem', fontSize: '0.8rem' },
  empty: { color: Theme.colors.textMuted, fontStyle: 'italic' as const },
  error: { color: Theme.colors.danger, marginBottom: '0.6rem' },
}

function getSystemName(systemId: string) {
  return systems.value.find((s) => s.id === systemId)?.name || 'DESCONOCIDO'
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
  const hasColony = (fleet.ships || []).some((s: any) => s.type === 'colony_ship' && s.count > 0)
  const hasUncolonized = (sys.planets || []).some((p: any) => !p.colonized_by)
  return hasColony && hasUncolonized
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
