import random
from pathlib import Path

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
            data_dir = Path(__file__).resolve().parents[1] / 'data'
            with (data_dir / 'ships.json').open('r', encoding='utf-8') as f:
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

# MOO2 Space Monsters (PLAN sec 18)
SPACE_MONSTERS = {
    "space_crystal": {
        "stationary": {"hp": 200, "attack": 40, "defense": 20, "shields": 30, "weapon": "ray", "telepathic_capture": True},
        "travelling": {"hp": 800, "attack": 60, "defense": 30, "shields": 50, "weapon": "ray", "telepathic_capture": True},
        "tactic_hint": "run_and_fire",
    },
    "space_amoeba": {
        "stationary": {"hp": 250, "attack": 35, "defense": 15, "shields": 0, "weapon": "plasma_web"},
        "travelling": {"hp": 1000, "attack": 50, "defense": 25, "shields": 0, "weapon": "plasma_web", "extra_attacks": 1},
        "tactic_hint": "run_and_fire",
    },
    "space_eel": {
        "stationary": {"hp": 180, "attack": 50, "defense": 25, "shields": 40, "weapon": "shockwave", "lightning_shield": True},
        "travelling": {"hp": 720, "attack": 75, "defense": 40, "shields": 60, "weapon": "shockwave", "lightning_shield": True, "extra_attacks": 1},
        "tactic_hint": "charge_and_fire",
    },
}


def resolve_combat_against_monster(attacker_fleet: dict, monster_type: str, is_travelling: bool = False, ship_types_data: dict = None) -> dict:
    """PLAN sec 18 — combat resolution against a space monster."""
    if monster_type not in SPACE_MONSTERS:
        return {"winner": "stalemate", "error": "Unknown monster type"}

    variant = "travelling" if is_travelling else "stationary"
    monster_stats = SPACE_MONSTERS[monster_type][variant]

    # Build a synthetic "fleet" for the monster
    monster_fleet = {
        "ships": [{"type": f"{monster_type}_{variant}", "count": 1}],
    }

    # Inject monster stats into ship_types_data
    if ship_types_data is None:
        ship_types_data = {}
    ship_types_data = dict(ship_types_data)
    ship_types_data[f"{monster_type}_{variant}"] = {
        "attack": monster_stats["attack"],
        "defense": monster_stats["defense"],
        "shields": monster_stats["shields"],
        "health": monster_stats["hp"],
    }

    result = resolve_combat(attacker_fleet, monster_fleet, defender_orbital_defense=0, ship_types_data=ship_types_data)
    result["monster_type"] = monster_type
    result["is_travelling"] = is_travelling
    result["tactic_hint"] = SPACE_MONSTERS[monster_type]["tactic_hint"]
    return result


def resolve_combat_phase_missiles(attacker_fleet: dict, defender_fleet: dict, ship_types_data: dict = None) -> dict:
    """PLAN sec 15 — pre-resolution missile/torpedo phase.

    Torpedoes ignore point defense; missiles can be intercepted.
    Returns extra damage applied before main combat.
    """
    if ship_types_data is None:
        ship_types_data = {}

    def fleet_attribute(fleet, attr):
        total = 0
        for group in fleet.get("ships", []):
            stats = ship_types_data.get(group["type"], {})
            total += stats.get(attr, 0) * group.get("count", 0)
        return total

    att_missiles = fleet_attribute(attacker_fleet, "missiles")
    att_torpedoes = fleet_attribute(attacker_fleet, "torpedoes")
    def_point_defense = fleet_attribute(defender_fleet, "point_defense")
    def_ecm = fleet_attribute(defender_fleet, "ecm")
    att_eccm = fleet_attribute(attacker_fleet, "eccm")

    # Missiles: can be shot down. Effective accuracy = ECCM vs (PD + ECM)
    pd_strength = def_point_defense + def_ecm * 0.5
    accuracy = max(0.0, min(1.0, 1.0 - (pd_strength - att_eccm) / max(1, att_missiles + 10)))
    missile_damage = int(att_missiles * accuracy * 5)

    # Torpedoes: ECM jammers can reduce slightly but PD doesn't
    torpedo_accuracy = max(0.6, 1.0 - def_ecm / max(1, att_torpedoes + 20))
    torpedo_damage = int(att_torpedoes * torpedo_accuracy * 8)

    return {
        "missile_damage": missile_damage,
        "torpedo_damage": torpedo_damage,
        "missile_accuracy": round(accuracy, 2),
        "torpedo_accuracy": round(torpedo_accuracy, 2),
    }


def can_mind_control(attacker_race_traits, defender_race_traits) -> bool:
    """PLAN sec 4 — mind control requires Telepathic and defender is non-Telepathic."""
    if "telepathic" not in (attacker_race_traits or []):
        return False
    if "telepathic" in (defender_race_traits or []):
        return False
    return True


def mind_control_colony(game_state, attacker_id: str, colony_id: str) -> dict:
    """PLAN sec 4 — capture a colony psychically without ground invasion."""
    # Find the colony in any AI player
    target_owner = None
    target_colony = None
    for player in [game_state["player"]] + game_state.get("ai_players", []):
        for colony in player.get("colonies", []):
            if colony["id"] == colony_id:
                target_owner = player
                target_colony = colony
                break
        if target_colony:
            break

    if not target_colony:
        return {"success": False, "reason": "Colony not found"}

    # Determine attacker
    if attacker_id == "player":
        attacker = game_state["player"]
    else:
        attacker = next((ai for ai in game_state.get("ai_players", []) if ai["id"] == attacker_id), None)
    if not attacker:
        return {"success": False, "reason": "Attacker not found"}

    # Trait check via race id heuristic (matches diplomacy_service)
    attacker_race = (attacker.get("race") or "").lower()
    defender_race = (target_owner.get("race") or "").lower()
    attacker_traits = ["telepathic"] if "telepath" in attacker_race or "psilon" in attacker_race else []
    defender_traits = ["telepathic"] if "telepath" in defender_race or "psilon" in defender_race else []

    if not can_mind_control(attacker_traits, defender_traits):
        return {"success": False, "reason": "Mind control unavailable (need Telepathic vs non-Telepathic)"}

    # Transfer colony, no rebellion timer
    target_owner["colonies"] = [c for c in target_owner.get("colonies", []) if c["id"] != colony_id]
    if "colonies" not in attacker:
        attacker["colonies"] = []
    target_colony["owner"] = attacker_id
    target_colony["rebellion_timer"] = 0  # telepaths assimilate instantly
    attacker["colonies"].append(target_colony)

    return {"success": True, "colony_id": colony_id, "new_owner": attacker_id, "method": "mind_control"}


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
        # Captured by force: PLAN sec 4 — set rebellion_timer (5 turns of -50% production)
        colony["rebellion_timer"] = 5
        return {
            "winner": "attacker",
            "colony_captured": True,
            "remaining_attackers": max(1, int(attack_strength)),
            "rebellion_timer": 5,
        }
    else:
        return {"winner": "defender", "colony_captured": False, "remaining_defenders": max(1, int(defense_strength))}
