import random
import uuid


# DIPLOMACY sec 9 — extended mission catalogue
MISSION_TYPES = [
    "info_probe",         # Discover population/buildings (low risk)
    "tech_espionage",     # Discover ongoing research (medium risk)
    "economic_sabotage",  # -15% to -30% production for 3-8 turns (high risk)
    "military_sabotage",  # Damage military infrastructure (very high risk)
    "scientific_sabotage",# -20% to -40% research for 4-10 turns (high risk)
    "political_espionage",# Discover strategy / military plans (medium risk)
    # Legacy compatibility
    "sabotage",
    "steal_tech",
    "assassinate",
    "incite_revolt",
]

# DIPLOMACY sec 9 — Spy levels with detection risk and effectiveness multipliers
SPY_LEVELS = {
    1: {"name": "Novato",     "detect_min": 30, "detect_max": 40, "effectiveness": 0.4, "cost": 50,  "salary": 5},
    2: {"name": "Entrenado",  "detect_min": 15, "detect_max": 25, "effectiveness": 0.7, "cost": 100, "salary": 10},
    3: {"name": "Veterano",   "detect_min": 5,  "detect_max": 15, "effectiveness": 1.0, "cost": 200, "salary": 20},
    4: {"name": "Maestro",    "detect_min": 1,  "detect_max": 5,  "effectiveness": 1.4, "cost": 400, "salary": 40},
}

MISSION_RISK = {
    "info_probe":          {"base": 10, "duration": 1, "category": "intel"},
    "tech_espionage":      {"base": 25, "duration": 3, "category": "intel"},
    "economic_sabotage":   {"base": 45, "duration": 1, "category": "sabotage"},
    "military_sabotage":   {"base": 60, "duration": 1, "category": "sabotage"},
    "scientific_sabotage": {"base": 45, "duration": 1, "category": "sabotage"},
    "political_espionage": {"base": 25, "duration": 2, "category": "intel"},
    # Legacy
    "sabotage":            {"base": 40, "duration": 1, "category": "sabotage"},
    "steal_tech":          {"base": 30, "duration": 3, "category": "intel"},
    "assassinate":         {"base": 60, "duration": 1, "category": "sabotage"},
    "incite_revolt":       {"base": 50, "duration": 2, "category": "sabotage"},
}


def _get_player(game_state, player_id):
    if player_id == "player":
        return game_state["player"]
    return next((p for p in game_state.get("ai_players", []) if p["id"] == player_id), None)


def list_spies(game_state, player_id):
    player = _get_player(game_state, player_id)
    if not player:
        return []
    return player.get("spies", [])


def recruit_spy(game_state, player_id, level=1):
    player = _get_player(game_state, player_id)
    if not player:
        return {"error": "Player not found"}, 404

    level = max(1, min(4, int(level)))
    cfg = SPY_LEVELS[level]
    cost = cfg["cost"]
    if player["resources"]["bc"] < cost:
        return {"error": f"Not enough BC to recruit a level-{level} spy ({cost} required)"}, 400

    player["resources"]["bc"] -= cost
    spy = {
        "id": str(uuid.uuid4()),
        "name": f"Agent {random.randint(100, 999)}",
        "level": level,
        "level_name": cfg["name"],
        "skill": random.randint(10, 30) + level * 10,
        "salary": cfg["salary"],
        "status": "idle",            # idle | on_mission | training | compromised | dead
        "mission": None,
        "mission_type": None,
        "assigned_to": None,
        "turns_remaining": 0,
        "training_turns": 0,
    }

    if "spies" not in player:
        player["spies"] = []

    player["spies"].append(spy)
    return {"spy": spy}, 200


def calculate_detection_risk(spy, mission_type, target_counter_intel=0):
    """Per DIPLOMACY sec 9: detection risk depends on spy level, mission and target's counter-intel."""
    cfg = SPY_LEVELS.get(spy.get("level", 1), SPY_LEVELS[1])
    spy_risk = random.randint(cfg["detect_min"], cfg["detect_max"])
    mission_risk = MISSION_RISK.get(mission_type, {"base": 30})["base"]
    risk = (spy_risk * 0.4) + (mission_risk * 0.6) + target_counter_intel
    return max(1, min(99, int(risk)))


def assign_mission(game_state, player_id, spy_id, target_id, mission_type):
    player = _get_player(game_state, player_id)
    if not player:
        return {"error": "Player not found"}, 404

    spies = player.get("spies", [])
    spy = next((s for s in spies if s["id"] == spy_id), None)

    if not spy:
        return {"error": "Spy not found"}, 404

    if mission_type not in MISSION_TYPES:
        return {"error": "Invalid mission type"}, 400

    if spy["status"] not in ["idle"]:
        return {"error": f"Spy is {spy['status']}, not available"}, 400

    target = _get_player(game_state, target_id)
    counter_intel = 0
    if target:
        # Counter-intel = number of "defensive" spies of the target
        counter_intel = sum(5 for s in target.get("spies", []) if s.get("mission") == "defense")

    risk = calculate_detection_risk(spy, mission_type, counter_intel)
    duration = MISSION_RISK.get(mission_type, {"duration": 1})["duration"]

    spy["status"] = "on_mission"
    spy["mission"] = mission_type
    spy["mission_type"] = mission_type
    spy["assigned_to"] = target_id
    spy["turns_remaining"] = duration
    spy["detection_risk"] = risk

    return {"spy": spy, "estimated_risk": risk, "duration": duration}, 200


