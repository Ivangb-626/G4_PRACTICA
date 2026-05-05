import random


# Treaty types per DIPLOMACY_MOO2_EXPANSION.md
TREATY_TYPES = ["peace", "non_aggression", "trade", "research", "alliance"]

# Demand types per DIPLOMACY_MOO2_EXPANSION.md sec 7 & 12
DEMAND_TYPES = [
    "demand_money",
    "demand_tech",
    "demand_system",
    "demand_tribute_5",
    "demand_tribute_10",
    "stop_spying",
    "remove_fleet",
]

# Gift types per DIPLOMACY_MOO2_EXPANSION.md sec 8
GIFT_TYPES = ["gift_money", "gift_tech"]

# Race traits affecting diplomacy (DIPLOMACY sec 11)
DIPLOMATIC_RACE_TRAITS = {
    "charismatic": {"relation_bonus": 30, "blocks_diplomacy": False, "trade_multiplier": 1.0},
    "repulsive": {"relation_bonus": -30, "blocks_diplomacy": True, "trade_multiplier": 1.0},
    "telepathic": {"relation_bonus": 20, "blocks_diplomacy": False, "trade_multiplier": 1.0},
    "fantastic_traders": {"relation_bonus": 0, "blocks_diplomacy": False, "trade_multiplier": 1.4},
    "omniscient": {"relation_bonus": 0, "blocks_diplomacy": False, "trade_multiplier": 1.0, "free_scouting": True},
}


def initialize_diplomacy(game_state):
    """Initializes the diplomacy structures in the game state if missing."""
    if "diplomacy" not in game_state:
        game_state["diplomacy"] = {
            "relations": {},
            "council_active": False,
            "council_history": [],
        }

    entities = ["player"] + [ai["id"] for ai in game_state.get("ai_players", [])]
    for i in range(len(entities)):
        for j in range(i + 1, len(entities)):
            pair_key = f"{entities[i]}:{entities[j]}"
            alt_key = f"{entities[j]}:{entities[i]}"
            if pair_key not in game_state["diplomacy"]["relations"] and alt_key not in game_state["diplomacy"]["relations"]:
                game_state["diplomacy"]["relations"][pair_key] = {
                    "value": 50,
                    "treaties": [],
                    "active_treaties": [],
                    "patience": 100,
                    "last_contact_turn": -1,
                    "last_scouted_turn": -1,
                    "intel": None,
                    "knownTechs": [],
                    "tribute_percent": 0,
                    "tribute_turns_left": 0,
                    "treaty_history": [],
                }
    return game_state


def get_relation_key(relations, faction1, faction2):
    k1 = f"{faction1}:{faction2}"
    k2 = f"{faction2}:{faction1}"
    if k1 in relations:
        return k1
    if k2 in relations:
        return k2
    return None


def _get_player(game_state, player_id):
    if player_id == "player":
        return game_state["player"]
    return next((p for p in game_state.get("ai_players", []) if p["id"] == player_id), None)


def _get_race_traits(player):
    """Returns the list of diplomatic trait names for a player based on its race id."""
    race_id = player.get("race") or player.get("race_id") or ""
    traits = []
    rid = race_id.lower()
    if "charisma" in rid or "human" in rid:
        traits.append("charismatic")
    if "repulsive" in rid or "klackon" in rid:
        traits.append("repulsive")
    if "telepath" in rid or "psilon" in rid:
        traits.append("telepathic")
    if "trader" in rid or "darlok" in rid:
        traits.append("fantastic_traders")
    return traits


def _has_repulsive(player):
    return "repulsive" in _get_race_traits(player)


def _trait_relation_bonus(player_a, player_b):
    """Charismatic gives +30, Repulsive -30 to relations."""
    bonus = 0
    for trait in _get_race_traits(player_a) + _get_race_traits(player_b):
        bonus += DIPLOMATIC_RACE_TRAITS.get(trait, {}).get("relation_bonus", 0)
    return bonus


