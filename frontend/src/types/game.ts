export type Resources = {
  bc: number
  total_bc?: number
  total_food_surplus?: number
  total_production?: number
  total_research?: number
  command_points?: number
  command_points_used?: number
  free_ship?: boolean
}

export type Population = {
  total: number
  max: number
  farmers: number
  workers: number
  scientists: number
}

export type Planet = {
  index: number
  name: string
  type: string
  size: string
  minerals: string
  gravity: string
  max_population: number
  colonized_by: string | null
  special?: string | null
}

export type ColonyBuilding = {
  id: string
  name: string
  completed?: boolean
}

export type BuildQueueItem = {
  type: 'building' | 'ship'
  id: string
  progress: number
  cost: number
}

export type Colony = {
  id: string
  name: string
  star_system_id: string
  planet_index: number
  owner: string
  population: Population
  buildings: ColonyBuilding[]
  build_queue: BuildQueueItem[]
  morale: string
  food_output: number
  food_consumption: number
  food_surplus: number
  industry_output: number
  research_output: number
  bc_output: number
  ground_defense: number
  orbital_defense: number
}

export type FleetShip = {
  type: string
  count: number
}

export type Fleet = {
  id: string
  name: string
  owner: string
  star_system_id: string
  destination: string | null
  eta_turns: number | null
  ships: FleetShip[]
  command_points_used: number
}

export type Race = {
  id: string
  name: string
}

export type PlayerEmpire = {
  race: Race
  resources: Resources
  colonies: Colony[]
  fleets: Fleet[]
  technologies: {
    researched: Array<{
      field: string
      level: number
      tech_id: string
      status?: string
    }>
    current_research: {
      field: string
      level: number
      tech_id: string
      progress: number
      total_cost: number
    } | null
  }
}

export type AIPlayer = PlayerEmpire & {
  id: string
  name?: string
  personality: string
}

export type GalaxySystem = {
  id: string
  name: string
  position: { x: number; y: number }
  star_type: string
  explored: boolean
  planets: Planet[]
  connections: string[]
  has_player_colony: boolean
  has_player_fleet: boolean
  has_enemy_fleet: boolean
}

export type GameState = {
  game_id?: string | null
  name: string
  scenario_id: string
  difficulty: string
  turn: number
  created_at: string
  last_saved: string
  is_autosave: boolean
  cheats_used: string[]
  victory_condition: string | null
  player: PlayerEmpire
  ai_players: AIPlayer[]
  galaxy: {
    size: string
    num_systems: number
    star_systems: GalaxySystem[]
    fog_of_war: Record<string, string[]>
  }
}

export type TechOption = {
  tech_id: string
  name: string
  description: string
  research_cost: number
  status: 'available' | 'locked' | 'current' | 'researched' | 'discarded'
  field: string
  level: number
  unlocks: Record<string, unknown>
}

export type TechField = {
  field: string
  levels: Array<{
    level: number
    options: TechOption[]
  }>
}

export type GameSummary = {
  game_id: string
  name: string
  turn: number
  player_race?: string
  galaxy_size?: string
  last_saved?: string
  is_autosave?: boolean
}

export type ColonySummary = {
  id: string
  name: string
  system_id: string
  population: number
  morale: string
  food_output: number
  food_surplus: number
  industry_output: number
  research_output: number
  bc_output: number
  buildings_count: number
  build_queue_items: number
}

export type FleetSummary = {
  id: string
  name: string
  location: string
  star_system_id: string
  in_transit: boolean
  destination: string | null
  eta_turns: number | null
  ship_count: number
  ships: FleetShip[]
}

export type TurnEvent = Record<string, unknown> & {
  type: string
}

export type AIActionSummary = {
  ai_id: string
  personality: string
  actions: Array<Record<string, unknown>>
  reasoning: string
}

export type Scenario = {
  id: string
  name: string
  description: string
  galaxy_sizes: string[]
  max_opponents: number
  difficulty_options: string[]
}
