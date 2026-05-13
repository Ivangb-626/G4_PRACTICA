<template>
  <div :style="styles.panel">
    <div :style="styles.head">
      <div>
        <h2 :style="styles.title">CUERPO DIPLOMATICO</h2>
        <p :style="styles.subtitle">Tratados, regalos, demandas y declaraciones de guerra.</p>
      </div>
      <button :style="styles.btn" @click="reload">REFRESH</button>
    </div>

    <p v-if="error" :style="styles.error">{{ error }}</p>
    <p v-if="info" :style="styles.info">{{ info }}</p>

    <!-- Relations -->
    <h3 :style="styles.h3">Relaciones</h3>
    <table :style="styles.table">
      <thead>
        <tr>
          <th :style="styles.th">FACCION</th>
          <th :style="styles.th">VALOR</th>
          <th :style="styles.th">ESTADO</th>
          <th :style="styles.th">ACCIONES</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="rel in relationRows" :key="rel.other">
          <td :style="styles.td"><strong :style="{ color: '#88ff88' }">{{ rel.label.toUpperCase() }}</strong></td>
          <td :style="getRelationStyle(rel.value)">{{ rel.value }}</td>
          <td :style="styles.td">{{ rel.state.toUpperCase() }}</td>
          <td :style="styles.td">
            <Tooltip title="Pacto de No Agresion" description="Acuerdo de no atacarse mutuamente.">
              <button :style="styles.btnSmall" @click="proposeTreaty(rel.other, 'non_aggression_pact')">NAP</button>
            </Tooltip>
            <Tooltip title="Tratado Comercial" description="Establece rutas comerciales para ingresos extra.">
              <button :style="styles.btnSmall" @click="proposeTreaty(rel.other, 'trade_treaty')">COMERCIO</button>
            </Tooltip>
            <Tooltip title="Alianza" description="Pacto militar: defensa mutua en caso de ataque.">
              <button :style="styles.btnSmall" @click="proposeTreaty(rel.other, 'alliance')">ALIANZA</button>
            </Tooltip>
            <Tooltip title="Regalar BC" description="Mejora relaciones.">
              <button :style="styles.btnSmall" @click="giftBC(rel.other)">REGALO 50 BC</button>
            </Tooltip>
            <Tooltip title="Declarar Guerra" description="Inicia hostilidades.">
              <button :style="styles.btnDanger" @click="declareWar(rel.other)">GUERRA</button>
            </Tooltip>
            <Tooltip title="Rendirse" description="Termina la partida si estas en guerra.">
              <button :style="styles.btnDanger" @click="surrender(rel.other)">RENDIRSE</button>
            </Tooltip>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Treaties -->
    <h3 :style="styles.h3">Tratados activos</h3>
    <ul :style="styles.list">
      <li v-for="t in treaties" :key="t.id" :style="styles.li">
        <strong>{{ t.type.toUpperCase() }}</strong> · {{ (t.parties || []).join(' & ') }}
        · turno {{ t.signed_at_turn }}
        <span v-if="t.expires_at_turn"> - expira en T{{ t.expires_at_turn }}</span>
      </li>
      <li v-if="!treaties.length" :style="styles.empty">No hay tratados activos.</li>
    </ul>

    <!-- Tech trade -->
    <h3 :style="styles.h3">Intercambio de tecnologia</h3>
    <div :style="styles.row">
      <select v-model="trade.target" :style="styles.select" @change="trade.requested = ''">
        <option value="">Objetivo</option>
        <option v-for="rel in relationRows" :key="rel.other" :value="rel.other">{{ rel.label }}</option>
      </select>
      <select v-model="trade.offered" :style="styles.select">
        <option value="">tech ofrecida</option>
        <option v-for="t in offerableTechs" :key="t.id" :value="t.id">{{ t.label }}</option>
      </select>
      <select v-model="trade.requested" :style="styles.select" :disabled="!trade.target">
        <option value="">tech solicitada</option>
        <option v-for="t in requestableTechs" :key="t.id" :value="t.id">{{ t.label }}</option>
      </select>
      <button :style="styles.btnSmall" @click="techTrade" :disabled="!trade.target || !trade.offered || !trade.requested">PROPONER</button>
    </div>
    <p v-if="trade.target && !requestableTechs.length" :style="styles.empty">
      Ese imperio no tiene tecnologias que te falten.
    </p>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useGameStore } from '../store/gameStore'
