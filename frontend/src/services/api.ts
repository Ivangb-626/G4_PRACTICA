import httpClient from '../types/httpClient'

export const api = {
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
  listGames: async () => {
    const res = await httpClient.get('/api/games')
    return res.data
  },
  createGame: async (name: string, scenarioConfig: Record<string, unknown>) => {
    const res = await httpClient.post('/api/games', { name, scenario_config: scenarioConfig })
    return res.data
  },
  loadGame: async (gameId: string) => {
    const res = await httpClient.get(`/api/games/${gameId}`)
    return res.data
  },
  saveGame: async (gameId: string, name?: string) => {
    const res = await httpClient.post(`/api/games/${gameId}/save`, { name })
    return res.data
  },
  deleteGame: async (gameId: string) => {
    const res = await httpClient.delete(`/api/games/${gameId}`)
    return res.data
  },
  getStatus: async (gameId: string) => {
    const res = await httpClient.get(`/api/games/${gameId}/status`)
    return res.data
  },
  getGalaxy: async (gameId: string) => {
    const res = await httpClient.get(`/api/games/${gameId}/galaxy`)
    return res.data
  },
  getTechTree: async (gameId: string) => {
    const res = await httpClient.get(`/api/games/${gameId}/tech-tree`)
    return res.data
  },
  selectResearch: async (gameId: string, data: { field: string; level: number; tech_id: string }) => {
    const res = await httpClient.post(`/api/games/${gameId}/research`, data)
    return res.data
  },
  getFleets: async (gameId: string) => {
    const res = await httpClient.get(`/api/games/${gameId}/fleets`)
    return res.data
  },
  moveFleet: async (gameId: string, fleetId: string, destination: string) => {
    const res = await httpClient.post(`/api/games/${gameId}/fleet/${fleetId}/move`, { destination })
    return res.data
  },
  splitFleet: async (
    gameId: string,
    fleetId: string,
    ships: Array<{ type: string; count: number }>,
  ) => {
    const res = await httpClient.post(`/api/games/${gameId}/fleet/${fleetId}/split`, { ships })
    return res.data
  },
  colonize: async (gameId: string, fleetId: string, planetIndex: number) => {
    const res = await httpClient.post(`/api/games/${gameId}/colonize`, {
      fleet_id: fleetId,
      planet_index: planetIndex,
    })
    return res.data
  },
  getColonies: async (gameId: string) => {
    const res = await httpClient.get(`/api/games/${gameId}/colonies`)
    return res.data
  },
  getColony: async (gameId: string, colonyId: string) => {
    const res = await httpClient.get(`/api/games/${gameId}/colony/${colonyId}`)
    return res.data
  },
  manageColony: async (
    gameId: string,
    colonyId: string,
    data: { population?: { farmers: number; workers: number; scientists: number } },
  ) => {
    const res = await httpClient.post(`/api/games/${gameId}/colony/${colonyId}/manage`, data)
    return res.data
  },
  addBuildQueueItem: async (gameId: string, colonyId: string, type: 'building' | 'ship', id: string) => {
    const res = await httpClient.post(`/api/games/${gameId}/colony/${colonyId}/build-queue/add`, { type, id })
    return res.data
  },
  removeBuildQueueItem: async (gameId: string, colonyId: string, index: number) => {
    const res = await httpClient.post(`/api/games/${gameId}/colony/${colonyId}/build-queue/remove`, { index })
    return res.data
  },
  reorderBuildQueue: async (gameId: string, colonyId: string, from: number, to: number) => {
    const res = await httpClient.post(`/api/games/${gameId}/colony/${colonyId}/build-queue/reorder`, {
      from,
      to,
    })
    return res.data
  },
  endTurn: async (gameId: string) => {
    const res = await httpClient.post(`/api/games/${gameId}/endTurn`, {})
    return res.data
  },
  applyCheat: async (gameId: string, cheatCode: string, target?: Record<string, unknown>) => {
    const res = await httpClient.post(`/api/games/${gameId}/cheat`, {
      cheat_code: cheatCode,
      target,
    })
    return res.data
  },
  getScenarios: async () => {
    const res = await httpClient.get('/api/scenarios')
    return res.data
  },
  getDiplomacy: async (gameId: string) => {
    const res = await httpClient.get(`/api/games/${gameId}/diplomacy`)
    return res.data
  },
  proposeTreaty: async (gameId: string, target: string, treatyType: string) => {
    const res = await httpClient.post(`/api/games/${gameId}/diplomacy/propose`, {
      target,
      treaty_type: treatyType,
    })
    return res.data
  },
  declareWar: async (gameId: string, target: string) => {
    const res = await httpClient.post(`/api/games/${gameId}/diplomacy/war`, { target })
    return res.data
  },

  // Diplomacy: Tech trade (DIPLOMACY sec 3)
  tradeTech: async (gameId: string, target: string, offered: string, requested: string) => {
    const res = await httpClient.post(`/api/games/${gameId}/diplomacy/trade-tech`, {
      target,
      offered_tech: offered,
      requested_tech: requested,
    })
    return res.data
  },

  // Diplomacy: Gifts (DIPLOMACY sec 8)
  giveGift: async (
    gameId: string,
    target: string,
    giftType: 'gift_money' | 'gift_tech',
    options: { amount?: number; tech_id?: string } = {},
  ) => {
    const res = await httpClient.post(`/api/games/${gameId}/diplomacy/gift`, {
      target,
      gift_type: giftType,
      ...options,
    })
    return res.data
  },

  // Diplomacy: Demands (DIPLOMACY sec 7 & 12)
  makeDemand: async (
    gameId: string,
    target: string,
    demandType: string,
    payload: Record<string, unknown> = {},
  ) => {
    const res = await httpClient.post(`/api/games/${gameId}/diplomacy/demand`, {
      target,
      demand_type: demandType,
      payload,
    })
    return res.data
  },

  // Diplomacy: Scouting / Intelligence (DIPLOMACY sec 14)
  getIntelligence: async (gameId: string, target: string) => {
    const res = await httpClient.get(`/api/games/${gameId}/diplomacy/intelligence/${target}`)
    return res.data
  },
  openDialogue: async (gameId: string, target: string) => {
    const res = await httpClient.post(`/api/games/${gameId}/diplomacy/dialogue/${target}`)
    return res.data
  },
  getRelations: async (gameId: string) => {
    const res = await httpClient.get(`/api/games/${gameId}/diplomacy/relations`)
    return res.data
  },

  // Espionage: levels & defense (DIPLOMACY sec 9)
  getEspionage: async (gameId: string) => {
    const res = await httpClient.get(`/api/game/${gameId}/espionage`)
    return res.data
  },
  getSpyLevels: async (gameId: string) => {
    const res = await httpClient.get(`/api/games/${gameId}/espionage/levels`)
    return res.data
  },
  recruitSpy: async (gameId: string, level: 1 | 2 | 3 | 4 = 1) => {
    const res = await httpClient.post(`/api/game/${gameId}/espionage/recruit`, { level })
    return res.data
  },
  assignSpyMission: async (
    gameId: string,
    spyId: string,
    targetId: string,
    missionType: string,
  ) => {
    const res = await httpClient.post(`/api/game/${gameId}/espionage/mission`, {
      spy_id: spyId,
      target_id: targetId,
      mission_type: missionType,
    })
    return res.data
  },
  assignSpyDefense: async (gameId: string, spyId: string) => {
    const res = await httpClient.post(`/api/games/${gameId}/espionage/defense`, { spy_id: spyId })
    return res.data
  },

  // Combat: Mind Control (PLAN sec 4)
  mindControl: async (gameId: string, colonyId: string) => {
    const res = await httpClient.post(`/api/games/${gameId}/combat/mind-control`, {
      colony_id: colonyId,
    })
    return res.data
  },

  // Combat: Space Monsters (PLAN sec 18)
  listSpaceMonsters: async (gameId: string) => {
    const res = await httpClient.get(`/api/games/${gameId}/space-monsters`)
    return res.data
  },
  fightSpaceMonster: async (gameId: string, fleetId: string, systemId: string) => {
    const res = await httpClient.post(`/api/games/${gameId}/combat/monster`, {
      fleet_id: fleetId,
      system_id: systemId,
    })
    return res.data
  },

  // Orion & Antarans (PLAN sec 19 & 20)
  defeatGuardian: async (gameId: string) => {
    const res = await httpClient.post(`/api/games/${gameId}/orion/defeat-guardian`, {})
    return res.data
  },
  buildDimensionalPortal: async (gameId: string, colonyId?: string) => {
    const res = await httpClient.post(`/api/games/${gameId}/antaran/build-portal`, {
      colony_id: colonyId,
    })
    return res.data
  },
  assaultAntaranHomeworld: async (gameId: string, fleetId: string) => {
    const res = await httpClient.post(`/api/games/${gameId}/antaran/assault`, { fleet_id: fleetId })
    return res.data
  },
}
