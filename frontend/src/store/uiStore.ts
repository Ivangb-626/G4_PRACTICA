import { defineStore } from 'pinia';

export type ScreenName =
  | 'main_menu'
  | 'new_game'
  | 'galaxy'
  | 'colony'
  | 'research'
  | 'fleet'
  | 'ship_designer'
  | 'diplomacy'
  | 'leaders'
  | 'espionage'
  | 'combat'
  | 'turn_summary'
  | 'council'
  | 'inventory'
  | 'victory';

export const useUIStore = defineStore('ui', {
  state: () => ({
    activeScreen: 'main_menu' as ScreenName,
    selectedSystemId: null as string | null,
    selectedColonyId: null as string | null,
    sidebarOpen: false,
    cheatInput: '',
    notification: null as string | null,
    eventLogOpen: false,
    shortcutsOpen: false,
    gameSpeed: 'normal' as 'pausa' | 'lenta' | 'normal' | 'rapida',
  }),
  actions: {
    setScreen(screen: ScreenName) {
      this.activeScreen = screen;
    },
    selectSystem(id: string | null) {
      this.selectedSystemId = id;
    },
    selectColony(id: string | null) {
      this.selectedColonyId = id;
    },
    toggleSidebar() {
      this.sidebarOpen = !this.sidebarOpen;
    },
    setCheatInput(input: string) {
      this.cheatInput = input;
    },
    showNotification(msg: string) {
      this.notification = msg;
    },
    clearNotification() {
      this.notification = null;
    },
    openEventLog() {
      this.eventLogOpen = true;
    },
    closeEventLog() {
      this.eventLogOpen = false;
    },
    toggleShortcuts() {
      this.shortcutsOpen = !this.shortcutsOpen;
    },
    closeShortcuts() {
      this.shortcutsOpen = false;
    },
    setGameSpeed(speed: 'pausa' | 'lenta' | 'normal' | 'rapida') {
      this.gameSpeed = speed;
    }
  }
});
