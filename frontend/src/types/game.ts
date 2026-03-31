export interface User {
  id: string;
  username: string;
  email: string;
}

export interface Race {
  id: string;
  name: string;
}

export interface Planet {
  index: number;
  type: string;
  size: string;
  mineral_richness: string;
  gravity: string;
  colony?: Colony;
}

export interface StarSystem {
  id: string;
  name: string;
  x: number;
  y: number;
  star_type: string;
  planets: Planet[];
  owner?: string;
  neighbors: string[];
}

export interface Colony {
  id: string;
  system_id: string;
  planet_index: number;
  owner: string;
  population: number;
  population_farmers: number;
  population_workers: number;
  population_scientists: number;
  buildings: string[];
  build_queue: any[];
}

export interface Fleet {
  id: string;
  owner: string;
  system_id?: string;
  destination_id?: string;
  ships: any[];
}

export interface GameState {
  id: string;
  name: string;
  turn: number;
  systems: StarSystem[];
  fleets: Fleet[];
  players: any[];
}
