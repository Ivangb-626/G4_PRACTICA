const BASE_URL = window.location.origin;

async function request(path: string, options: RequestInit = {}) {
  const token = localStorage.getItem('token');
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const response = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Unknown error' }));
    throw new Error(error.error || `HTTP ${response.status}`);
  }

  return response.json();
}

export const api = {
  auth: {
    login: (username, password) => request('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),
    register: (username, email, password) => request('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, email, password }),
    }),
    profile: () => request('/api/auth/profile'),
  },
  game: {
    new: (name, scenario_id) => request('/api/game/new', {
      method: 'POST',
      body: JSON.stringify({ name, scenario_id }),
    }),
    list: () => request('/api/game/list'),
    get: (id) => request(`/api/game/${id}`),
    delete: (id) => request(`/api/game/${id}`, { method: 'DELETE' }),
    endTurn: (id) => request(`/api/game/${id}/end-turn`, { method: 'POST' }),
  },
  galaxy: {
    get: (id) => request(`/api/game/${id}/galaxy`),
    getStar: (id, starIdx) => request(`/api/game/${id}/galaxy/star/${starIdx}`),
  },
  colony: {
    list: (id) => request(`/api/game/${id}/colony`),
    get: (id, colonyId) => request(`/api/game/${id}/colony/${colonyId}`),
    assign: (id, colonyId, assignment) => request(`/api/game/${id}/colony/${colonyId}/assign`, {
      method: 'POST',
      body: JSON.stringify(assignment),
    }),
    buildQueue: (id, colonyId, item) => request(`/api/game/${id}/colony/${colonyId}/build-queue`, {
      method: 'POST',
      body: JSON.stringify(item),
    }),
  },
  fleet: {
    list: (id) => request(`/api/game/${id}/fleet`),
    move: (id, fleetId, starIdx) => request(`/api/game/${id}/fleet/${fleetId}/move`, {
      method: 'POST',
      body: JSON.stringify({ star_idx: starIdx }),
    }),
    colonize: (id, fleetId, planetIdx) => request(`/api/game/${id}/fleet/${fleetId}/colonize`, {
      method: 'POST',
      body: JSON.stringify({ planet_idx: planetIdx }),
    }),
  },
  cheat: {
    apply: (id, code) => request(`/api/game/${id}/cheat`, {
      method: 'POST',
      body: JSON.stringify({ code }),
    }),
    codes: (id) => request(`/api/game/${id}/cheat/codes`),
  }
};
