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
}
