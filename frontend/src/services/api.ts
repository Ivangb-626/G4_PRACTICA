import axios from 'axios'

const API_BASE = (import.meta as any).env.VITE_API_URL || 'http://localhost:8000'

function getToken() {
  return localStorage.getItem('token')
}

function authHeaders() {
  const token = getToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

function handleError(err: any) {
  const message = err?.response?.data?.error || err?.message || 'Error de red'
  throw new Error(message)
}

export const api = {
  login: async (username: string, password: string) => {
    const res = await axios.post(`${API_BASE}/api/auth/login`, { username, password })
    return res.data
  },
  register: async (username: string, email: string, password: string) => {
    const res = await axios.post(`${API_BASE}/api/auth/register`, { username, email, password })
    return res.data
  },
  getProfile: async () => {
    const res = await axios.get(`${API_BASE}/api/auth/profile`, { headers: authHeaders() })
    return res.data
  },
  listGames: async () => {
    const res = await axios.get(`${API_BASE}/api/games`, { headers: authHeaders() })
    return res.data
  },
  createGame: async (name: string, scenario_config: any) => {
    const res = await axios.post(`${API_BASE}/api/games`, { name, scenario_config }, { headers: authHeaders() })
    return res.data
  },
  loadGame: async (gameId: string) => {
    const res = await axios.get(`${API_BASE}/api/games/${gameId}`, { headers: authHeaders() })
    return res.data
  },
  saveGame: async (gameId: string, name?: string) => {
    const res = await axios.post(`${API_BASE}/api/games/${gameId}/save`, { name }, { headers: authHeaders() })
    return res.data
  },
  deleteGame: async (gameId: string) => {
    const res = await axios.delete(`${API_BASE}/api/games/${gameId}`, { headers: authHeaders() })
    return res.data
  },
  manageColony: async (gameId: string, colonyId: string, data: any) => {
    const res = await axios.post(`${API_BASE}/api/games/${gameId}/colony/${colonyId}/manage`, data, { headers: authHeaders() })
    return res.data
  },
  selectResearch: async (gameId: string, data: any) => {
    const res = await axios.post(`${API_BASE}/api/games/${gameId}/research`, data, { headers: authHeaders() })
    return res.data
  },
  moveFleet: async (gameId: string, fleetId: string, destination: string) => {
    const res = await axios.post(`${API_BASE}/api/games/${gameId}/fleet/${fleetId}/move`, { destination }, { headers: authHeaders() })
    return res.data
  },
  colonize: async (gameId: string, fleetId: string, planetIndex: number) => {
    const res = await axios.post(`${API_BASE}/api/games/${gameId}/colonize`, { fleet_id: fleetId, planet_index: planetIndex }, { headers: authHeaders() })
    return res.data
  },
  endTurn: async (gameId: string) => {
    const res = await axios.post(`${API_BASE}/api/games/${gameId}/endTurn`, {}, { headers: authHeaders() })
    return res.data
  },
  applyCheat: async (gameId: string, cheat_code: string, target: any) => {
    const res = await axios.post(`${API_BASE}/api/games/${gameId}/cheat`, { cheat_code, target }, { headers: authHeaders() })
    return res.data
  },
  getGalaxy: async (gameId: string) => {
    const res = await axios.get(`${API_BASE}/api/games/${gameId}/galaxy`, { headers: authHeaders() })
    return res.data
  },
  getTechTree: async (gameId: string) => {
    const res = await axios.get(`${API_BASE}/api/games/${gameId}/tech-tree`, { headers: authHeaders() })
    return res.data
  },
  getColony: async (gameId: string, colonyId: string) => {
    const res = await axios.get(`${API_BASE}/api/games/${gameId}/colony/${colonyId}`, { headers: authHeaders() })
    return res.data
  },
  getScenarios: async () => {
    const res = await axios.get(`${API_BASE}/api/scenarios`)
    return res.data
  }
}