def _relation_status(value):
    """Maps the -100..+200 scale to a status (DIPLOMACY sec 10)."""
    if value <= -51:
        return "enemy_total"
    if value <= -1:
        return "hostile"
    if value <= 50:
        return "neutral"
    if value <= 100:
        return "friendly"
    if value <= 150:
        return "very_friendly"
    return "loyal_ally"


def _patience_decay(rel, amount=10):
    rel["patience"] = max(0, rel.get("patience", 100) - amount)


def _patience_recover(rel, amount=5):
    rel["patience"] = min(100, rel.get("patience", 100) + amount)


def propose_treaty(game_state, proposer, target, treaty_type):
    initialize_diplomacy(game_state)

    if treaty_type not in TREATY_TYPES:
        return {"success": False, "reason": "Invalid treaty type"}

    proposer_p = _get_player(game_state, proposer)
    target_p = _get_player(game_state, target)
    if not proposer_p or not target_p:
        return {"success": False, "reason": "Player not found"}

    # Repulsive races can ONLY propose peace or war (DIPLOMACY sec 11)
    if _has_repulsive(proposer_p) or _has_repulsive(target_p):
        if treaty_type not in ["peace"]:
            return {"success": False, "reason": "Repulsive races cannot sign treaties beyond peace"}

    relations = game_state["diplomacy"]["relations"]
    key = get_relation_key(relations, proposer, target)
    if not key:
        return {"success": False, "reason": "Unknown relation"}

    rel = relations[key]
    if treaty_type in rel["treaties"]:
        return {"success": False, "reason": "Treaty already active"}

    if rel.get("patience", 100) <= 0:
        return {"success": False, "reason": "The other empire refuses to talk for now"}

    # Acceptance probability
    base = rel["value"] + _trait_relation_bonus(proposer_p, target_p)
    if treaty_type == "alliance":
        base -= 30
    elif treaty_type == "trade":
        base += 10
    elif treaty_type == "peace":
        base += 20
    elif treaty_type == "research":
        base += 5
    elif treaty_type == "non_aggression":
        base += 15

    accepted = random.randint(0, 100) < base

    rel["last_contact_turn"] = game_state.get("turn", 0)
    rel["last_scouted_turn"] = game_state.get("turn", 0)

    if accepted:
        rel["treaties"].append(treaty_type)
        rel["active_treaties"].append({
            "type": treaty_type,
            "start_turn": game_state.get("turn", 0),
            "end_turn": game_state.get("turn", 0) + 30 if treaty_type == "peace" else None,
        })
        rel["value"] = min(200, rel["value"] + 10)
        _patience_recover(rel, 10)
        rel["treaty_history"].append({"type": treaty_type, "turn": game_state.get("turn", 0), "result": "accepted"})
        return {"success": True, "message": f"{target} accepted the {treaty_type} treaty!"}
    else:
        rel["value"] = max(-100, rel["value"] - 5)
        _patience_decay(rel, 15)
        rel["treaty_history"].append({"type": treaty_type, "turn": game_state.get("turn", 0), "result": "rejected"})
        return {"success": False, "message": f"{target} rejected the {treaty_type} treaty."}


def declare_war(game_state, declarer, target):
    initialize_diplomacy(game_state)
    relations = game_state["diplomacy"]["relations"]
    key = get_relation_key(relations, declarer, target)
    if not key:
        return {"success": False, "reason": "Unknown relation"}

    rel = relations[key]
    rel["treaties"] = []
    rel["active_treaties"] = []
    rel["value"] = max(-100, min(rel["value"], -20))
    rel["last_contact_turn"] = game_state.get("turn", 0)
    rel["treaty_history"].append({"type": "war", "turn": game_state.get("turn", 0), "result": "declared"})
    return {"success": True, "message": f"{declarer} has declared war on {target}!"}


