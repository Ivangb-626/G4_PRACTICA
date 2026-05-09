import httpClient from '../types/httpClient'

/**
 * API client mapped 1:1 to the Flask backend (see backend/app/__init__.py).
 * Base URL is configurable via VITE_API_URL.
 */
export const api = {
  // ---------- Auth ----------
  login: async (username: string, password: string) => {
    const res = await httpClient.post('/api/auth/login', { username, password })
    return res.data
  },
  register: async (username: string, email: string, password: string) => {
    const res = await httpClient.post('/api/auth/register', { username, email, password })
    return res.data
  },
  getProfile: async () => {
    const res = await httpClient.get('/api/auth/profile')
    return res.data
  },

  // ---------- Game lifecycle ----------
  getScenarios: async () => {
    const res = await httpClient.get('/api/game/scenarios')
    return res.data
  },
  listGames: async () => {
    const res = await httpClient.get('/api/game/list')
    return res.data
  },
  createGame: async (config: Record<string, unknown>) => {
    const res = await httpClient.post('/api/game/new', config)
    return res.data
  },
  loadGame: async (gameId: string) => {
    const res = await httpClient.get(`/api/game/${gameId}`)
    return res.data
  },
  deleteGame: async (gameId: string) => {
    const res = await httpClient.delete(`/api/game/${gameId}`)
    return res.data
  },
  endTurn: async (gameId: string) => {
    const res = await httpClient.post(`/api/game/${gameId}/end-turn`, {})
    return res.data
  },
  getTurnStatus: async (gameId: string) => {
    const res = await httpClient.get(`/api/game/${gameId}/turn-status`)
    return res.data
  },
  getScore: async (gameId: string) => {
    const res = await httpClient.get(`/api/game/${gameId}/score`)
    return res.data
  },
  getHallOfFame: async () => {
    const res = await httpClient.get('/api/game/hall-of-fame')
    return res.data
  },

  // ---------- Galaxy ----------
  getGalaxy: async (gameId: string) => {
    const res = await httpClient.get(`/api/game/${gameId}/galaxy`)
    return res.data
  },
  getSystem: async (gameId: string, systemId: string) => {
    const res = await httpClient.get(`/api/game/${gameId}/galaxy/system/${systemId}`)
    return res.data
  },

  // ---------- Colony ----------
  listColonies: async (gameId: string) => {
    const res = await httpClient.get(`/api/game/${gameId}/colony`)
    return res.data
  },
  getColony: async (gameId: string, colonyId: string) => {
    const res = await httpClient.get(`/api/game/${gameId}/colony/${colonyId}`)
    return res.data
  },
  assignPopulation: async (
    gameId: string,
    colonyId: string,
    payload: { farmers: number; workers: number; scientists: number },
  ) => {
    const res = await httpClient.post(`/api/game/${gameId}/colony/${colonyId}/assign`, payload)
    return res.data
  },
  addBuildQueueItem: async (
    gameId: string,
    colonyId: string,
    itemType: 'building' | 'ship',
    itemId: string,
  ) => {
    const res = await httpClient.post(`/api/game/${gameId}/colony/${colonyId}/build-queue`, {
      item_type: itemType,
      item_id: itemId,
    })
    return res.data
  },
  removeBuildQueueItem: async (gameId: string, colonyId: string, idx: number) => {
    const res = await httpClient.delete(`/api/game/${gameId}/colony/${colonyId}/build-queue/${idx}`)
    return res.data
  },

  // ---------- Fleet ----------
  listFleets: async (gameId: string) => {
    const res = await httpClient.get(`/api/game/${gameId}/fleet`)
    return res.data
  },
  moveFleet: async (gameId: string, fleetId: string, destination: string) => {
    const res = await httpClient.post(`/api/game/${gameId}/fleet/${fleetId}/move`, { destination })
    return res.data
  },
  getFleetRange: async (gameId: string) => {
    const res = await httpClient.get(`/api/game/${gameId}/fleet/range`)
    return res.data as { max_jumps: number }
  },
  getFleetReachable: async (gameId: string, fleetId: string) => {
    const res = await httpClient.get(`/api/game/${gameId}/fleet/${fleetId}/reachable`)
    return res.data as { max_jumps: number; origin: string; reachable: string[] }
  },
  colonizePlanet: async (gameId: string, fleetId: string, planetIndex: number) => {
    const res = await httpClient.post(`/api/game/${gameId}/fleet/${fleetId}/colonize`, { planet_index: planetIndex })
    return res.data
  },
  splitFleet: async (gameId: string, fleetId: string, ships: Array<{ type: string; count: number }>) => {
    const res = await httpClient.post(`/api/game/${gameId}/fleet/${fleetId}/split`, { ships })
    return res.data
  },
  mergeFleets: async (gameId: string, fleetA: string, fleetB: string) => {
    const res = await httpClient.post(`/api/game/${gameId}/fleet/merge`, { fleet_a: fleetA, fleet_b: fleetB })
    return res.data
  },
  disbandFleet: async (gameId: string, fleetId: string) => {
    const res = await httpClient.delete(`/api/game/${gameId}/fleet/${fleetId}`)
    return res.data
  },

  // ---------- Research ----------
  getResearch: async (gameId: string) => {
    const res = await httpClient.get(`/api/game/${gameId}/research`)
    return res.data
  },
  selectResearch: async (gameId: string, payload: { field: string; level: number; tech_id: string }) => {
    const res = await httpClient.post(`/api/game/${gameId}/research/select`, payload)
    return res.data
  },

  // ---------- Diplomacy ----------
  getDiplomacy: async (gameId: string) => {
    const res = await httpClient.get(`/api/game/${gameId}/diplomacy`)
    return res.data
  },
  proposeTreaty: async (gameId: string, target: string, treatyType: string, terms: any = {}) => {
    const res = await httpClient.post(`/api/game/${gameId}/diplomacy/propose`, { target, type: treatyType, terms })
    return res.data
  },
  acceptTreaty: async (gameId: string, treatyId: string) => {
    const res = await httpClient.post(`/api/game/${gameId}/diplomacy/accept`, { treaty_id: treatyId })
    return res.data
  },
  rejectTreaty: async (gameId: string, treatyId: string) => {
    const res = await httpClient.post(`/api/game/${gameId}/diplomacy/reject`, { treaty_id: treatyId })
    return res.data
  },
  declareWar: async (gameId: string, target: string) => {
    const res = await httpClient.post(`/api/game/${gameId}/diplomacy/war`, { target })
    return res.data
  },
  surrender: async (gameId: string, target: string) => {
    const res = await httpClient.post(`/api/game/${gameId}/diplomacy/surrender`, { target })
    return res.data
  },
  giveGift: async (gameId: string, target: string, payload: { bc?: number; tech_id?: string; field?: string; level?: number }) => {
    const res = await httpClient.post(`/api/game/${gameId}/diplomacy/gift`, { target, payload })
    return res.data
  },
  makeDemand: async (gameId: string, target: string, payload: { bc?: number; tech_id?: string }) => {
    const res = await httpClient.post(`/api/game/${gameId}/diplomacy/demand`, { target, payload })
    return res.data
  },
  techTrade: async (gameId: string, target: string, offeredTech: string, requestedTech: string) => {
    const res = await httpClient.post(`/api/game/${gameId}/diplomacy/tech-trade`, {
      target,
      offered_tech: offeredTech,
      requested_tech: requestedTech,
    })
    return res.data
  },
  blackmail: async (gameId: string, target: string, leverageStrength: number) => {
    const res = await httpClient.post(`/api/game/${gameId}/diplomacy/blackmail`, {
      target,
      leverage: { strength: leverageStrength },
    })
    return res.data
  },
  aiEvaluateProposal: async (gameId: string, target: string, proposal: Record<string, unknown>) => {
    const res = await httpClient.post(`/api/game/${gameId}/diplomacy/ai-evaluate`, { target, proposal })
    return res.data
  },

  // ---------- Combat ----------
  combatAuto: async (gameId: string) => {
    const res = await httpClient.post(`/api/game/${gameId}/combat/auto`, {})
    return res.data
  },
  combatTacticalStart: async (gameId: string, fleetId: string, targetOwner: string, targetFleetId: string) => {
    const res = await httpClient.post(`/api/game/${gameId}/combat/tactical/start`, {
      fleet_id: fleetId,
      target_owner: targetOwner,
      target_fleet_id: targetFleetId,
    })
    return res.data
  },
  combatTacticalAuto: async (gameId: string, state: any) => {
    const res = await httpClient.post(`/api/game/${gameId}/combat/tactical/auto`, { state })
    return res.data
  },
  combatTacticalAction: async (gameId: string, state: any, unitUid: string, action: any) => {
    const res = await httpClient.post(`/api/game/${gameId}/combat/tactical/action`, { state, unit_uid: unitUid, action })
    return res.data
  },
  fightMonster: async (gameId: string, fleetId: string, systemId: string) => {
    const res = await httpClient.post(`/api/game/${gameId}/combat/monster`, { fleet_id: fleetId, system_id: systemId })
    return res.data
  },
  defeatGuardian: async (gameId: string) => {
    const res = await httpClient.post(`/api/game/${gameId}/combat/orion/defeat-guardian`, {})
    return res.data
  },
  buildDimensionalPortal: async (gameId: string, colonyId?: string) => {
    const res = await httpClient.post(`/api/game/${gameId}/combat/antaran/build-portal`, { colony_id: colonyId })
    return res.data
  },
  assaultAntaranHomeworld: async (gameId: string, fleetId: string) => {
    const res = await httpClient.post(`/api/game/${gameId}/combat/antaran/assault`, { fleet_id: fleetId })
    return res.data
  },

  // ---------- Espionage ----------
  listSpies: async (gameId: string) => {
    const res = await httpClient.get(`/api/game/${gameId}/espionage`)
    return res.data
  },
  recruitSpy: async (gameId: string) => {
    const res = await httpClient.post(`/api/game/${gameId}/espionage/recruit`, {})
    return res.data
  },
  assignSpyMission: async (gameId: string, spyId: string, target: string, mission: string) => {
    const res = await httpClient.post(`/api/game/${gameId}/espionage/mission`, {
      spy_id: spyId,
      target,
      mission,
    })
    return res.data
  },

  // ---------- Leaders ----------
  listHiredLeaders: async (gameId: string) => {
    const res = await httpClient.get(`/api/game/${gameId}/leaders`)
    return res.data
  },
  listAvailableLeaders: async (gameId: string) => {
    const res = await httpClient.get(`/api/game/${gameId}/leaders/available`)
    return res.data
  },
  hireLeader: async (gameId: string, leaderId: string) => {
    const res = await httpClient.post(`/api/game/${gameId}/leaders/hire`, { leader_id: leaderId })
    return res.data
  },
  assignLeader: async (gameId: string, leaderId: string, targetId: string) => {
    const res = await httpClient.post(`/api/game/${gameId}/leaders/assign`, {
      leader_id: leaderId,
      target_id: targetId,
    })
    return res.data
  },
  unassignLeader: async (gameId: string, leaderId: string) => {
    const res = await httpClient.post(`/api/game/${gameId}/leaders/unassign`, { leader_id: leaderId })
    return res.data
  },
  dismissLeader: async (gameId: string, leaderId: string) => {
    const res = await httpClient.post(`/api/game/${gameId}/leaders/dismiss`, { leader_id: leaderId })
    return res.data
  },

  // ---------- Ship design ----------
  getShipDesignCatalog: async (gameId: string) => {
    const res = await httpClient.get(`/api/game/${gameId}/ship-design/catalog`)
    return res.data
  },
  listShipDesigns: async (gameId: string) => {
    const res = await httpClient.get(`/api/game/${gameId}/ship-design`)
    return res.data
  },
  createShipDesign: async (gameId: string, design: Record<string, unknown>) => {
    const res = await httpClient.post(`/api/game/${gameId}/ship-design`, design)
    return res.data
  },
  deleteShipDesign: async (gameId: string, designId: string) => {
    const res = await httpClient.delete(`/api/game/${gameId}/ship-design/${designId}`)
    return res.data
  },

  // ---------- Council ----------
  getCouncilVotes: async (gameId: string) => {
    const res = await httpClient.get(`/api/game/${gameId}/council/votes`)
    return res.data
  },
  conveneCouncil: async (gameId: string) => {
    const res = await httpClient.post(`/api/game/${gameId}/council/convene`, {})
    return res.data
  },
  voteCouncil: async (gameId: string, candidate: string) => {
    const res = await httpClient.post(`/api/game/${gameId}/council/vote`, { candidate })
    return res.data
  },

  // ---------- Ground combat ----------
  groundAssault: async (gameId: string, fleetId: string, colonyId: string, exterminate = false) => {
    const res = await httpClient.post(`/api/game/${gameId}/ground/assault`, {
      fleet_id: fleetId,
      colony_id: colonyId,
      exterminate,
    })
    return res.data
  },
  mindControl: async (gameId: string, colonyId: string) => {
    const res = await httpClient.post(`/api/game/${gameId}/ground/mind-control`, { colony_id: colonyId })
    return res.data
  },
  bombardColony: async (gameId: string, fleetId: string, colonyId: string, intensity = 1) => {
    const res = await httpClient.post(`/api/game/${gameId}/ground/bombard`, {
      fleet_id: fleetId,
      colony_id: colonyId,
      intensity,
    })
    return res.data
  },

  // ---------- Race design ----------
  getRaceDesignOptions: async () => {
    const res = await httpClient.get('/api/race-design/options')
    return res.data
  },
  validateRaceDesign: async (picks: string[]) => {
    const res = await httpClient.post('/api/race-design/validate', { picks })
    return res.data
  },

  // ---------- Cheats ----------
  applyCheat: async (gameId: string, code: string, target?: Record<string, unknown>) => {
    const res = await httpClient.post(`/api/game/${gameId}/cheat`, { code, target })
    return res.data
  },
  listCheatCodes: async (gameId: string) => {
    const res = await httpClient.get(`/api/game/${gameId}/cheat/codes`)
    return res.data
  },
}

export default api
