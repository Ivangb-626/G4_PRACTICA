<template>
  <div :style="styles.screen">
    <div :style="styles.victoryBox">
      <h1 :style="styles.title">VICTORY</h1>
      <h2 :style="styles.subtitle">ANTARES DEFEATED</h2>
      
      <div :style="styles.scoreCard">
        <h3 :style="styles.innerTitle">IMPERIAL SCORE BREAKDOWN</h3>
        <div :style="styles.scoreRow">
          <span>Colonies (x500)</span>
          <span>{{ score.colonies * 500 }}</span>
        </div>
        <div :style="styles.scoreRow">
          <span>Population (x10)</span>
          <span>{{ score.population * 10 }}</span>
        </div>
        <div :style="styles.scoreRow">
          <span>Technologies (x100)</span>
          <span>{{ score.techs * 100 }}</span>
        </div>
        <div :style="styles.scoreRow">
          <span>Credits (x0.1)</span>
          <span>{{ (score.bc * 0.1).toFixed(1) }}</span>
        </div>
        <div :style="styles.scoreRow">
          <span>Turns (-2/turn)</span>
          <span>-{{ score.turns * 2 }}</span>
        </div>
        <div :style="styles.totalRow">
          <span>FINAL SCORE</span>
          <span>{{ score.total }}</span>
        </div>
      </div>

      <div :style="styles.hofSection">
        <h3 :style="styles.innerTitle">HALL OF FAME</h3>
        <table :style="styles.table">
          <thead>
            <tr>
              <th :style="styles.th">COMMANDER</th>
              <th :style="styles.th">RACE</th>
              <th :style="styles.th">SCORE</th>
              <th :style="styles.th">DATE</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(entry, idx) in hof" :key="idx" :style="styles.tr">
              <td :style="styles.td">{{ entry.username }}</td>
              <td :style="styles.td">{{ entry.race.toUpperCase() }}</td>
              <td :style="styles.td">{{ entry.score }}</td>
              <td :style="styles.td">{{ new Date(entry.date).toLocaleDateString() }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <button :style="styles.btn" @click="uiStore.setScreen('main_menu')">RETURN TO COMMAND</button>
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

const hof = ref<any[]>([]);
const score = ref({
  colonies: 0,
  population: 0,
  techs: 0,
  bc: 0,
  turns: 0,
  total: 0
});

const styles = {
  screen: {
    height: '100%',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#000',
    backgroundImage: 'radial-gradient(circle, #1a1a3e 0%, #000 100%)',
  },
  victoryBox: {
    width: '600px',
    padding: '2rem',
    backgroundColor: 'rgba(7, 15, 36, 0.9)',
    border: '4px solid #ffd700',
    borderRadius: '16px',
    textAlign: 'center' as const,
    boxShadow: '0 0 50px rgba(255, 215, 0, 0.3)',
  },
  title: {
    fontSize: '4rem',
    color: '#ffd700',
    margin: 0,
    letterSpacing: '0.5em',
    textShadow: '0 0 20px #ffd700',
  },
  subtitle: {
    fontSize: '1.5rem',
    color: '#00ffff',
    margin: '0.5rem 0 2rem',
    letterSpacing: '0.2em',
  },
  scoreCard: {
    backgroundColor: '#1a1a3e',
    padding: '1.5rem',
    borderRadius: '8px',
    marginBottom: '2rem',
    textAlign: 'left' as const,
  },
  innerTitle: {
    margin: '0 0 1rem',
    fontSize: '1rem',
    color: '#8888aa',
    borderBottom: '1px solid #333',
    paddingBottom: '0.5rem',
  },
  scoreRow: {
    display: 'flex',
    justifyContent: 'space-between',
    padding: '0.4rem 0',
    fontSize: '0.9rem',
  },
  totalRow: {
    display: 'flex',
    justifyContent: 'space-between',
    padding: '1rem 0 0',
    marginTop: '0.5rem',
    borderTop: '2px solid #ffd700',
    fontSize: '1.2rem',
    fontWeight: 'bold' as const,
    color: '#ffd700',
  },
  hofSection: {
    marginBottom: '2rem',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse' as const,
    fontSize: '0.8rem',
  },
  th: {
    padding: '0.5rem',
    borderBottom: '1px solid #00ffff',
    color: '#00ffff',
  },
  td: {
    padding: '0.5rem',
    borderBottom: '1px solid #1a1a3e',
  },
  tr: {
    backgroundColor: 'rgba(255, 255, 255, 0.02)',
  },
  btn: {
    backgroundColor: '#ffd700',
    color: '#000',
    border: 'none',
    padding: '1rem 2rem',
    cursor: 'pointer',
    fontSize: '1.1rem',
    fontWeight: 'bold' as const,
    borderRadius: '4px',
  }
};

async function loadHof() {
  try {
    const res = await api.game.getTopHallOfFame(); // Need to ensure client has this
    hof.value = res || [];
  } catch (err) {
    console.error(err);
  }
}

onMounted(() => {
  loadHof();
  // Compute local score if available in gameStore.game
  if (gameStore.game) {
    const p = gameStore.game.player;
    score.value = {
      colonies: p.colonies.length,
      population: p.colonies.reduce((sum: number, c: any) => sum + (c.population || 0), 0),
      techs: p.technologies.length,
      bc: p.bc,
      turns: gameStore.game.turn,
      total: gameStore.game.score || 0
    };
  }
});
</script>
