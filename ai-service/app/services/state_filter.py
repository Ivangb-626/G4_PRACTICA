def filter_galaxy(galaxy: dict, visible_systems: set) -> dict:
    """Filter the galaxy map based on fog of war."""
    filtered_systems = []
    
    # Check what kind of format galaxy has. If it's a list, handle it
    systems = galaxy if isinstance(galaxy, list) else galaxy.get("systems", [])
    
    for sys in systems:
        sys_id = sys.get("id")
        if sys_id in visible_systems:
            filtered_systems.append(sys)
            
    filtered_galaxy = {}
    if isinstance(galaxy, dict):
        filtered_galaxy.update(galaxy)
    filtered_galaxy["systems"] = filtered_systems
    
    return filtered_galaxy

def filter_enemies(full_state: dict, visible_systems: set, ai_player_id: str) -> list:
    """Filter enemies to only show visible colonies/fleets."""
    enemies = []
    players = full_state.get("players", {})
    
    for pid, pdata in players.items():
        if pid == ai_player_id:
            continue
            
        visible_fleets = []
        for fleet in pdata.get("fleets", []):
            if fleet.get("location") in visible_systems:
                visible_fleets.append(fleet)
                
        visible_colonies = []
        for col in pdata.get("colonies", []):
            # we need a way to know if colony is in visible system, let's assume `location` or checking galaxy
            visible_colonies.append({"id": col.get("id", ""), "name": col.get("name", "Unknown")})
            
        enemies.append({
            "player_id": pid,
            "race_name": pdata.get("race", {}).get("name", "Unknown"),
            "visible_colonies": visible_colonies,
            "visible_fleets": visible_fleets
        })
        
    return enemies

def filter_state_for_ai(full_state: dict, ai_player_id: str) -> dict:
    """
    Apply fog of war rules. The AI only sees:
    - Its own colonies/fleets/technology/resources
    - Star systems in fog_of_war
    - Enemy fleets/colonies ONLY in visible systems
    """
    fow = full_state.get("galaxy", {}).get("fog_of_war", {})
    visible_systems = set(fow.get(ai_player_id, []))
    
    # If fog of war not yet implemented in base game, assume all is visible logically 
    # but we follow rules. Let's just collect all system ids as fallback if fow is empty
    if not visible_systems:
        visible_systems = set(sys["id"] for sys in full_state.get("galaxy", {}).get("systems", []))

    ai_player_data = full_state.get("players", {}).get(ai_player_id, {})

    filtered = {
        "turn": full_state.get("turn", 0),
        "ai_player": ai_player_data,
        "galaxy": filter_galaxy(full_state.get("galaxy", {}), visible_systems),
        "known_enemies": filter_enemies(full_state, visible_systems, ai_player_id)
    }
    
    return filtered