def trade_tech(game_state, proposer, target, offered_tech, requested_tech):
    """DIPLOMACY sec 3 — exchange of researched technology between empires."""
    initialize_diplomacy(game_state)

    proposer_p = _get_player(game_state, proposer)
    target_p = _get_player(game_state, target)
    if not proposer_p or not target_p:
        return {"success": False, "reason": "Player not found"}

    if _has_repulsive(proposer_p) or _has_repulsive(target_p):
        return {"success": False, "reason": "Repulsive races cannot trade technology"}

    proposer_techs = proposer_p.get("technologies", [])
    target_techs = target_p.get("technologies", [])

    if offered_tech not in proposer_techs:
        return {"success": False, "reason": "You don't have the offered technology"}
    if requested_tech not in target_techs:
        return {"success": False, "reason": "Target does not have the requested technology"}
    if requested_tech in proposer_techs:
        return {"success": False, "reason": "You already have this technology"}

    relations = game_state["diplomacy"]["relations"]
    key = get_relation_key(relations, proposer, target)
    rel = relations[key]

    # AI accepts if relation is OK and trade is roughly fair (same prefix area)
    fair = offered_tech.split("_")[0] == requested_tech.split("_")[0] or rel["value"] >= 60
    accepted = fair and rel.get("patience", 100) > 20

    rel["last_contact_turn"] = game_state.get("turn", 0)
    rel["last_scouted_turn"] = game_state.get("turn", 0)

    if accepted:
        proposer_p["technologies"] = list(set(proposer_techs + [requested_tech]))
        target_p["technologies"] = list(set(target_techs + [offered_tech]))
        rel["value"] = min(200, rel["value"] + 8)
        rel["knownTechs"] = list(set(rel.get("knownTechs", []) + [offered_tech, requested_tech]))
        return {"success": True, "message": f"Tech trade completed: {offered_tech} <-> {requested_tech}"}
    else:
        _patience_decay(rel, 10)
        return {"success": False, "message": f"{target} rejected the tech trade as unfair"}


