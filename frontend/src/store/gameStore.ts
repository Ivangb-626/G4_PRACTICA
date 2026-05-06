import { defineStore } from 'pinia';
import { api } from '../api/client';

export const useGameStore = defineStore('game', {
  state: () => ({
    token: localStorage.getItem('token') || null as string | null,
    username: localStorage.getItem('username') || null as string | null,
    gameId: null as string | null,
    game: null as any | null,
    games: [] as any[],
    galaxy: null as any | null,
    colonies: [] as any[],
    fleets: [] as any[],
    designs: [] as any[],
    techState: null as any | null,
    relations: [] as any[],
    leaders: [] as any[],
    availableLeaders: [] as any[],
    tacticalState: null as any | null,
    events: [] as any[],
    aiActions: [] as any[],
  }),
  actions: {
    async login(u: string, p: string) {
      // API call to login
    },
    async register(u: string, p: string) {
      // API call to register
    },
    logout() {
      this.token = null;
      this.username = null;
      localStorage.removeItem('token');
      localStorage.removeItem('username');
    },
    async createGame(opts: any) {
      // API call to /api/game/new
    },
    async loadGame(id: string) {
      // API call to /api/game/<id>
    },
    async listGames() {
      // API call to /api/game/list
    },
    async endTurn() {
      // API call to /api/game/<id>/end-turn
    },
    async fetchGalaxy() {
      if (!this.gameId) throw new Error('No active game');
      this.galaxy = await api.galaxy.get(this.gameId);
    },
    async fetchResearch() {
      if (!this.gameId) throw new Error('No active game');
      this.techState = await api.research.get(this.gameId);
    },
    async fetchFleets() {
      if (!this.gameId) throw new Error('No active game');
      this.fleets = await api.fleet.list(this.gameId);
    },
  }
});
