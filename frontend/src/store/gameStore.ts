import { defineStore } from 'pinia'
import { api } from '../api/client'
import { useAuthStore } from './authStore'

type AnyObj = Record<string, any>

export const useGameStore = defineStore('game', {
  state: () => ({
    gameId: null as string | null,
    game: null as AnyObj | null,
    games: [] as AnyObj[],
    galaxy: null as AnyObj | null,
    colonies: [] as AnyObj[],
    fleets: [] as AnyObj[],
    designs: [] as AnyObj[],
    techState: null as AnyObj | null,
    diplomacy: null as AnyObj | null,
    leaders: [] as AnyObj[],
    availableLeaders: [] as AnyObj[],
    spies: [] as AnyObj[],
    council: null as AnyObj | null,
    score: null as AnyObj | null,
    lastTurnEvents: [] as AnyObj[],
    aiActions: [] as AnyObj[],
    lastTurnResult: null as AnyObj | null,
  }),
  getters: {
    /** True si el imperio investigo Interphased Drive (rango ilimitado). */
    hasUnlimitedRange(state): boolean {
      const techs = state.game?.player?.technologies?.researched || []
      return techs.some(
        (t: AnyObj) => t.tech_id === 'interphased_drive' && t.status !== 'discarded',
      )
    },
    /**
     * Numero maximo de saltos interestelares basado en techs de Power.
     * Devuelve Infinity si Interphased Drive esta investigada.
     */
    maxJumps(state): number {
      const techs = state.game?.player?.technologies?.researched || []
      const hasTop = techs.some(
        (t: AnyObj) => t.tech_id === 'interphased_drive' && t.status !== 'discarded',
      )
      if (hasTop) return Number.POSITIVE_INFINITY
      const power = techs.filter((t: AnyObj) => t.field === 'power' && t.status !== 'discarded')
      let base = Math.max(1, power.length)
      const flags = state.game?.player?.race?.traits?.flags || {}
      if (flags.transdimensional) base += 1
      return base
    },
    /** Si la partida ha terminado en victoria/derrota. */
    isGameOver(state): boolean {
      return Boolean(state.game?.victory_condition)
    },
  },
  actions: {
    // ----- Auth wrappers -----
    async login(username: string, password: string) {
      const res = await api.auth.login(username, password)
      const auth = useAuthStore()
      auth.setAuth(res.token, res.username)
      return res
    },
    async register(username: string, email: string, password: string) {
      return api.auth.register(username, email, password)
    },
    logout() {
      const auth = useAuthStore()
      auth.logout()
      this.$reset()
    },

    // ----- Game lifecycle -----
    async fetchGames() {
      this.games = await api.game.list()
    },
    async createGame(config: AnyObj) {
      const res = await api.game.new(config)
      this.gameId = res.game_id
      await this.loadGame(res.game_id)
      return res
    },
    async loadGame(id: string) {
      this.gameId = id
      this.game = await api.game.get(id)
      await Promise.all([this.fetchGalaxy(), this.fetchColonies(), this.fetchFleets()])
    },
    async deleteGame(id: string) {
      await api.game.delete(id)
      if (this.gameId === id) {
        this.gameId = null
        this.game = null
      }
    },
    async endTurn() {
      if (!this.gameId) throw new Error('No active game')
      const res = await api.game.endTurn(this.gameId)
      this.lastTurnResult = res
      this.lastTurnEvents = res.events || []
      this.aiActions = res.ai_actions || []
      this.game = res.game_state || this.game
      await Promise.all([this.fetchGalaxy(), this.fetchColonies(), this.fetchFleets(), this.fetchResearch()])
      return res
    },
    async fetchScore() {
      if (!this.gameId) return
      this.score = await api.game.score(this.gameId)
    },

    // ----- Galaxy / colonies / fleets -----
    async fetchGalaxy() {
      if (!this.gameId) return
      this.galaxy = await api.galaxy.get(this.gameId)
    },
    async fetchColonies() {
      if (!this.gameId) return
      this.colonies = await api.colony.list(this.gameId)
    },
    async fetchColony(id: string) {
      if (!this.gameId) return null
      return api.colony.get(this.gameId, id)
    },
    async fetchFleets() {
      if (!this.gameId) return
      this.fleets = await api.fleet.list(this.gameId)
    },

    // ----- Research -----
    async fetchResearch() {
      if (!this.gameId) return
      this.techState = await api.research.get(this.gameId)
    },
    async selectResearch(payload: { field: string; level: number; tech_id: string }) {
      if (!this.gameId) return
      await api.research.select(this.gameId, payload)
      await this.fetchResearch()
    },

    // ----- Diplomacy -----
    async fetchDiplomacy() {
      if (!this.gameId) return
      this.diplomacy = await api.diplomacy.list(this.gameId)
    },
    async proposeTreaty(target: string, type: string, terms: AnyObj = {}) {
      if (!this.gameId) return
      const res = await api.diplomacy.propose(this.gameId, { target, type, terms })
      await this.fetchDiplomacy()
      return res
    },
    async declareWar(target: string) {
      if (!this.gameId) return
      const res = await api.diplomacy.declareWar(this.gameId, target)
      await this.fetchDiplomacy()
      return res
    },

    // ----- Leaders -----
    async fetchLeaders() {
      if (!this.gameId) return
      const [hired, avail] = await Promise.all([
        api.leaders.list(this.gameId),
        api.leaders.available(this.gameId),
      ])
      this.leaders = hired
      this.availableLeaders = avail
    },
    async hireLeader(leaderId: string) {
      if (!this.gameId) return
      const res = await api.leaders.hire(this.gameId, leaderId)
      await this.fetchLeaders()
      return res
    },
    async assignLeader(leaderId: string, targetId: string) {
      if (!this.gameId) return
      const res = await api.leaders.assign(this.gameId, leaderId, targetId)
      await this.fetchLeaders()
      return res
    },

    // ----- Espionage -----
    async fetchSpies() {
      if (!this.gameId) return
      this.spies = await api.espionage.list(this.gameId)
    },
    async recruitSpy() {
      if (!this.gameId) return
      const res = await api.espionage.recruit(this.gameId)
      await this.fetchSpies()
      return res
    },
    async assignSpy(spyId: string, target: string, mission: string) {
      if (!this.gameId) return
      const res = await api.espionage.mission(this.gameId, spyId, target, mission)
      await this.fetchSpies()
      return res
    },

    // ----- Council -----
    async fetchCouncil() {
      if (!this.gameId) return
      this.council = await api.council.votes(this.gameId)
    },
    async voteCouncil(candidate: string) {
      if (!this.gameId) return
      const res = await api.council.vote(this.gameId, candidate)
      await this.fetchCouncil()
      return res
    },

    // ----- Cheats -----
    async applyCheat(code: string, target?: AnyObj) {
      if (!this.gameId) return
      const res = await api.cheat.apply(this.gameId, code, target)
      await this.loadGame(this.gameId)
      return res
    },
  },
})
