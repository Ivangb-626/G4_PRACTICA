<template>
  <div :style="styles.panel">
    <div :style="styles.head">
      <div>
        <h2 :style="styles.title">FLEET ADMIRALTY</h2>
        <p :style="styles.subtitle">Strategic command and tactical disposition of imperial vessels.</p>
      </div>
      <button :style="styles.btn" @click="gameStore.fetchFleets()">REFRESH</button>
    </div>

    <div :style="styles.fleetGrid">
      <div v-for="fleet in gameStore.fleets" :key="fleet.id" :style="styles.fleetCard">
        <div :style="styles.cardHead">
          <div>
            <h4 :style="styles.fleetName">{{ fleet.name }}</h4>
            <p :style="styles.subtitle">Location: {{ getStarName(fleet.star_index) }}</p>
          </div>
          <span :style="getStatusStyle(fleet)">{{ fleet.in_transit ? `ETA ${fleet.eta} T` : 'READY' }}</span>
        </div>

        <div :style="styles.shipList">
          <div v-for="ship in fleet.ships" :key="ship.id" :style="styles.shipItem">
            {{ ship.count }}x {{ ship.name }}
          </div>
        </div>

        <div v-if="!fleet.in_transit" :style="styles.actions">
          <select v-model="moves[fleet.id]" :style="styles.select">
            <option value="">SELECT DESTINATION</option>
            <option v-for="star in gameStore.galaxy?.stars" :key="star.index" :value="star.index">
              {{ star.name }}
            </option>
          </select>
          <button :style="styles.btnSmall" @click="moveFleet(fleet.id)">JUMP</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useGameStore } from '../store/gameStore';
import { useUIStore } from '../store/uiStore';
import { api } from '../api/client';

const gameStore = useGameStore();
const uiStore = useUIStore();

const moves = ref<Record<string, number>>({});

const styles = {
  panel: {
    padding: '1.5rem',
    backgroundColor: '#0a0a2e',
    color: '#e0e0ff',
    fontFamily: 'monospace',
  },
  head: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '2rem',
    borderBottom: '2px solid #00ffff',
    paddingBottom: '1rem',
  },
  title: {
    margin: 0,
    fontSize: '2rem',
    color: '#00ffff',
    letterSpacing: '0.2em',
  },
  subtitle: {
    margin: '0.3rem 0 0',
    color: '#8888aa',
    fontSize: '0.9rem',
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
  },
  fleetGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))',
    gap: '1.5rem',
  },
  fleetCard: {
    padding: '1.2rem',
    backgroundColor: '#1a1a3e',
    border: '1px solid rgba(0, 255, 255, 0.3)',
    borderRadius: '8px',
  },
  cardHead: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: '1rem',
  },
  fleetName: {
    margin: 0,
    fontSize: '1.2rem',
    color: '#fff',
  },
  shipList: {
    margin: '1rem 0',
    padding: '0.8rem',
    backgroundColor: '#070f24',
    borderRadius: '4px',
  },
  shipItem: {
    fontSize: '0.85rem',
    marginBottom: '0.3rem',
    color: '#44ee44',
  },
  actions: {
    display: 'flex',
    gap: '0.5rem',
    marginTop: '1rem',
  },
  select: {
    flex: 1,
    backgroundColor: '#070f24',
    color: '#00ffff',
    border: '1px solid #00ffff',
    padding: '0.3rem',
    fontSize: '0.8rem',
  }
};

function getStarName(index: number) {
  return gameStore.galaxy?.stars.find((s: any) => s.index === index)?.name || 'UNKNOWN';
}

function getStatusStyle(fleet: any) {
  return {
    fontSize: '0.7rem',
    padding: '0.2rem 0.5rem',
    backgroundColor: fleet.in_transit ? '#5e4a07' : '#075e2a',
    color: '#fff',
    borderRadius: '4px',
  };
}

async function moveFleet(fleetId: string) {
  const dest = moves.value[fleetId];
  if (dest === undefined || !gameStore.gameId) return;
  try {
    await api.fleet.move(gameStore.gameId, fleetId, dest);
    gameStore.fetchFleets();
  } catch (err) {
    console.error(err);
  }
}

onMounted(() => {
  if (gameStore.gameId) {
    gameStore.fetchFleets();
  }
});
</script>
