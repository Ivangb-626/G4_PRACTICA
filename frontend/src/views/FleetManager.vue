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
import { api } from '../api/client';
import { Theme, createPanelStyle, btnStyle } from '../styles/styleSystem';

const gameStore = useGameStore();

const moves = ref<Record<string, number>>({});

const styles = {
  panel: createPanelStyle(),
  head: { display: 'flex', justifyContent: 'space-between', marginBottom: '2rem', borderBottom: `1px solid ${Theme.colors.border}`, paddingBottom: '1rem' },
  title: { margin: 0, fontSize: '2rem', color: Theme.colors.primary, letterSpacing: '0.2em', textShadow: Theme.effects.glow },
  subtitle: { margin: '0.3rem 0 0', color: Theme.colors.textMuted, fontSize: '0.9rem' },
  btn: btnStyle(),
  btnSmall: { ...btnStyle(), padding: '0.3rem 0.6rem', fontSize: '0.75rem' },
  fleetGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: '1.5rem' },
  fleetCard: createPanelStyle(),
  cardHead: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' },
  fleetName: { margin: 0, fontSize: '1.2rem', color: Theme.colors.text },
  shipList: { margin: '1rem 0', padding: '0.8rem', backgroundColor: Theme.colors.bgDark, borderRadius: '4px' },
  shipItem: { fontSize: '0.85rem', marginBottom: '0.3rem', color: Theme.colors.ok },
  actions: { display: 'flex', gap: '0.5rem', marginTop: '1rem' },
  select: { flex: 1, backgroundColor: Theme.colors.bgDark, color: Theme.colors.primary, border: `1px solid ${Theme.colors.primary}`, padding: '0.3rem', fontSize: '0.8rem' },
};

function getStarName(index: number) {
  return gameStore.galaxy?.stars.find((s: any) => s.index === index)?.name || 'UNKNOWN';
}

function getStatusStyle(fleet: any) {
  return {
    fontSize: '0.7rem',
    padding: '0.2rem 0.5rem',
    backgroundColor: fleet.in_transit ? Theme.colors.secondary : Theme.colors.ok,
    color: '#000',
    borderRadius: '4px',
    fontWeight: 'bold' as const,
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