def assign_defense(game_state, player_id, spy_id):
    """Assign spy to counter-intelligence."""
    player = _get_player(game_state, player_id)
    if not player:
        return {"error": "Player not found"}, 404
    spies = player.get("spies", [])
    spy = next((s for s in spies if s["id"] == spy_id), None)
    if not spy:
        return {"error": "Spy not found"}, 404
    spy["status"] = "on_mission"
    spy["mission"] = "defense"
    spy["mission_type"] = "defense"
    spy["assigned_to"] = player_id
    spy["turns_remaining"] = 0
    return {"spy": spy}, 200


def execute_mission(game_state, spy):
    """Resolves a mission: rolls detection, applies effects.

    Returns a dict describing what happened, used by the turn engine.
    """
    target_id = spy.get("assigned_to")
    mission = spy.get("mission_type") or spy.get("mission")
    if not target_id or not mission:
        return {"result": "no_op"}

    target = _get_player(game_state, target_id)
    if not target:
        return {"result": "target_missing"}

    risk = spy.get("detection_risk", 30)
    detected = random.randint(0, 100) < risk
    cfg = SPY_LEVELS.get(spy.get("level", 1), SPY_LEVELS[1])
    eff = cfg["effectiveness"]

    result = {"mission": mission, "target": target_id, "detected": detected, "level": spy.get("level", 1)}

    if detected:
        spy["status"] = "compromised"
        result["consequence"] = "spy_neutralized"
        # Reputation penalty if relations system present
        try:
            from app.services.diplomacy_service import initialize_diplomacy, get_relation_key
            initialize_diplomacy(game_state)
            relations = game_state["diplomacy"]["relations"]
            owner = next((p["id"] for p in game_state.get("ai_players", []) if spy in p.get("spies", [])), "player")
            key = get_relation_key(relations, owner, target_id)
            if key:
                relations[key]["value"] = max(-100, relations[key]["value"] - random.randint(5, 20))
        except Exception:
            pass
        return result

    # Mission succeeded
    spy["status"] = "idle"
    spy["mission"] = None
    spy["mission_type"] = None
    spy["assigned_to"] = None

    if mission == "info_probe":
        result["intel"] = {
            "colonies": len(target.get("colonies", [])),
            "fleets": len(target.get("fleets", [])),
        }
    elif mission == "tech_espionage" or mission == "steal_tech":
        techs_known = result.setdefault("intel", {})
        techs_known["technologies"] = target.get("technologies", [])[:int(2 * eff) + 1]
    elif mission == "economic_sabotage":
        # Reduce BC
        loss = int(target["resources"].get("bc", 0) * (0.15 + 0.15 * eff))
        target["resources"]["bc"] = max(0, target["resources"]["bc"] - loss)
        result["effect"] = {"bc_lost": loss}
    elif mission == "scientific_sabotage":
        target["research_penalty_turns"] = max(target.get("research_penalty_turns", 0), int(4 + 6 * eff))
        target["research_penalty_pct"] = 0.20 + 0.20 * eff
        result["effect"] = {"research_penalty_pct": target["research_penalty_pct"], "turns": target["research_penalty_turns"]}
    elif mission == "military_sabotage":
        # Damage a random fleet
        fleets = target.get("fleets", [])
        if fleets:
            f = random.choice(fleets)
            for ship in f.get("ships", []):
                ship["count"] = max(0, ship["count"] - max(1, int(ship["count"] * 0.15 * eff)))
            f["ships"] = [s for s in f["ships"] if s["count"] > 0]
            result["effect"] = {"fleet_damaged": f.get("id")}
    elif mission == "political_espionage":
        result["intel"] = {
            "current_research": target.get("current_research"),
            "treaties": [],
        }
    elif mission == "sabotage":
        result["effect"] = {"sabotage": True}
    elif mission == "assassinate":
        leaders = target.get("leaders", [])
        if leaders:
            removed = leaders.pop(0)
            result["effect"] = {"assassinated_leader": removed.get("name")}
    elif mission == "incite_revolt":
        target["unrest_turns"] = max(target.get("unrest_turns", 0), int(3 + 3 * eff))
        result["effect"] = {"unrest_turns": target["unrest_turns"]}

    return result


def process_turn_espionage(game_state):
    """Per-turn: tick mission timers, execute completed missions, charge salaries."""
    events = []
    everyone = ["player"] + [ai["id"] for ai in game_state.get("ai_players", [])]

    for pid in everyone:
        player = _get_player(game_state, pid)
        if not player:
            continue
        spies = player.get("spies", [])
        for spy in list(spies):
            # Salary
            salary = spy.get("salary", 5)
            player["resources"]["bc"] = player["resources"].get("bc", 0) - salary

            # Tick on-mission spies (except defensive)
            if spy.get("status") == "on_mission" and spy.get("mission") != "defense":
                spy["turns_remaining"] = max(0, spy.get("turns_remaining", 0) - 1)
                if spy["turns_remaining"] <= 0:
                    result = execute_mission(game_state, spy)
                    events.append({"owner": pid, "spy": spy.get("name"), "result": result})

        # Remove dead/compromised spies after a delay
        player["spies"] = [s for s in spies if s.get("status") != "dead"]

    return events
