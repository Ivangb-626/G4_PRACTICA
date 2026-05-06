<template>
  <div :style="styles.panel">
    <div :style="styles.head">
      <div>
        <h2 :style="styles.title">DIPLOMATIC CORPS</h2>
        <div :style="styles.tabs">
          <button v-for="t in tabs" :key="t.id" :style="getTabStyle(t.id)" @click="activeTab = t.id">{{ t.label }}</button>
        </div>
      </div>
      <button :style="styles.btn(hovered.refresh)" @mouseover="hovered.refresh=true" @mouseleave="hovered.refresh=false" @click="loadRelations">REFRESH</button>
    </div>

    <!-- Relations Table -->
    <div :style="styles.content">
      <table :style="styles.table">
        <thead>
          <tr>
            <th :style="styles.th">FACTION</th>
            <th :style="styles.th">RELATION</th>
            <th :style="styles.th">STATUS</th>
            <th :style="styles.th">ACTION</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="rel in gameStore.relations" :key="rel.other" :style="styles.tr">
            <td :style="styles.td">
              <strong :style="{ color: getRaceColor(rel.other) }">{{ rel.other.toUpperCase() }}</strong>
            </td>
            <td :style="getRelationStyle(rel.value)">{{ rel.value }}</td>
            <td :style="styles.td">{{ rel.status.replace('_', ' ').toUpperCase() }}</td>
            <td :style="styles.td">
              <button :style="styles.btnSmall(hovered[rel.other+'p'])" @mouseover="hovered[rel.other+'p']=true" @mouseleave="hovered[rel.other+'p']=false" @click="propose(rel.other)">PROPOSE</button>
              <button :style="styles.btnDanger(hovered[rel.other+'w'])" @mouseover="hovered[rel.other+'w']=true" @mouseleave="hovered[rel.other+'w']=false" @click="declareWar(rel.other)">WAR</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { useGameStore } from '../store/gameStore';
import { api } from '../api/client';
import { Theme, createPanelStyle, btnStyle } from '../styles/styleSystem';

const gameStore = useGameStore();
const activeTab = ref('relations');
const hovered = reactive<Record<string, boolean>>({});

const tabs = [
  { id: 'relations', label: 'RELATIONS' },
  { id: 'intel', label: 'INTEL' },
  { id: 'trade', label: 'TRADE' }
];

const styles = {
  panel: createPanelStyle(),
  head: { display: 'flex', justifyContent: 'space-between', marginBottom: '2rem' },
  title: { margin: 0, fontSize: '2rem', color: Theme.colors.primary, letterSpacing: '0.2em', textShadow: Theme.effects.glow },
  tabs: { display: 'flex', gap: '0.5rem', marginTop: '1rem' },
  btn: (h: boolean) => btnStyle(h),
  btnSmall: (h: boolean) => ({ ...btnStyle(h), padding: '0.3rem 0.6rem', fontSize: '0.75rem', marginRight: '0.5rem' }),
  btnDanger: (h: boolean) => ({ ...btnStyle(h), borderColor: Theme.colors.danger, color: Theme.colors.danger, backgroundColor: h ? Theme.colors.danger : 'transparent', padding: '0.3rem 0.6rem', fontSize: '0.75rem' }),
  content: { marginTop: '1rem' },
  table: { width: '100%', borderCollapse: 'collapse' as const },
  th: { textAlign: 'left' as const, padding: '1rem', color: Theme.colors.textMuted, fontSize: '0.8rem', textTransform: 'uppercase' as const },
  td: { padding: '1rem', borderBottom: `1px solid ${Theme.colors.border}` },
  tr: { transition: 'background 0.2s', '&:hover': { backgroundColor: 'rgba(255,255,255,0.05)' } }
};

function getTabStyle(id: string) {
  const isActive = activeTab.value === id;
  return {
    padding: '0.4rem 0.8rem',
    backgroundColor: isActive ? Theme.colors.primary : 'transparent',
    color: isActive ? '#000' : Theme.colors.primary,
    border: `1px solid ${Theme.colors.primary}`,
    cursor: 'pointer',
    fontSize: '0.75rem',
    fontWeight: 'bold' as const,
  };
}

function getRaceColor(raceId: string) {
  return { alkari: Theme.colors.ok, meklar: Theme.colors.danger, trilarian: Theme.colors.primary }[raceId] || '#fff';
}

function getRelationStyle(value: number) {
  return { padding: '1rem', color: value > 50 ? Theme.colors.ok : value < 0 ? Theme.colors.danger : Theme.colors.text, fontWeight: 'bold' as const };
}

async function loadRelations() {
  if (!gameStore.gameId) return;
  const res = await api.diplomacy.list(gameStore.gameId);
  gameStore.relations = res || [];
}

async function propose(targetId: string) {}
async function declareWar(targetId: string) { if (confirm('DECLARE WAR?')) {} }

onMounted(loadRelations);
</script>
