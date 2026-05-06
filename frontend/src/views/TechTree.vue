<template>
  <div :style="styles.panel">
    <div :style="styles.head">
      <div>
        <h2 :style="styles.title">RESEARCH & DEVELOPMENT</h2>
        <p :style="styles.subtitle">
          {{ gameStore.techState?.current_research ? `CURRENT PROJECT: ${gameStore.techState.current_research.toUpperCase()}` : 'IDLE' }}
        </p>
      </div>
      <button :style="styles.btn" @click="gameStore.fetchResearch()">REFRESH</button>
    </div>

    <!-- Breakthrough Progress -->
    <div v-if="gameStore.techState?.chance > 0" :style="styles.breakthrough">
      <div :style="styles.progressLabel">BREAKTHROUGH PROBABILITY: {{ Math.round(gameStore.techState.chance) }}%</div>
      <div :style="styles.progressBar">
        <div :style="{ ...styles.progressFill, width: gameStore.techState.chance + '%' }"></div>
      </div>
    </div>

    <div :style="styles.fieldList">
      <div v-for="field in gameStore.techState?.available_techs?.fields || []" :key="field.field" :style="styles.fieldCard">
        <h3 :style="styles.fieldTitle">{{ field.field.toUpperCase() }}</h3>
        
        <div v-for="level in field.levels" :key="level.level" :style="styles.levelRow">
          <div :style="styles.optionGrid">
            <div v-for="opt in level.options" :key="opt.tech_id" :style="getOptionStyle(opt.status)">
              <div>
                <strong :style="{ color: '#fff' }">{{ opt.name.toUpperCase() }}</strong>
                <p :style="styles.subtitle">{{ opt.description }}</p>
                <small :style="{ color: '#8888aa', fontSize: '0.7rem' }">COST: {{ opt.base_cost }} RP</small>
              </div>
              <button v-if="opt.status === 'available'" :style="styles.btnSmall" @click="selectTech(opt.tech_id)">RESEARCH</button>
              <span v-else :style="styles.statusBadge">{{ opt.status.toUpperCase() }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useGameStore } from '../store/gameStore';
import { api } from '../api/client';
import { Theme, createPanelStyle, btnStyle } from '../styles/styleSystem';

const gameStore = useGameStore();

const styles = {
  panel: createPanelStyle(),
  head: { display: 'flex', justifyContent: 'space-between', marginBottom: '2rem', borderBottom: `2px solid ${Theme.colors.primary}`, paddingBottom: '1rem' },
  title: { margin: 0, fontSize: '2rem', color: Theme.colors.primary, letterSpacing: '0.2em' },
  subtitle: { margin: '0.3rem 0 0', color: Theme.colors.textMuted, fontSize: '0.9rem' },
  btn: btnStyle(),
  btnSmall: { ...btnStyle(), padding: '0.3rem 0.6rem', fontSize: '0.75rem' },
  fieldList: { display: 'flex', flexDirection: 'column' as const, gap: '1.5rem' },
  fieldCard: { padding: '1.2rem', backgroundColor: Theme.colors.bgDark, border: `1px solid ${Theme.colors.border}`, borderRadius: '8px' },
  fieldTitle: { margin: '0 0 1rem', fontSize: '1.2rem', color: Theme.colors.secondary, borderBottom: `1px solid ${Theme.colors.secondary}`, paddingBottom: '0.3rem' },
  breakthrough: { marginBottom: '1rem', padding: '1rem', backgroundColor: Theme.colors.bgDark, border: `1px solid ${Theme.colors.secondary}` },
  progressLabel: { fontSize: '0.8rem', color: Theme.colors.secondary, marginBottom: '0.5rem' },
  progressBar: { width: '100%', height: '8px', backgroundColor: Theme.colors.bgDark, border: `1px solid ${Theme.colors.border}`, borderRadius: '4px', overflow: 'hidden' as const },
  progressFill: { height: '100%', backgroundColor: Theme.colors.secondary, transition: 'width 0.3s ease' },
  levelRow: { marginBottom: '1rem' },
  optionGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '0.6rem' },
  statusBadge: { fontSize: '0.7rem', padding: '0.2rem 0.5rem', backgroundColor: Theme.colors.bgDark, color: Theme.colors.textMuted, border: `1px solid ${Theme.colors.border}`, borderRadius: '4px', alignSelf: 'center' as const },
};

function getOptionStyle(status: string) {
  let borderColor = 'rgba(112, 166, 214, 0.18)';
  if (status === 'available') borderColor = '#00ffff';
  if (status === 'current') borderColor = '#ffd700';
  if (status === 'researched') borderColor = '#44ee44';
  return { display: 'flex', justifyContent: 'space-between', padding: '0.8rem', backgroundColor: '#070f24', border: `1px solid ${borderColor}`, borderRadius: '4px' };
}

async function selectTech(techId: string) {
  if (!gameStore.gameId) return;
  try {
    await api.research.select(gameStore.gameId, techId);
    gameStore.fetchResearch();
  } catch (err) { console.error(err); }
}

onMounted(() => { if (gameStore.gameId) gameStore.fetchResearch(); });
</script>
