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
    selectedStarIndex: null as number | null,
    selectedColonyId: null as string | null,
    sidebarOpen: false,
    cheatInput: '',
    notification: null as string | null,
    eventLogOpen: false,
  }),
  actions: {
    setScreen(screen: ScreenName) {
      this.activeScreen = screen;
    },
    selectStar(index: number | null) {
      this.selectedStarIndex = index;
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
    }
  }
});
