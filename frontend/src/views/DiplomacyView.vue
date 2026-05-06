<template>
  <div :style="styles.panel">
    <div :style="styles.head">
      <div>
        <h2 :style="styles.title">DIPLOMATIC CORPS</h2>
        <div :style="styles.tabs">
          <button v-for="t in tabs" :key="t.id" :style="getTabStyle(t.id)" @click="activeTab = t.id">{{ t.label }}</button>
        </div>
      </div>
      <button :style="styles.btn" @click="loadRelations">REFRESH</button>
    </div>

    <!-- Relations Table -->
    <div v-if="activeTab === 'relations'" :style="styles.content">
      <table :style="styles.table">
        <thead>
          <tr :style="styles.tableHead">
            <th :style="styles.th">FACTION</th>
            <th :style="styles.th">RELATION</th>
            <th :style="styles.th">STATUS</th>
            <th :style="styles.th">TREATIES</th>
            <th :style="styles.th">ACTION</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="rel in gameStore.relations" :key="rel.other" :style="styles.tr">
            <td :style="styles.td">
              <strong :style="{ color: getRaceColor(rel.other) }">{{ rel.other.toUpperCase() }}</strong>
              <small :style="styles.raceSmall">({{ PERSONALITIES[rel.other]?.disposition || 'neutral' }})</small>
            </td>
            <td :style="getRelationStyle(rel.value)">{{ rel.value }}</td>
            <td :style="styles.td">{{ rel.status.replace('_', ' ').toUpperCase() }}</td>
            <td :style="styles.td">{{ rel.treaties.join(', ') || 'NONE' }}</td>
            <td :style="styles.td">
              <button :style="styles.btnSmall" @click="propose(rel.other)">PROPOSE</button>
              <button :style="styles.btnDanger" @click="declareWar(rel.other)">WAR</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Other tabs placeholders -->
    <div v-else :style="styles.placeholder">
      SECURE CHANNEL ESTABLISHED... SELECT A TARGET FOR {{ activeTab.toUpperCase() }}.
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useGameStore } from '../store/gameStore';
import { api } from '../api/client';

const gameStore = useGameStore();
const activeTab = ref('relations');

const PERSONALITIES = {
  alkari: { disposition: 'defensive', color: '#44ee44' },
  meklar: { disposition: 'industrial', color: '#ee4444' },
  trilarian: { disposition: 'erratic', color: '#4444ff' }
};

const tabs = [
  { id: 'relations', label: 'RELATIONS' },
  { id: 'intel', label: 'INTEL' },
  { id: 'trade', label: 'TRADE' },
  { id: 'gift', label: 'GIFT' },
  { id: 'demand', label: 'DEMAND' }
];

const styles = {
  panel: {
    padding: '1.5rem',
    backgroundColor: '#070f24',
    color: '#e0e0ff',
    fontFamily: 'monospace',
    border: '2px solid #00ffff',
  },
  head: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: '2rem',
  },
  title: {
    margin: 0,
    fontSize: '2rem',
    color: '#00ffff',
    letterSpacing: '0.2em',
  },
  tabs: {
    display: 'flex',
    gap: '0.5rem',
    marginTop: '1rem',
  },
  btn: {
    backgroundColor: '#1a1a3e',
    color: '#00ffff',
    border: '2px solid #00ffff',
    padding: '0.6rem 1.2rem',
    cursor: 'pointer',
    fontWeight: 'bold' as const,
  },
  btnSmall: {
    backgroundColor: '#2a2a5e',
    color: '#00ffff',
    border: '1px solid #00ffff',
    padding: '0.3rem 0.6rem',
    cursor: 'pointer',
    marginRight: '0.5rem',
  },
  btnDanger: {
    backgroundColor: '#5e2a2a',
    color: '#ff4444',
    border: '1px solid #ff4444',
    padding: '0.3rem 0.6rem',
    cursor: 'pointer',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse' as const,
  },
  tableHead: {
    borderBottom: '2px solid #00ffff',
  },
  th: {
    textAlign: 'left' as const,
    padding: '0.8rem',
    color: '#8888aa',
    fontSize: '0.8rem',
  },
  tr: {
    borderBottom: '1px solid #1a1a3e',
  },
  td: {
    padding: '1rem 0.8rem',
  },
  raceSmall: {
    display: 'block',
    fontSize: '0.7rem',
    color: '#8888aa',
    marginTop: '0.2rem',
  },
  placeholder: {
    padding: '4rem',
    textAlign: 'center' as const,
    color: '#8888aa',
    fontStyle: 'italic',
  }
};

function getTabStyle(id: string) {
  const isActive = activeTab.value === id;
  return {
    padding: '0.4rem 0.8rem',
    backgroundColor: isActive ? '#00ffff' : '#1a1a3e',
    color: isActive ? '#070f24' : '#00ffff',
    border: '1px solid #00ffff',
    cursor: 'pointer',
    fontSize: '0.75rem',
    fontWeight: 'bold' as const,
  };
}

function getRaceColor(raceId: string) {
  return PERSONALITIES[raceId]?.color || '#fff';
}

function getRelationStyle(value: number) {
  let color = '#aaaacc';
  if (value < 0) color = '#ff4444';
  if (value > 50) color = '#44ee44';
  if (value > 100) color = '#ffd700';

  return {
    padding: '1rem 0.8rem',
    color,
    fontWeight: 'bold' as const,
  };
}

async function loadRelations() {
  if (!gameStore.gameId) return;
  try {
    const res = await api.diplomacy.list(gameStore.gameId);
    gameStore.relations = res.relations || [];
  } catch (err) {
    console.error(err);
  }
}

async function propose(targetId: string) {
  // Logic to propose treaty
}

async function declareWar(targetId: string) {
  if (!confirm(`DECLARE WAR ON ${targetId.toUpperCase()}?`)) return;
  // Logic to declare war
}

onMounted(loadRelations);
</script>