import { api } from '../api/client'
import { Theme, createPanelStyle, btnStyle } from '../styles/styleSystem'
import Tooltip from '../components/Tooltip.vue' // Import the Tooltip component

const gameStore = useGameStore()
const error = ref('')
const info = ref('')
const trade = ref({ target: '', offered: '', requested: '' })

const relations = computed<Record<string, any>>(() => gameStore.diplomacy?.relations || {})
const treaties = computed<any[]>(() => (gameStore.diplomacy?.treaties || []).filter((t: any) => t.active))

function empireLabel(id: string): string {
  const game = gameStore.game as any
  const ai = (game?.ai_players || []).find((p: any) => p?.id === id)
  return ai?.name || id
}

function ownedTechIds(empire: any): Set<string> {
  const items = empire?.technologies?.researched || []
  return new Set(
    items
      .filter((t: any) => t?.tech_id && t?.status !== 'discarded')
      .map((t: any) => t.tech_id as string),
  )
}

function prettifyTechId(id: string): string {
  return id.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

const playerTechIds = computed<Set<string>>(() => ownedTechIds((gameStore.game as any)?.player))

const offerableTechs = computed(() =>
  Array.from(playerTechIds.value)
    .map((id) => ({ id, label: prettifyTechId(id) }))
    .sort((a, b) => a.label.localeCompare(b.label)),
)

const requestableTechs = computed(() => {
  const target = trade.value.target
  if (!target) return []
  const game = gameStore.game as any
  const targetEmpire = (game?.ai_players || []).find((p: any) => p?.id === target)
  if (!targetEmpire) return []
  const targetTechs = ownedTechIds(targetEmpire)
  const mine = playerTechIds.value
  return Array.from(targetTechs)
    .filter((id) => !mine.has(id))
    .map((id) => ({ id, label: prettifyTechId(id) }))
    .sort((a, b) => a.label.localeCompare(b.label))
})

const relationRows = computed(() => {
  // Solo mostramos la relacion del jugador con cada IA: una entrada por imperio.
  const seen = new Set<string>()
  const out: Array<{ other: string; label: string; value: number; state: string }> = []
  Object.entries(relations.value).forEach(([key, rel]) => {
    const parts = key.split('|')
    if (!parts.includes('player')) return
    const other = parts.find((p) => p !== 'player')
    if (!other || other === 'antaranos' || seen.has(other)) return
    seen.add(other)
    out.push({ other, label: empireLabel(other), value: rel.value ?? 0, state: rel.state ?? 'neutral' })
  })
  return out.sort((a, b) => a.label.localeCompare(b.label))
})

const styles = {
  panel: createPanelStyle(),
  head: { display: 'flex', justifyContent: 'space-between', marginBottom: '1.5rem', borderBottom: `1px solid ${Theme.colors.border}`, paddingBottom: '1rem' },
  title: { margin: 0, fontSize: '1.6rem', color: Theme.colors.primary, letterSpacing: '0.18em' },
  subtitle: { margin: '0.3rem 0 0', color: Theme.colors.textMuted, fontSize: '0.85rem' },
  h3: { color: Theme.colors.secondary, marginTop: '1.4rem', marginBottom: '0.6rem', fontSize: '1rem', letterSpacing: '0.1em' },
  btn: btnStyle(),
  btnSmall: { ...btnStyle(), padding: '0.25rem 0.55rem', fontSize: '0.7rem', marginRight: '0.3rem', marginBottom: '0.3rem' },
  btnDanger: { ...btnStyle(), padding: '0.25rem 0.55rem', fontSize: '0.7rem', borderColor: Theme.colors.danger, color: Theme.colors.danger, marginRight: '0.3rem' },
  table: { width: '100%', borderCollapse: 'collapse' as const, marginBottom: '0.5rem' },
  th: { textAlign: 'left' as const, padding: '0.5rem', color: Theme.colors.textMuted, fontSize: '0.75rem', textTransform: 'uppercase' as const, borderBottom: `1px solid ${Theme.colors.border}` },
  td: { padding: '0.5rem', borderBottom: '1px solid rgba(89, 170, 255, 0.15)', fontSize: '0.85rem' },
  list: { margin: '0.5rem 0', padding: 0, listStyle: 'none' as const },
  li: { padding: '0.4rem 0.6rem', backgroundColor: Theme.colors.bgDark, border: `1px solid ${Theme.colors.border}`, borderRadius: '4px', marginBottom: '0.3rem', fontSize: '0.85rem' },
  empty: { color: Theme.colors.textMuted, fontStyle: 'italic' as const, padding: '0.4rem' },
  row: { display: 'flex', gap: '0.4rem', flexWrap: 'wrap' as const, alignItems: 'center' },
  select: { backgroundColor: Theme.colors.bgDark, color: Theme.colors.primary, border: `1px solid ${Theme.colors.primary}`, padding: '0.3rem 0.5rem', fontSize: '0.8rem' },
  input: { backgroundColor: Theme.colors.bgDark, color: Theme.colors.text, border: `1px solid ${Theme.colors.primary}`, padding: '0.3rem 0.5rem', fontSize: '0.8rem' },
  error: { color: Theme.colors.danger, marginBottom: '0.6rem' },
  info: { color: Theme.colors.ok, marginBottom: '0.6rem' },
}

function getRelationStyle(value: number) {
  return {
    padding: '0.5rem',
    color: value > 50 ? Theme.colors.ok : value < 0 ? Theme.colors.danger : Theme.colors.text,
    fontWeight: 'bold' as const,
    borderBottom: '1px solid rgba(89, 170, 255, 0.15)',
  }
}

async function reload() {
  error.value = ''
  info.value = ''
  if (!gameStore.gameId) return
  try {
    await gameStore.fetchDiplomacy()
  } catch (err: any) {
    error.value = err.message || 'No se pudieron cargar las relaciones'
  }
}

async function proposeTreaty(target: string, type: string) {
  try {
    const res = await gameStore.proposeTreaty(target, type)
    info.value = res?.accepted ? `${target} acepto ${type}` : `${target} rechazo ${type}`
  } catch (err: any) {
    error.value = err.message || 'Error en la propuesta'
  }
}

async function declareWar(target: string) {
  if (!confirm(`Declarar guerra a ${target}?`)) return
  try {
    await gameStore.declareWar(target)
    info.value = `Guerra declarada a ${target}`
  } catch (err: any) {
    error.value = err.message
  }
}

async function surrender(target: string) {
  if (!confirm(`Rendirse ante ${target}? PERDERAS TUS COLONIAS.`)) return
  try {
    await api.diplomacy.surrender(gameStore.gameId!, target)
    info.value = 'Rendicion entregada'
    await reload()
  } catch (err: any) {
    error.value = err.message
  }
}

async function giftBC(target: string) {
  try {
    await api.diplomacy.gift(gameStore.gameId!, target, { bc: 50 })
    info.value = `Regalo de 50 BC enviado a ${target}`
    await reload()
  } catch (err: any) {
    error.value = err.message
  }
}

async function techTrade() {
  if (!trade.value.target || !trade.value.offered || !trade.value.requested) return
  try {
    const res = await api.diplomacy.techTrade(
      gameStore.gameId!,
      trade.value.target,
      trade.value.offered,
      trade.value.requested,
    )
    info.value = res?.accepted ? 'Intercambio aceptado' : 'Intercambio rechazado'
    await reload()
  } catch (err: any) {
    error.value = err.message
  }
}

onMounted(reload)
</script>
