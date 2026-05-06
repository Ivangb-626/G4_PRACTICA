<template>
  <div :style="styles.panel">
    <div :style="styles.head">
      <div>
        <h2 :style="styles.title">IMPERIAL ACADEMY</h2>
        <p :style="styles.subtitle">Strategic recruitment of fleet admirals and planetary governors.</p>
      </div>
      <button :style="styles.btn" @click="fetchLeaders">REFRESH</button>
    </div>

    <div :style="styles.mainGrid">
      <!-- Candidates -->
      <div :style="styles.innerPanel">
        <h3 :style="styles.innerTitle">AVAILABLE CANDIDATES</h3>
        <div :style="styles.list">
          <div v-for="ld in availableLeaders" :key="ld.id" :style="styles.card">
            <div>
              <strong :style="{ color: '#fff' }">{{ ld.name }}</strong>
              <div :style="{ color: '#00ffff', fontSize: '0.8rem' }">{{ ld.title }}</div>
              <div :style="{ color: '#8888aa', fontSize: '0.7rem', marginTop: '0.3rem' }">{{ ld.description }}</div>
            </div>
            <div :style="{ textAlign: 'right' as const }">
              <div :style="{ color: '#ffd700', fontSize: '0.9rem' }">{{ ld.hire_cost }} BC</div>
              <button :style="styles.btnSmall" @click="hireLeader(ld.id)">HIRE</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Active Staff -->
      <div :style="styles.innerPanel">
        <h3 :style="styles.innerTitle">ACTIVE STAFF</h3>
        <div :style="styles.list">
          <div v-for="ld in hiredLeaders" :key="ld.uid" :style="styles.cardActive">
            <div>
              <strong :style="{ color: '#fff' }">{{ ld.name }}</strong>
              <div :style="{ color: '#00ffff', fontSize: '0.8rem' }">{{ ld.title }}</div>
            </div>
            <div :style="{ textAlign: 'right' as const }">
              <div :style="{ color: ld.assigned_to ? '#44ee44' : '#ffd700', fontSize: '0.8rem' }">
                {{ ld.assigned_to ? 'ASSIGNED' : 'UNASSIGNED' }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useGameStore } from '../store/gameStore';
import { api } from '../api/client';

const gameStore = useGameStore();

const hiredLeaders = ref<any[]>([]);
const availableLeaders = ref<any[]>([]);

const styles = {
  panel: {
    padding: '1.5rem',
    backgroundColor: '#070f24',
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
  mainGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '1.5rem',
  },
  innerPanel: {
    padding: '1.2rem',
    backgroundColor: '#1a1a3e',
    border: '1px solid rgba(0, 255, 255, 0.3)',
    borderRadius: '8px',
  },
  innerTitle: {
    margin: '0 0 1.5rem',
    fontSize: '1.2rem',
    color: '#ffd700',
  },
  list: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '1rem',
  },
  card: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '1rem',
    backgroundColor: '#070f24',
    border: '1px solid #1a1a3e',
    borderRadius: '4px',
  },
  cardActive: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '1rem',
    backgroundColor: '#070f24',
    border: '1px solid #00ffff',
    borderRadius: '4px',
  },
  btn: {
    backgroundColor: '#1a1a3e',
    color: '#00ffff',
    border: '2px solid #00ffff',
    padding: '0.6rem 1.2rem',
    cursor: 'pointer',
  },
  btnSmall: {
    backgroundColor: '#2a2a5e',
    color: '#00ffff',
    border: '1px solid #00ffff',
    padding: '0.3rem 0.6rem',
    cursor: 'pointer',
    fontSize: '0.75rem',
    marginTop: '0.5rem',
  }
};

async function fetchLeaders() {
  if (!gameStore.gameId) return;
  try {
    const res = await api.leaders.list(gameStore.gameId);
    const avail = await api.leaders.available(gameStore.gameId);
    hiredLeaders.value = res.leaders || [];
    availableLeaders.value = avail.available_leaders || [];
  } catch (err) {
    console.error(err);
  }
}

async function hireLeader(id: string) {
  if (!gameStore.gameId) return;
  try {
    await api.leaders.hire(gameStore.gameId, id);
    fetchLeaders();
  } catch (err) {
    console.error(err);
  }
}

onMounted(() => {
  if (gameStore.gameId) {
    fetchLeaders();
  }
});
</script>
