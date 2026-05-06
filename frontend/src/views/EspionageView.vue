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
import { ref, onMounted } from 'vue';
import { useGameStore } from '../store/gameStore';
import { api } from '../api/client';
import { Theme, createPanelStyle, btnStyle } from '../styles/styleSystem';

const gameStore = useGameStore();
const spies = ref<any[]>([]);
const selectedSpyId = ref<string | null>(null);
const recruitLevel = ref<number>(1);
const targetPlayer = ref<string>('');
const selectedMission = ref<string>('steal_tech');
const missionTypes = ['steal_tech', 'sabotage', 'assassinate', 'incite_rebellion'];

const styles = {
  panel: createPanelStyle(),
  head: { display: 'flex', justifyContent: 'space-between', marginBottom: '2rem', borderBottom: `1px solid ${Theme.colors.border}`, paddingBottom: '1rem' },
  title: { margin: 0, fontSize: '2rem', color: Theme.colors.primary, letterSpacing: '0.2em', textShadow: Theme.effects.glow },
  subtitle: { margin: '0.3rem 0 0', color: Theme.colors.textMuted, fontSize: '0.9rem' },
  mainGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' },
  innerPanel: createPanelStyle(),
  innerHead: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' },
  innerTitle: { margin: '0 0 1rem', fontSize: '1.2rem', color: Theme.colors.secondary },
  spyList: { display: 'flex', flexDirection: 'column' as const, gap: '0.8rem' },
  btn: btnStyle(),
  btnSmall: { ...btnStyle(), padding: '0.3rem 0.6rem', fontSize: '0.75rem' },
  btnDanger: {
    ...btnStyle(),
    borderColor: Theme.colors.danger,
    color: Theme.colors.danger,
    backgroundColor: 'transparent',
    flex: 1,
  },
  selectSmall: { backgroundColor: Theme.colors.bgDark, color: Theme.colors.primary, border: `1px solid ${Theme.colors.primary}`, fontSize: '0.75rem', padding: '0.3rem' },
  placeholder: { padding: '4rem', textAlign: 'center' as const, color: Theme.colors.textMuted, fontStyle: 'italic' },
  form: { display: 'flex', flexDirection: 'column' as const, gap: '1rem' },
  label: { fontSize: '0.8rem', color: Theme.colors.textMuted },
  input: { backgroundColor: Theme.colors.bgDark, color: Theme.colors.text, border: `1px solid ${Theme.colors.primary}`, padding: '0.6rem', borderRadius: '4px' },
};

function getSpyCardStyle(id: string) {
  const isSelected = selectedSpyId.value === id;
  return {
    padding: '1rem',
    backgroundColor: isSelected ? Theme.colors.bgGlass : Theme.colors.bgDark,
    border: `1px solid ${isSelected ? Theme.colors.primary : Theme.colors.border}`,
    borderRadius: '4px',
    cursor: 'pointer',
    transition: 'all 0.2s',
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
