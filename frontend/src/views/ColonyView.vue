<template>
  <div v-if="colony" :style="styles.layout">
    <div :style="styles.colonyPanel">
      <div :style="styles.panelHead">
        <div>
          <h2 :style="styles.title">{{ colony.name }}</h2>
          <p :style="styles.subtitle">
            Sistema {{ colony.star_index }} · Poblacion {{ colony.population }}/{{ colony.max_population }}
          </p>
        </div>
        <button :style="styles.btn" @click="uiStore.setScreen('galaxy')">GALAXY MAP</button>
      </div>

      <!-- Stats Grid -->
      <div :style="styles.statGrid">
        <div :style="styles.statCard">
          <span :style="styles.statLabel">FOOD</span>
          <strong :style="styles.statValue">{{ colony.food_output }}</strong>
          <small :style="styles.statSmall">Surplus {{ colony.food_surplus }}</small>
        </div>
        <div :style="styles.statCard">
          <span :style="styles.statLabel">INDUSTRY</span>
          <strong :style="styles.statValue">{{ colony.industry_output }}</strong>
          <small :style="styles.statSmall">Production/turn</small>
        </div>
        <div :style="styles.statCard">
          <span :style="styles.statLabel">RESEARCH</span>
          <strong :style="styles.statValue">{{ colony.research_output }}</strong>
          <small :style="styles.statSmall">Labs active</small>
        </div>
        <div :style="styles.statCard">
          <span :style="styles.statLabel">CREDITS</span>
          <strong :style="styles.statValue">{{ colony.bc_output }}</strong>
          <small :style="styles.statSmall">Local income</small>
        </div>
      </div>

      <div :style="styles.split">
        <!-- Population Mgmt -->
        <div :style="styles.innerPanel">
          <div :style="styles.innerHead">
            <h3 :style="styles.innerTitle">POPULATION</h3>
            <button :style="styles.btn" @click="savePopulation">APPLY</button>
          </div>
          <div :style="styles.sliderGroup">
            <label>Farmers: {{ population.farmers }}</label>
            <input v-model.number="population.farmers" type="range" min="0" :max="colony.population" @input="rebalance('farmers')" />
          </div>
          <div :style="styles.sliderGroup">
            <label>Workers: {{ population.workers }}</label>
            <input v-model.number="population.workers" type="range" min="0" :max="colony.population" @input="rebalance('workers')" />
          </div>
          <div :style="styles.sliderGroup">
            <label>Scientists: {{ population.scientists }}</label>
            <input v-model.number="population.scientists" type="range" min="0" :max="colony.population" @input="rebalance('scientists')" />
          </div>
        </div>

        <!-- Buildings -->
        <div :style="styles.innerPanel">
          <h3 :style="styles.innerTitle">STRUCTURES</h3>
          <ul :style="styles.list">
            <li v-for="b in colony.buildings" :key="b.id" :style="styles.listItem">{{ b.name }}</li>
          </ul>
        </div>
      </div>
    </div>

    <!-- Build Queue -->
    <div :style="styles.queuePanel">
      <h3 :style="styles.title">CONSTRUCTION QUEUE</h3>
      <ul :style="styles.list">
        <li v-for="(item, idx) in colony.build_queue" :key="idx" :style="styles.queueItem">
          <div>
            <strong>{{ item.name }}</strong>
            <p :style="styles.subtitle">{{ item.progress }}/{{ item.cost }}</p>
          </div>
          <button :style="styles.btnDanger" @click="removeQueue(idx)">X</button>
        </li>
      </ul>
      
      <div :style="styles.buildOptions">
        <h4 :style="styles.innerTitle">AVAILABLE PROJECTS</h4>
        <div :style="styles.buildGrid">
          <div v-for="b in availableBuildings" :key="b.id" :style="styles.buildCard" @click="addQueue('building', b.id)">
            <strong>{{ b.name }}</strong>
            <span>{{ b.cost }} BC</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, onMounted, computed } from 'vue';
import { useGameStore } from '../store/gameStore';
import { useUIStore } from '../store/uiStore';
import { api } from '../api/client';

const gameStore = useGameStore();
const uiStore = useUIStore();

const colony = computed(() => {
  return gameStore.game?.player?.colonies.find((c: any) => c.id === uiStore.selectedColonyId);
});

const availableBuildings = ref<any[]>([]);

const population = reactive({
  farmers: 0,
  workers: 0,
  scientists: 0,
});