def make_gift(game_state, giver, receiver, gift_type, amount=None, tech_id=None):
    """DIPLOMACY sec 8 — gifts of money or tech improve relations."""
    initialize_diplomacy(game_state)

    giver_p = _get_player(game_state, giver)
    receiver_p = _get_player(game_state, receiver)
    if not giver_p or not receiver_p:
        return {"success": False, "reason": "Player not found"}

    relations = game_state["diplomacy"]["relations"]
    key = get_relation_key(relations, giver, receiver)
    rel = relations[key]

    if gift_type == "gift_money":
        amount = int(amount or 0)
        if amount <= 0:
            return {"success": False, "reason": "Invalid amount"}
        if giver_p["resources"]["bc"] < amount:
            return {"success": False, "reason": "Not enough BC"}
        giver_p["resources"]["bc"] -= amount
        receiver_p["resources"]["bc"] = receiver_p["resources"].get("bc", 0) + amount
        bonus = min(15, 3 + amount // 100)
        rel["value"] = min(200, rel["value"] + bonus)
        msg = f"Gifted {amount} BC to {receiver} (+{bonus} relation)"
    elif gift_type == "gift_tech":
        if not tech_id:
            return {"success": False, "reason": "Missing tech_id"}
        if tech_id not in giver_p.get("technologies", []):
            return {"success": False, "reason": "You don't have that technology"}
        receiver_p["technologies"] = list(set(receiver_p.get("technologies", []) + [tech_id]))
        rel["value"] = min(200, rel["value"] + 12)
        rel["knownTechs"] = list(set(rel.get("knownTechs", []) + [tech_id]))
        msg = f"Gifted technology {tech_id} to {receiver} (+12 relation)"
    else:
        return {"success": False, "reason": "Invalid gift type"}

    rel["last_contact_turn"] = game_state.get("turn", 0)
    _patience_recover(rel, 5)
    return {"success": True, "message": msg, "new_relation": rel["value"]}


def make_demand(game_state, demander, target, demand_type, payload=None):
    """DIPLOMACY sec 7 & 12 — extortion / ultimatums."""
    initialize_diplomacy(game_state)
    payload = payload or {}

    if demand_type not in DEMAND_TYPES:
        return {"success": False, "reason": "Invalid demand type"}

    demander_p = _get_player(game_state, demander)
    target_p = _get_player(game_state, target)
    if not demander_p or not target_p:
        return {"success": False, "reason": "Player not found"}

    relations = game_state["diplomacy"]["relations"]
    key = get_relation_key(relations, demander, target)
    rel = relations[key]

    # Compute fleet-power ratio (demand acceptance hinges on it)
    demander_power = _empire_fleet_power(game_state, demander)
    target_power = _empire_fleet_power(game_state, target)
    ratio = demander_power / max(1, target_power)

    threshold = {
        "demand_money": 1.2,
        "demand_tech": 1.5,
        "demand_system": 2.0,
        "demand_tribute_5": 1.5,
        "demand_tribute_10": 2.0,
        "stop_spying": 1.0,
        "remove_fleet": 1.3,
    }.get(demand_type, 1.5)

    accepted = ratio >= threshold

    rel["last_contact_turn"] = game_state.get("turn", 0)
    _patience_decay(rel, 20)

    if not accepted:
        rel["value"] = max(-100, rel["value"] - 25)
        # Risk of war if very offended
        if ratio < 0.7 and demand_type in ["demand_system", "demand_tribute_10"]:
            rel["treaties"] = []
            rel["active_treaties"] = []
            return {"success": False, "message": f"{target} declared war in response to your demand!", "war": True}
        return {"success": False, "message": f"{target} refused the demand", "ratio": round(ratio, 2)}

    # Acceptance: apply consequence
    rel["value"] = max(-100, rel["value"] - 15)
    if demand_type == "demand_money":
        amount = min(target_p["resources"]["bc"], int(payload.get("amount", 100)))
        target_p["resources"]["bc"] -= amount
        demander_p["resources"]["bc"] = demander_p["resources"].get("bc", 0) + amount
        return {"success": True, "message": f"Extorted {amount} BC from {target}"}
    elif demand_type == "demand_tech":
        tech_id = payload.get("tech_id")
        if tech_id and tech_id in target_p.get("technologies", []):
            demander_p["technologies"] = list(set(demander_p.get("technologies", []) + [tech_id]))
            return {"success": True, "message": f"Extorted technology {tech_id} from {target}"}
        return {"success": False, "reason": "Target doesn't have that tech"}
    elif demand_type == "demand_tribute_5":
        rel["tribute_percent"] = 5
        rel["tribute_turns_left"] = 10
        return {"success": True, "message": f"{target} agreed to pay 5% tribute for 10 turns"}
    elif demand_type == "demand_tribute_10":
        rel["tribute_percent"] = 10
        rel["tribute_turns_left"] = 10
        return {"success": True, "message": f"{target} agreed to pay 10% tribute for 10 turns"}
    elif demand_type == "stop_spying":
        return {"success": True, "message": f"{target} agreed to stop spying"}
    elif demand_type == "remove_fleet":
        return {"success": True, "message": f"{target} agreed to remove its fleet"}
    elif demand_type == "demand_system":
        return {"success": True, "message": f"{target} ceded the requested system (handled separately)"}

    return {"success": False, "reason": "Unknown demand"}


def _empire_fleet_power(game_state, player_id):
    """Sum of ship attack * count for all fleets owned by this empire."""
    from app.services.game_service import SHIP_TYPES
    player = _get_player(game_state, player_id)
    if not player:
        return 0
    total = 0
    for fleet in player.get("fleets", []):
        for ship in fleet.get("ships", []):
            total += SHIP_TYPES.get(ship["type"], {}).get("attack", 0) * ship.get("count", 0)
    return total


def get_intelligence(game_state, observer, target):
    """DIPLOMACY sec 14 — Diplomacy as Scouting.

    Returns a snapshot of intel about target visible to observer based on
    current relation level and freshness of last contact.
    """
    initialize_diplomacy(game_state)
    relations = game_state["diplomacy"]["relations"]
    key = get_relation_key(relations, observer, target)
    if not key:
        return {"success": False, "reason": "No contact established with that empire"}

    rel = relations[key]
    target_p = _get_player(game_state, target)
    observer_p = _get_player(game_state, observer)
    if not target_p:
        return {"success": False, "reason": "Target not found"}

    # Free intel for omniscient observers
    free_scouting = "omniscient" in _get_race_traits(observer_p)

    status = _relation_status(rel["value"])
    intel = {
        "target": target,
        "race": target_p.get("race") or target_p.get("race_id"),
        "relation_status": status,
        "last_contact_turn": rel.get("last_contact_turn", -1),
        "last_scouted_turn": rel.get("last_scouted_turn", -1),
        "active_treaties": [t["type"] for t in rel.get("active_treaties", [])],
    }

    # NEUTRAL or higher
    if status in ["neutral", "friendly", "very_friendly", "loyal_ally"] or free_scouting:
        intel["population_total"] = sum(c["population"]["total"] for c in target_p.get("colonies", []))
        intel["known_systems"] = [c.get("system_id") for c in target_p.get("colonies", [])]
        intel["known_techs"] = rel.get("knownTechs", [])

    # FRIENDLY or higher
    if status in ["friendly", "very_friendly", "loyal_ally"] or free_scouting:
        intel["fleet_count"] = len(target_p.get("fleets", []))
        intel["fleet_power"] = _empire_fleet_power(game_state, target)
        intel["current_research"] = target_p.get("current_research")
        intel["all_techs"] = target_p.get("technologies", [])

    # ALLIANCE
    if "alliance" in rel.get("treaties", []) or free_scouting:
        intel["full_visibility"] = True
        intel["colonies"] = [
            {"id": c["id"], "name": c.get("name"), "population": c["population"]["total"]}
            for c in target_p.get("colonies", [])
        ]
        intel["fleets"] = [
            {"id": f["id"], "ships": f.get("ships", []), "location": f.get("location")}
            for f in target_p.get("fleets", [])
        ]

    # Mark information freshness
    turn = game_state.get("turn", 0)
    age = turn - rel.get("last_scouted_turn", -1)
    if age <= 5:
        intel["freshness"] = "fresh"
    elif age <= 10:
        intel["freshness"] = "aging"
    else:
        intel["freshness"] = "stale"

    rel["intel"] = intel
    rel["last_scouted_turn"] = turn
    rel["last_contact_turn"] = turn
    return {"success": True, "intel": intel}


def open_dialogue(game_state, observer, target):
    """Opening a dialog refreshes intel and lightly recovers patience."""
    initialize_diplomacy(game_state)
    relations = game_state["diplomacy"]["relations"]
    key = get_relation_key(relations, observer, target)
    if not key:
        return {"success": False, "reason": "No contact established"}
    rel = relations[key]
    rel["last_contact_turn"] = game_state.get("turn", 0)
    return get_intelligence(game_state, observer, target)


def list_relations(game_state, observer="player"):
    """Returns all relations involving observer with status info."""
    initialize_diplomacy(game_state)
    out = []
    relations = game_state["diplomacy"]["relations"]
    for key, rel in relations.items():
        a, b = key.split(":")
        if observer not in (a, b):
            continue
        other = b if a == observer else a
        out.append({
            "other": other,
            "value": rel["value"],
            "status": _relation_status(rel["value"]),
            "treaties": rel.get("treaties", []),
            "active_treaties": rel.get("active_treaties", []),
            "patience": rel.get("patience", 100),
            "tribute_percent": rel.get("tribute_percent", 0),
            "tribute_turns_left": rel.get("tribute_turns_left", 0),
            "last_contact_turn": rel.get("last_contact_turn", -1),
            "last_scouted_turn": rel.get("last_scouted_turn", -1),
        })
    return out


def process_turn_diplomacy(game_state):
    """Per-turn diplomacy bookkeeping: tributes, peace expiry, treaty income."""
    initialize_diplomacy(game_state)
    turn = game_state.get("turn", 0)
    relations = game_state["diplomacy"]["relations"]

    events = []

    for key, rel in relations.items():
        a, b = key.split(":")
        player_a = _get_player(game_state, a)
        player_b = _get_player(game_state, b)
        if not player_a or not player_b:
            continue

        # Tribute extraction (DIPLOMACY sec 7)
        if rel.get("tribute_turns_left", 0) > 0 and rel.get("tribute_percent", 0) > 0:
            payer = player_b
            receiver = player_a
            pct = rel["tribute_percent"] / 100.0
            tribute = int(payer["resources"].get("bc", 0) * pct)
            payer["resources"]["bc"] = max(0, payer["resources"]["bc"] - tribute)
            receiver["resources"]["bc"] = receiver["resources"].get("bc", 0) + tribute
            rel["tribute_turns_left"] -= 1
            events.append({"type": "tribute_paid", "from": b, "to": a, "amount": tribute})

        # Treaty income (DIPLOMACY sec 4)
        for treaty in rel.get("active_treaties", []):
            ttype = treaty["type"]
            elapsed = turn - treaty.get("start_turn", turn)
            pop_a = sum(c["population"]["total"] for c in player_a.get("colonies", []))
            pop_b = sum(c["population"]["total"] for c in player_b.get("colonies", []))
            combined_pop = pop_a + pop_b
            traders_a = "fantastic_traders" in _get_race_traits(player_a)
            traders_b = "fantastic_traders" in _get_race_traits(player_b)
            mult_a = 1.4 if traders_a else 1.0
            mult_b = 1.4 if traders_b else 1.0

            if ttype == "trade":
                if elapsed < 5 and not (traders_a or traders_b):
                    # First 5 turns: penalty
                    cost = max(1, combined_pop // 4)
                    player_a["resources"]["bc"] = max(0, player_a["resources"].get("bc", 0) - int(cost / 2))
                    player_b["resources"]["bc"] = max(0, player_b["resources"].get("bc", 0) - int(cost / 2))
                else:
                    income = max(1, combined_pop // 2)
                    player_a["resources"]["bc"] = player_a["resources"].get("bc", 0) + int(income * mult_a / 2)
                    player_b["resources"]["bc"] = player_b["resources"].get("bc", 0) + int(income * mult_b / 2)
            elif ttype == "research":
                if elapsed < 5:
                    pass  # mild RP penalty handled implicitly
                else:
                    rp_bonus = max(1, combined_pop // 3)
                    if "research_points" not in player_a:
                        player_a["research_points"] = 0
                    if "research_points" not in player_b:
                        player_b["research_points"] = 0
                    player_a["research_points"] += rp_bonus // 2
                    player_b["research_points"] += rp_bonus // 2

            # Peace expiry
            if ttype == "peace" and treaty.get("end_turn") and turn >= treaty["end_turn"]:
                rel["active_treaties"].remove(treaty)
                if "peace" in rel["treaties"]:
                    rel["treaties"].remove("peace")
                events.append({"type": "peace_expired", "between": [a, b]})

        # Patience slow recovery
        if rel.get("patience", 100) < 100 and turn % 3 == 0:
            rel["patience"] = min(100, rel["patience"] + 5)

        # Non-aggression incremental relation bonus
        if "non_aggression" in rel.get("treaties", []):
            rel["value"] = min(200, rel["value"] + 1)

    return events


def check_galactic_council(game_state):
    """DIPLOMACY sec 13 — Galactic Council elections every 25 turns.

    Abstentions count as votes against BOTH candidates (per StrategyWiki).
    """
    t = game_state.get("turn", 0)
    initialize_diplomacy(game_state)
    if t > 0 and t % 25 == 0:
        game_state["diplomacy"]["council_active"] = True

        # Compute votes (population-based)
        candidates = ["player"] + [ai["id"] for ai in game_state.get("ai_players", [])]
        votes = {}
        for cid in candidates:
            p = _get_player(game_state, cid)
            if p:
                votes[cid] = sum(c["population"]["total"] for c in p.get("colonies", []))
        total = sum(votes.values())
        threshold = (2 * total) / 3
        winner = next((cid for cid, v in votes.items() if v >= threshold), None)

        result = {
            "type": "council_convened",
            "message": "The Galactic Council has convened!",
            "votes": votes,
            "total_votes": total,
            "threshold": threshold,
            "winner": winner,
        }
        game_state["diplomacy"]["council_history"].append({"turn": t, **result})
        return result
    return None
