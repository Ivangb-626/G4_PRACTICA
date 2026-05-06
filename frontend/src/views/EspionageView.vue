<template>
  <div :style="styles.panel">
    <div :style="styles.head">
      <div>
        <h2 :style="styles.title">INTELLIGENCE NETWORK</h2>
        <p :style="styles.subtitle">Shadow operations, deep cover agents, and counter-intelligence protocols.</p>
      </div>
      <button :style="styles.btn" @click="fetchSpies">REFRESH</button>
    </div>

    <div :style="styles.mainGrid">
      <!-- Roster -->
      <div :style="styles.innerPanel">
        <div :style="styles.innerHead">
          <h3 :style="styles.innerTitle">ACTIVE AGENTS</h3>
          <div :style="{ display: 'flex', gap: '0.5rem' }">
            <select v-model="recruitLevel" :style="styles.selectSmall">
              <option :value="1">LVL 1 (50 BC)</option>
              <option :value="2">LVL 2 (100 BC)</option>
              <option :value="3">LVL 3 (200 BC)</option>
              <option :value="4">LVL 4 (400 BC)</option>
            </select>
            <button :style="styles.btnSmall" @click="recruitSpy">RECRUIT</button>
          </div>
        </div>

        <div :style="styles.spyList">
          <div v-for="spy in spies" :key="spy.id" 
               :style="getSpyCardStyle(spy.id)"
               @click="selectedSpyId = spy.id">
            <div :style="{ display: 'flex', justifyContent: 'space-between' }">
              <strong :style="{ color: '#fff' }">{{ spy.name }}</strong>
              <span :style="{ color: '#00ffff', fontSize: '0.8rem' }">L{{ spy.level }} · {{ spy.level_name }}</span>
            </div>
            <div :style="getStatusStyle(spy)">{{ spy.status.toUpperCase() }}</div>
          </div>
        </div>
      </div>

      <!-- Control -->
      <div :style="styles.innerPanel">
        <h3 :style="styles.innerTitle">MISSION CONTROL</h3>
        <div v-if="!selectedSpyId" :style="styles.placeholder">SELECT AN AGENT TO BEGIN OPERATIONS.</div>
        <div v-else :style="styles.form">
          <label :style="styles.label">TARGET EMPIRE</label>
          <input v-model="targetPlayer" :style="styles.input" placeholder="e.g. ai_0" />

          <label :style="styles.label">OPERATION TYPE</label>
          <select v-model="selectedMission" :style="styles.input">
            <option v-for="m in missionTypes" :key="m" :value="m">{{ m.toUpperCase().replace('_', ' ') }}</option>
          </select>

          <div :style="{ display: 'flex', gap: '1rem', marginTop: '1rem' }">
            <button :style="styles.btnDanger" @click="assignMission">LAUNCH MISSION</button>
            <button :style="styles.btn" @click="assignDefense">DEFENSE</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useGameStore } from '../store/gameStore';
import { api } from '../api/client';

const gameStore = useGameStore();

const spies = ref<any[]>([]);
const missionTypes = ref<string[]>(['info_probe', 'tech_espionage', 'sabotage']);
const selectedSpyId = ref<string | null>(null);
const targetPlayer = ref('');
const selectedMission = ref('info_probe');
const recruitLevel = ref(1);

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
  innerHead: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '1rem',
  },
  innerTitle: {
    margin: 0,
    fontSize: '1.2rem',
    color: '#ffd700',
  },
  spyList: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '0.8rem',
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
  },
  btnDanger: {
    flex: 1,
    backgroundColor: '#5e2a2a',
    color: '#ff4444',
    border: '1px solid #ff4444',
    padding: '0.6rem',
    cursor: 'pointer',
  },
  selectSmall: {
    backgroundColor: '#070f24',
    color: '#00ffff',
    border: '1px solid #00ffff',
    fontSize: '0.75rem',
  },
  placeholder: {
    padding: '4rem',
    textAlign: 'center' as const,
    color: '#8888aa',
    fontStyle: 'italic',
  },
  form: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '1rem',
  },
  label: {
    fontSize: '0.8rem',
    color: '#8888aa',
  },
  input: {
    backgroundColor: '#070f24',
    color: '#fff',
    border: '1px solid #00ffff',
    padding: '0.6rem',
    borderRadius: '4px',
  }
};

function getSpyCardStyle(id: string) {
  const isSelected = selectedSpyId.value === id;
  return {
    padding: '1rem',
    backgroundColor: isSelected ? '#2a2a5e' : '#070f24',
    border: isSelected ? '1px solid #00ffff' : '1px solid #1a1a3e',
    borderRadius: '4px',
    cursor: 'pointer',
  };
}

function getStatusStyle(spy: any) {
  let color = '#44ee44';
  if (spy.status === 'compromised') color = '#ff4444';
  if (spy.status === 'on_mission') color = '#ffd700';

  return {
    fontSize: '0.75rem',
    marginTop: '0.4rem',
    color,
  };
}

async function fetchSpies() {
  if (!gameStore.gameId) return;
  try {
    const res = await api.espionage.list(gameStore.gameId);
    spies.value = res || [];
  } catch (err) {
    console.error(err);
  }
}

async function recruitSpy() {
  if (!gameStore.gameId) return;
  try {
    await api.espionage.recruit(gameStore.gameId, recruitLevel.value);
    fetchSpies();
  } catch (err) {
    console.error(err);
  }
}

async function assignMission() {
  if (!gameStore.gameId || !selectedSpyId.value) return;
  try {
    await api.espionage.mission(gameStore.gameId, selectedSpyId.value, targetPlayer.value, selectedMission.value);
    fetchSpies();
  } catch (err) {
    console.error(err);
  }
}

async function assignDefense() {
  // Defense logic
}

onMounted(() => {
  if (gameStore.gameId) {
    fetchSpies();
  }
});
</script>