const styles = {
  layout: {
    display: 'grid',
    gridTemplateColumns: '1.3fr 1fr',
    gap: '1rem',
    height: '100%',
  },
  colonyPanel: {
    padding: '1rem',
    backgroundColor: '#1a1a3e',
    border: '1px solid #00ffff',
    borderRadius: '8px',
  },
  queuePanel: {
    padding: '1rem',
    backgroundColor: '#1a1a3e',
    border: '1px solid #ffd700',
    borderRadius: '8px',
  },
  panelHead: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '1rem',
  },
  title: {
    margin: 0,
    fontSize: '1.5rem',
    color: '#00ffff',
  },
  subtitle: {
    margin: '0.2rem 0 0',
    color: '#8888aa',
    fontSize: '0.8rem',
  },
  btn: {
    backgroundColor: '#2a2a5e',
    color: '#00ffff',
    border: '1px solid #00ffff',
    padding: '0.4rem 0.8rem',
    cursor: 'pointer',
    fontSize: '0.8rem',
  },
  btnDanger: {
    backgroundColor: '#5e2a2a',
    color: '#ff4444',
    border: '1px solid #ff4444',
    padding: '0.2rem 0.5rem',
    cursor: 'pointer',
  },
  statGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(4, 1fr)',
    gap: '0.8rem',
    marginBottom: '1rem',
  },
  statCard: {
    padding: '0.8rem',
    backgroundColor: '#070f24',
    border: '1px solid rgba(0, 255, 255, 0.2)',
    borderRadius: '4px',
    textAlign: 'center' as const,
  },
  statLabel: {
    display: 'block',
    fontSize: '0.7rem',
    color: '#8888aa',
  },
  statValue: {
    display: 'block',
    fontSize: '1.2rem',
    color: '#fff',
    margin: '0.2rem 0',
  },
  statSmall: {
    display: 'block',
    fontSize: '0.65rem',
    color: '#8888aa',
  },
  split: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '1rem',
  },
  innerPanel: {
    padding: '0.8rem',
    backgroundColor: '#070f24',
    borderRadius: '4px',
  },
  innerHead: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '0.8rem',
  },
  innerTitle: {
    margin: 0,
    fontSize: '0.9rem',
    color: '#ffd700',
  },
  sliderGroup: {
    marginBottom: '0.8rem',
  },
  list: {
    listStyle: 'none',
    padding: 0,
    margin: 0,
  },
  listItem: {
    padding: '0.4rem',
    borderBottom: '1px solid #2a2a5e',
    fontSize: '0.85rem',
  },
  queueItem: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '0.6rem',
    backgroundColor: '#070f24',
    border: '1px solid #ffd700',
    marginBottom: '0.5rem',
    borderRadius: '4px',
  },
  buildOptions: {
    marginTop: '1.5rem',
  },
  buildGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '0.5rem',
    marginTop: '0.5rem',
  },
  buildCard: {
    padding: '0.6rem',
    backgroundColor: '#2a2a5e',
    border: '1px solid #00ffff',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '0.8rem',
    display: 'flex',
    justifyContent: 'space-between',
  }
};

function syncPopulation() {
  if (!colony.value) return;
  population.farmers = colony.value.farmers || 0;
  population.workers = colony.value.workers || 0;
  population.scientists = colony.value.scientists || 0;
}

function rebalance(changed: string) {
  const total = colony.value.population;
  let sum = population.farmers + population.workers + population.scientists;
  if (sum <= total) return;
  
  const keys = ['farmers', 'workers', 'scientists'];
  for (const k of keys) {
    if (k === changed) continue;
    const diff = sum - total;
    const canReduce = Math.min(population[k], diff);
    population[k] -= canReduce;
    sum -= canReduce;
    if (sum <= total) break;
  }
}

async function savePopulation() {
  if (!gameStore.gameId || !uiStore.selectedColonyId) return;
  try {
    await api.colony.assign(gameStore.gameId, uiStore.selectedColonyId, population);
    gameStore.loadGame(gameStore.gameId);
  } catch (err) {
    console.error(err);
  }
}

async function addQueue(type, id) {
  if (!gameStore.gameId || !uiStore.selectedColonyId) return;
  try {
    await api.colony.buildQueue(gameStore.gameId, uiStore.selectedColonyId, { item_type: type, item_id: id });
    gameStore.loadGame(gameStore.gameId);
  } catch (err) {
    console.error(err);
  }
}

async function removeQueue(idx) {
  // Logic to remove from queue
}

onMounted(() => {
  syncPopulation();
  // Fetch available buildings etc.
});
</script>
