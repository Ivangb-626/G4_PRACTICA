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
            <Tooltip
              :title="rel.state === 'war' ? 'Rendirse' : 'Rendirse (no disponible)'"
              :description="rel.state === 'war' ? 'Termina la guerra cediendo tus colonias y flotas.' : 'Solo disponible cuando estas en guerra con esta raza.'"
            >
              <button
                :style="rel.state === 'war' ? styles.btnDanger : styles.btnDisabled"
                :disabled="rel.state !== 'war'"
                @click="surrender(rel.other)"
              >RENDIRSE</button>
            </Tooltip>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Treaties -->
    <h3 :style="styles.h3">Tratados activos</h3>
    <ul :style="styles.list">
      <li v-for="t in treaties" :key="t.id" :style="styles.li">
        <strong>{{ treatyTypeLabel(t.type) }}</strong> entre {{ (t.parties || []).map(partyLabel).join(' y ') }}
        · firmado en turno {{ t.signed_at_turn }}
        <span v-if="t.expires_at_turn"> - expira en T{{ t.expires_at_turn }}</span>
      </li>
      <li v-if="!treaties.length" :style="styles.empty">No hay tratados activos.</li>
    </ul>

    <!-- Tech gift -->
    <h3 :style="styles.h3">Regalar tecnologia</h3>
    <p :style="styles.subtitle">
      Cede una tecnologia investigada a otra raza. Cuanto mas cara sea la tecnologia (en RP), mayor sera la mejora diplomatica.
    </p>
    <div :style="styles.row">
      <select v-model="techGift.target" :style="styles.select">
        <option value="">Objetivo</option>
        <option v-for="rel in relationRows" :key="rel.other" :value="rel.other">{{ rel.label }}</option>
      </select>
      <select v-model="techGift.tech" :style="styles.select">
        <option value="">tech a regalar</option>
        <option v-for="t in giftableTechs" :key="t.id" :value="t.id">
          {{ t.label }} ({{ t.cost }} RP, +{{ t.delta }} diplomacia)
        </option>
      </select>
      <button
        :style="styles.btnSmall"
        @click="giftTech"
        :disabled="!techGift.target || !techGift.tech"
      >REGALAR</button>
    </div>
    <p v-if="!giftableTechs.length" :style="styles.empty">
      Aun no tienes tecnologias investigadas para regalar.
    </p>

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
const techGift = ref({ target: '', tech: '' })

const relations = computed<Record<string, any>>(() => gameStore.diplomacy?.relations || {})
const treaties = computed<any[]>(() => (gameStore.diplomacy?.treaties || []).filter((t: any) => t.active))

function empireLabel(id: string): string {
  const game = gameStore.game as any
  const ai = (game?.ai_players || []).find((p: any) => p?.id === id)
  return ai?.race?.name || ai?.name || id
}

function partyLabel(id: string): string {
  if (id === 'player') {
    const playerRace = (gameStore.game as any)?.player?.race?.name
    return playerRace || 'Tu imperio'
  }
  return empireLabel(id)
}

const TREATY_LABELS: Record<string, string> = {
  non_aggression_pact: 'Pacto de No Agresion',
  trade_treaty: 'Tratado Comercial',
  alliance: 'Alianza',
  research_pact: 'Pacto de Investigacion',
  tribute: 'Tributo',
}

function treatyTypeLabel(type: string): string {
  if (!type) return ''
  const key = type.toLowerCase()
  return TREATY_LABELS[key] || type.replace(/_/g, ' ').toUpperCase()
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

const techCostMap = computed<Record<string, number>>(() => {
  const map: Record<string, number> = {}
  const fields = (gameStore.techState as any)?.fields || []
  for (const field of fields) {
    const levels = field?.levels || {}
    for (const lvl of Object.values(levels) as any[]) {
      for (const tech of (lvl?.options || []) as any[]) {
        const id = tech?.id
        const cost = tech?.research_cost ?? tech?.base_cost
        if (id && typeof cost === 'number') map[id] = cost
      }
    }
  }
  return map
})

function predictedTechDelta(cost: number): number {
  return Math.max(5, Math.min(50, Math.floor((cost || 50) / 30)))
}

const giftableTechs = computed(() => {
  const costs = techCostMap.value
  return Array.from(playerTechIds.value)
    .map((id) => {
      const cost = costs[id] ?? 50
      return { id, label: prettifyTechId(id), cost, delta: predictedTechDelta(cost) }
    })
    .sort((a, b) => b.cost - a.cost || a.label.localeCompare(b.label))
})

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
  btnDisabled: { ...btnStyle(), padding: '0.25rem 0.55rem', fontSize: '0.7rem', borderColor: Theme.colors.textMuted, color: Theme.colors.textMuted, marginRight: '0.3rem', opacity: 0.45, cursor: 'not-allowed' as const },
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
    await Promise.all([
      gameStore.fetchDiplomacy(),
      gameStore.techState ? Promise.resolve() : gameStore.fetchResearch(),
    ])
  } catch (err: any) {
    error.value = err.message || 'No se pudieron cargar las relaciones'
  }
}

async function proposeTreaty(target: string, type: string) {
  const name = empireLabel(target)
  const treatyName = treatyTypeLabel(type)
  try {
    const res = await gameStore.proposeTreaty(target, type)
    info.value = res?.accepted
      ? `${name} acepto el ${treatyName}.`
      : `${name} rechazo el ${treatyName}.`
  } catch (err: any) {
    error.value = err.message || 'Error en la propuesta'
  }
}

async function declareWar(target: string) {
  const name = empireLabel(target)
  if (!confirm(`Declarar guerra a ${name}?`)) return
  try {
    await gameStore.declareWar(target)
    info.value = `Guerra declarada a ${name}.`
  } catch (err: any) {
    error.value = err.message
  }
}

async function surrender(target: string) {
  const name = empireLabel(target)
  if (!confirm(`Rendirse ante ${name}? PERDERAS TUS COLONIAS.`)) return
  try {
    await api.diplomacy.surrender(gameStore.gameId!, target)
    info.value = `Rendicion entregada a ${name}.`
    await reload()
  } catch (err: any) {
    error.value = err.message
  }
}

async function giftTech() {
  const target = techGift.value.target
  const techId = techGift.value.tech
  if (!target || !techId || !gameStore.gameId) return
  const name = empireLabel(target)
  const techLabel = prettifyTechId(techId)
  try {
    const res = await api.diplomacy.gift(gameStore.gameId, target, { tech_id: techId })
    if (res?.success === false) {
      error.value = res.reason || 'No se pudo regalar la tecnologia'
      return
    }
    const delta = typeof res?.delta === 'number' ? res.delta : 0
    if (res?.tech_already_owned) {
      info.value = `${name} ya conocia ${techLabel}; no hubo cambio diplomatico.`
    } else {
      info.value = `Regalaste ${techLabel} a ${name}. Diplomacia +${delta}.`
    }
    techGift.value.tech = ''
    await reload()
  } catch (err: any) {
    error.value = err.message || 'No se pudo regalar la tecnologia'
  }
}

async function giftBC(target: string) {
  const name = empireLabel(target)
  try {
    await api.diplomacy.gift(gameStore.gameId!, target, { bc: 50 })
    info.value = `Regalo de 50 BC enviado a ${name}.`
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
