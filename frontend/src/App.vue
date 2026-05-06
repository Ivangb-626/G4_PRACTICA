<template>
  <div :style="styles.appShell">
    <!-- TopBar is only shown in-game -->
    <TopBar v-if="gameStore.gameId && uiStore.activeScreen !== 'main_menu' && uiStore.activeScreen !== 'new_game'" />

    <main :style="styles.main">
      <router-view />
    </main>

    <!-- Global Modals -->
    <EventLogModal v-if="uiStore.eventLogOpen" />
    <Notification v-if="uiStore.notification" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue';
import { useUIStore } from './store/uiStore';
import { useGameStore } from './store/gameStore';

// Components (Refactored versions)
import MainMenu from './views/Dashboard.vue';
import NewGame from './views/GameView.vue';
import GalaxyMap from './views/GalaxyMap.vue';
import ColonyScreen from './views/ColonyView.vue';
import ResearchScreen from './views/TechTree.vue';
import FleetScreen from './views/FleetManager.vue';
import ShipDesigner from './views/SystemView.vue';
import DiplomacyScreen from './views/DiplomacyView.vue';
import LeadersScreen from './views/LeadersView.vue';
import EspionageScreen from './views/EspionageView.vue';
import CombatScreen from './views/CombatResult.vue';
import VictoryScreen from './views/VictoryScreen.vue';
import TopBar from './views/BaseButton.vue'; // Need to refactor this to a proper TopBar
import EventLogModal from './views/LoadingSpinner.vue'; // Need to refactor this
import Notification from './views/ErrorAlert.vue';

const uiStore = useUIStore();
const gameStore = useGameStore();

const styles = {
  appShell: {
    minHeight: '100vh',
    backgroundColor: '#070f24',
    color: '#e0e0ff',
    fontFamily: 'monospace',
    display: 'flex',
    flexDirection: 'column' as const,
  },
  main: {
    flex: 1,
    padding: '1rem',
    overflow: 'auto',
  }
};

const handleKeyDown = (e: KeyboardEvent) => {
  // Ignore if typing in input
  if (['INPUT', 'TEXTAREA', 'SELECT'].includes((e.target as HTMLElement).tagName)) return;

  if (!gameStore.gameId) return;

  switch (e.key.toUpperCase()) {
    case 'T': gameStore.endTurn(); break;
    case 'G': uiStore.setScreen('galaxy'); break;
    case 'C': uiStore.setScreen('colony'); break;
    case 'R': uiStore.setScreen('research'); break;
    case 'F': uiStore.setScreen('fleet'); break;
    case 'L': uiStore.setScreen('leaders'); break;
    case 'D': uiStore.setScreen('diplomacy'); break;
    case 'S': uiStore.setScreen('ship_designer'); break;
    case 'ESCAPE': 
      if (uiStore.eventLogOpen) uiStore.closeEventLog();
      else uiStore.setScreen('galaxy'); 
      break;
  }
};

onMounted(() => {
  window.addEventListener('keydown', handleKeyDown);
});

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown);
});
</script>
