import random

def get_ship_stats(ship_type_name, ship_types_data):
    """Obtains the stats of a ship type from ship_types_data."""
    return ship_types_data.get(ship_type_name, {
        'attack': 0, 'defense': 0, 'shields': 0, 'health': 1
    })

def resolve_combat(attacker_fleet: dict, defender_fleet: dict, defender_orbital_defense: int = 0, ship_types_data: dict = None) -> dict:
    """
    1. Calcular fuerza de ataque y defensa
    2. Simular 5 rondas de combate
    3. Cada ronda: daño proporcional con factor aleatorio (0.8-1.2) - escudos
    4. Eliminar naves empezando por las más débiles
    5. Determinar ganador
    6. Retornar resultado con bajas por bando
    """
    if ship_types_data is None:
        from app.data import ships
        # Handle the fact that ships might be loaded via json like in game_service
        import json
        import os
        try:
            with open('backend/app/data/ships.json', 'r', encoding='utf-8') as f:
                ship_types_data = {s['type']: s for s in json.load(f)}
        except:
            ship_types_data = {}

    
    def calculate_strength_and_shields(fleet):
        strength = 0
        total_shields = 0
        all_ships = []
        for ship_group in fleet.get('ships', []):
            stype = ship_group['type']
            count = ship_group['count']
            stats = get_ship_stats(stype, ship_types_data)
            strength += stats.get('attack', 1) * count
            total_shields += stats.get('shields', 0) * count
            # flattened ships for casualty removal
            for _ in range(count):
                all_ships.append({'type': stype, 'health': stats.get('health', 10), 'stats': stats})
        
        # Sort ships by health ascending (weakest first)
        all_ships.sort(key=lambda s: s['health'])
        return strength, total_shields, all_ships

    att_str, att_shields, att_ships = calculate_strength_and_shields(attacker_fleet)
    def_str, def_shields, def_ships = calculate_strength_and_shields(defender_fleet)
    
    def_str += defender_orbital_defense

    def remove_ships(ships_list, damage):
        remaining_damage = damage
        survivors = []
        for ship in ships_list:
            if remaining_damage <= 0:
                survivors.append(ship)
                continue
            
            if remaining_damage >= ship['health']:
                remaining_damage -= ship['health']
            else:
                ship['health'] -= remaining_damage
                remaining_damage = 0
                survivors.append(ship)
        return survivors

    rounds = 5
    for _ in range(rounds):
        if not att_ships or not def_ships:
            break
            
        att_damage = max(0, att_str * random.uniform(0.8, 1.2) - def_shields)
        def_damage = max(0, def_str * random.uniform(0.8, 1.2) - att_shields)
        
        def_ships = remove_ships(def_ships, att_damage)
        att_ships = remove_ships(att_ships, def_damage)
        
        # Recalculate forces based on survivors
        att_str = sum(s['stats'].get('attack', 1) for s in att_ships)
        att_shields = sum(s['stats'].get('shields', 0) for s in att_ships)
        
        def_str = sum(s['stats'].get('attack', 1) for s in def_ships) + defender_orbital_defense
        def_shields = sum(s['stats'].get('shields', 0) for s in def_ships)

    if att_ships and not def_ships:
        winner = "attacker"
    elif def_ships and not att_ships:
        winner = "defender"
    else:
        winner = "stalemate"

    # Reconstruct grouped format for survivors
    def group_ships(ships_list):
        grouped = {}
        for s in ships_list:
            grouped[s['type']] = grouped.get(s['type'], 0) + 1
        return [{'type': k, 'count': v} for k, v in grouped.items()]

    att_survivors = group_ships(att_ships)
    def_survivors = group_ships(def_ships)
    
    return {
        "winner": winner,
        "attacker_remaining": att_survivors,
        "defender_remaining": def_survivors
    }

def resolve_ground_combat(num_transports: int, race_bonus_attacker: int, colony: dict, race_bonus_defender: int) -> dict:
    """
    Implementar fórmula de SPECS.md § 3.7
    """
    attack_strength = num_transports * 5 + race_bonus_attacker
    defense_strength = colony['population']['total'] + colony.get('ground_defense', 0) + race_bonus_defender

    rounds = 3
    for _ in range(rounds):
        if attack_strength <= 0 or defense_strength <= 0:
            break
            
        att_casualties = max(0, defense_strength * random.uniform(0.3, 0.5))
        def_casualties = max(0, attack_strength * random.uniform(0.3, 0.5))
        
        attack_strength -= att_casualties
        defense_strength -= def_casualties

    if attack_strength > 0 and defense_strength <= 0:
        return {"winner": "attacker", "colony_captured": True, "remaining_attackers": max(1, int(attack_strength))}
    else:
        return {"winner": "defender", "colony_captured": False, "remaining_defenders": max(1, int(defense_strength))}
