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
          <button :style="styles.btnDanger" @click="removeQueue(Number(idx))">X</button>
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
import { ref, reactive, onMounted, computed } from 'vue';
import { useGameStore } from '../store/gameStore';
import { useUIStore } from '../store/uiStore';
import { api } from '../api/client';
import { Theme, createPanelStyle, btnStyle } from '../styles/styleSystem';

const gameStore = useGameStore();
const uiStore = useUIStore();

const colony = computed(() => {
  return gameStore.game?.player?.colonies.find((c: any) => c.id === uiStore.selectedColonyId);
});

const availableBuildings = ref<any[]>([]);

const population = reactive<Record<'farmers' | 'workers' | 'scientists', number>>({
  farmers: 0,
  workers: 0,
  scientists: 0,
});

const styles = {
  layout: { display: 'grid', gridTemplateColumns: '1.3fr 1fr', gap: '1.5rem', height: '100%' },
  colonyPanel: createPanelStyle(),
  queuePanel: createPanelStyle(true),
  panelHead: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' },
  title: { margin: 0, fontSize: '2rem', color: Theme.colors.primary, letterSpacing: '0.1em', textShadow: Theme.effects.glow },
  subtitle: { margin: '0.2rem 0 0', color: Theme.colors.textMuted, fontSize: '0.9rem' },
  btn: btnStyle(),
  btnDanger: {
    backgroundColor: 'transparent',
    color: Theme.colors.danger,
    border: `1px solid ${Theme.colors.danger}`,
    padding: '0.2rem 0.5rem',
    cursor: 'pointer',
  },
  statGrid: { display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '1.5rem' },
  statCard: { padding: '1rem', backgroundColor: Theme.colors.bgDark, border: `1px solid ${Theme.colors.border}`, borderRadius: '8px', textAlign: 'center' as const },
  statLabel: { display: 'block', fontSize: '0.7rem', color: Theme.colors.textMuted },
  statValue: { display: 'block', fontSize: '1.6rem', color: Theme.colors.primary, marginTop: '0.5rem' },
  statSmall: { display: 'block', fontSize: '0.65rem', color: Theme.colors.textMuted },
  split: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' },
  innerPanel: { padding: '1rem', backgroundColor: Theme.colors.bgDark, borderRadius: '4px' },
  innerHead: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.8rem' },
  innerTitle: { margin: '0 0 1rem', fontSize: '1rem', color: Theme.colors.secondary },
  sliderGroup: { marginBottom: '1rem' },
  list: { listStyle: 'none', padding: 0, margin: 0 },
  listItem: { padding: '0.4rem', borderBottom: `1px solid ${Theme.colors.border}`, fontSize: '0.85rem' },
  queueItem: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '0.6rem',
    backgroundColor: Theme.colors.bgDark,
    border: `1px solid ${Theme.colors.secondary}`,
    marginBottom: '0.5rem',
    borderRadius: '4px',
  },
  buildOptions: { marginTop: '1.5rem' },
  buildGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginTop: '0.5rem' },
  buildCard: {
    padding: '0.6rem',
    backgroundColor: Theme.colors.bgDark,
    border: `1px solid ${Theme.colors.primary}`,
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '0.8rem',
    display: 'flex',
    justifyContent: 'space-between',
  },
};

function syncPopulation() {
  if (!colony.value) return;
  population.farmers = colony.value.farmers || 0;
  population.workers = colony.value.workers || 0;
  population.scientists = colony.value.scientists || 0;
}

type PopKey = 'farmers' | 'workers' | 'scientists';

function rebalance(changed: PopKey) {
  const total = colony.value.population;
  let sum = population.farmers + population.workers + population.scientists;
  if (sum <= total) return;

  const keys: PopKey[] = ['farmers', 'workers', 'scientists'];
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

async function addQueue(type: 'building' | 'ship', id: string) {
  if (!gameStore.gameId || !uiStore.selectedColonyId) return;
  try {
    await api.colony.buildQueue(gameStore.gameId, uiStore.selectedColonyId, { item_type: type, item_id: id });
    gameStore.loadGame(gameStore.gameId);
  } catch (err) {
    console.error(err);
  }
}

async function removeQueue(idx: number) {
  if (!gameStore.gameId || !uiStore.selectedColonyId) return;
  try {
    await api.colony.removeQueueItem(gameStore.gameId, uiStore.selectedColonyId, idx);
    gameStore.loadGame(gameStore.gameId);
  } catch (err) {
    console.error(err);
  }
}

onMounted(() => {
  syncPopulation();
  // Fetch available buildings etc.
});
</script>
