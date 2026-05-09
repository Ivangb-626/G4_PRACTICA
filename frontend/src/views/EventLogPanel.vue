<template>
  <Transition name="fade">
    <div v-if="isVisible" :style="styles.overlay">
      <div :style="styles.modal">
        <h2 :style="styles.title">LOG DEL TURNO {{ turn }}</h2>
        <div :style="styles.eventList">
          <div v-if="!events.length" :style="styles.empty">No hay eventos registrados aun.</div>
          <div v-for="(event, index) in events" :key="index" :style="styles.eventItem">
            <span :style="styles.eventType">{{ formatEventType(String(event.type || 'evento')) }}:</span>
            <span :style="styles.eventDetails">{{ formatEventDetails(event) }}</span>
          </div>
        </div>
        <button :style="styles.button" @click="uiStore.closeEventLog()">CERRAR</button>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useUIStore } from '../store/uiStore';
import { useGameStore } from '../store/gameStore';

const uiStore = useUIStore();
const gameStore = useGameStore();

const isVisible = computed(() => uiStore.eventLogOpen);
const events = computed(() => gameStore.lastTurnEvents);
const turn = computed(() => gameStore.game?.turn ? Math.max(1, gameStore.game.turn - 1) : 0); // Display previous turn's number

const formatEventType = (type: string) => {
  switch (type) {
    case 'combat_resolved': return 'Combat';
    case 'fleet_arrival': return 'Fleet Arrival';
    case 'research_complete': return 'Research Complete';
    case 'construction_complete': return 'Construction Complete';
    case 'leader_offer': return 'Leader Available';
    case 'spy_caught': return 'Spy Caught';
    case 'tech_stolen': return 'Technology Stolen';
    case 'espionage_sabotage_industry': return 'Industrial Sabotage';
    case 'espionage_sabotage_science': return 'Scientific Sabotage';
    case 'diplomacy_error': return 'Diplomacy Error';
    case 'espionage_error': return 'Espionage Error';
    case 'antaran_error': return 'Antaran Error';
    case 'assimilation_error': return 'Assimilation Error';
    case 'event_error': return 'Event Error';
    case 'artifacts_found': return 'Artifacts Found';
    case 'natives_met': return 'Natives Met';
    case 'splinter_annexed': return 'Splinter Colony Annexed';
    case 'antaranos_escaped': return 'Antarans Escaped';
    case 'leader_hired': return 'Leader Hired';
    case 'leader_expired': return 'Leader Expired';
    default: return type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  }
};

const formatEventDetails = (event: any) => {
  switch (event.type) {
    case 'combat_resolved': return `System ${event.system_id}: ${event.winner} vs ${event.defender}`;
    case 'fleet_arrival': return `Fleet ${event.fleet_id} arrived at ${event.system_id}`;
    case 'research_complete': return `New technology researched: ${event.tech_id}`;
    case 'construction_complete': return `Colony ${event.colony_id} completed ${event.item.item_id}`;
    case 'leader_offer': return `New leader ${event.leader_id} available for hire.`;
    case 'spy_caught': return `Your spy ${event.spy_id} was caught in ${event.at}!`;
    case 'tech_stolen': return `Your spy ${event.spy_id} stole ${event.tech_id} from ${event.from}!`;
    case 'espionage_sabotage_industry': return `Industrial sabotage in ${event.colony_id} reduced production by ${event.loss} PP.`;
    case 'espionage_sabotage_science': return `Scientific sabotage reduced research progress by ${event.loss} RP.`;
    case 'artifacts_found': return `Ancient artifacts found on ${event.colony_id}!`;
    case 'natives_met': return `Natives encountered on ${event.colony_id}! Food production increased.`;
    case 'splinter_annexed': return `Splinter colony ${event.colony_id} successfully annexed.`;
    case 'antaranos_escaped': return event.message;
    case 'leader_hired': return `Leader ${event.leader_id} hired for ${event.owner}.`;
    case 'leader_expired': return `Leader ${event.leader_id} has expired.`;
    case 'diplomacy_error':
    case 'espionage_error':
    case 'antaran_error':
    case 'assimilation_error':
    case 'event_error': return `An error occurred: ${event.error}`;
    default: return event.message || JSON.stringify(event);
  }
};

const styles = {
  overlay: {
    position: 'fixed' as const,
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1000,
  },
  modal: {
    backgroundColor: '#1a1a3e',
    padding: '2rem',
    borderRadius: '8px',
    border: '2px solid #00ffff',
    width: '80%',
    maxWidth: '700px',
    maxHeight: '80%',
    overflowY: 'auto' as const,
    boxShadow: '0 0 30px rgba(0, 255, 255, 0.5)',
    color: '#eee',
    position: 'relative' as const,
  },
  title: {
    color: '#00ffff',
    textAlign: 'center' as const,
    marginBottom: '1.5rem',
    fontSize: '1.8rem',
    textShadow: '0 0 10px #00ffff',
  },
  eventList: {
    marginBottom: '1.5rem',
  },
  empty: {
    color: '#8888aa',
    padding: '0.8rem',
    border: '1px dashed rgba(0, 255, 255, 0.25)',
    borderRadius: '4px',
  },
  eventItem: {
    backgroundColor: '#071536',
    padding: '0.8rem',
    marginBottom: '0.5rem',
    borderRadius: '4px',
    borderLeft: '3px solid #00ffff',
    display: 'flex',
    gap: '0.5rem',
  },
  eventType: {
    fontWeight: 'bold' as const,
    color: '#00ffff',
    flexShrink: 0,
  },
  eventDetails: {
    fontSize: '0.9rem',
    color: '#ccc',
  },
  button: {
    backgroundColor: '#00ffff',
    color: '#1a1a3e',
    border: 'none',
    padding: '0.8rem 1.5rem',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '1rem',
    fontWeight: 'bold' as const,
    display: 'block',
    margin: '0 auto',
    marginTop: '1.5rem',
    transition: 'background-color 0.2s',
  },
};
</script>

<style scoped>
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.5s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
