"""
diplomacy_service.py — Diplomacia, tratados y Senado Galactico.

API consumida por game_service.py:
- initialize_diplomacy(game_state)
- get_relation_key(relations, owner_a, owner_b)
- check_galactic_council(game_state)
- process_turn_diplomacy(game_state)
- update_diplomacy_relations(game_state)  (alias de process_turn_diplomacy para turn_engine)
- propose_treaty / accept_treaty / declare_war / surrender / gift / demand / propose_tech_trade / blackmail
"""
from __future__ import annotations

import os
import random
import json
from pathlib import Path
from typing import List, Optional

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


with (DATA_DIR / "technologies.json").open("r", encoding="utf-8") as f:
    TECHS = {item["id"]: item for item in json.load(f)}


AI_SERVICE_URL = os.environ.get("AI_SERVICE_URL", "http://ai-service:8001")


def get_relation_key(relations: dict, owner_a: str, owner_b: str) -> Optional[str]:
    if owner_a == owner_b:
        return None
    pair = sorted([str(owner_a), str(owner_b)])
    key = f"{pair[0]}|{pair[1]}"
    return key if key in relations else None


def _make_relation_key(owner_a: str, owner_b: str) -> str:
    pair = sorted([str(owner_a), str(owner_b)])
    return f"{pair[0]}|{pair[1]}"


def initialize_diplomacy(game_state: dict) -> None:
    """Garantiza la estructura diplomatica en game_state.

    Todas las facciones empiezan en estado 'neutral' con valor 0. Solo los
    Antaranos arrancan en guerra eterna (-100).
    """
    diplo = game_state.setdefault("diplomacy", {"relations": {}, "treaties": [], "history": []})
    relations = diplo.setdefault("relations", {})
    treaties = diplo.setdefault("treaties", [])

    factions = ["player", *(ai["id"] for ai in game_state.get("ai_players", []))]
    for i, a in enumerate(factions):
        for b in factions[i + 1 :]:
            key = _make_relation_key(a, b)
            relations.setdefault(key, {"value": 0, "state": "neutral", "last_changed_turn": game_state.get("turn", 1)})

    # Antaranos always hostile
    for f in factions:
        key = _make_relation_key(f, "antaranos")
        relations.setdefault(key, {"value": -100, "state": "war", "last_changed_turn": game_state.get("turn", 1)})

    diplo.setdefault("treaties", treaties)


def _adjust_relation(game_state: dict, a: str, b: str, delta: int) -> None:
    initialize_diplomacy(game_state)
    key = _make_relation_key(a, b)
    rel = game_state["diplomacy"]["relations"].setdefault(key, {"value": 30, "state": "neutral"})
    rel["value"] = max(-100, min(100, rel["value"] + delta))
    rel["last_changed_turn"] = game_state.get("turn", 1)
    if rel["value"] <= -50 and rel["state"] != "war":
        rel["state"] = "hostile"
    elif rel["value"] >= 50:
        rel["state"] = "friendly"
    else:
        if rel["state"] not in ("war",):
            rel["state"] = "neutral"


def _set_state(game_state: dict, a: str, b: str, state: str) -> None:
    initialize_diplomacy(game_state)
    key = _make_relation_key(a, b)
    rel = game_state["diplomacy"]["relations"].setdefault(key, {"value": 0, "state": "neutral"})
    rel["state"] = state
    if state == "war":
        rel["value"] = min(rel["value"], -50)


def _find_empire(game_state: dict, owner_id: str) -> Optional[dict]:
    if owner_id == "player":
        return game_state.get("player")
    return next((ai for ai in game_state.get("ai_players", []) if ai["id"] == owner_id), None)


# ---------- Treaty actions ----------

def propose_treaty(game_state: dict, sender: str, recipient: str, treaty_type: str, terms: dict = None) -> dict:
    initialize_diplomacy(game_state)
    rel_key = _make_relation_key(sender, recipient)
    rel = game_state["diplomacy"]["relations"].get(rel_key, {"value": 30})

    # Charismatic / repulsive
    sender_emp = _find_empire(game_state, sender)
    recipient_emp = _find_empire(game_state, recipient)
    if sender_emp and sender_emp.get("race", {}).get("traits", {}).get("flags", {}).get("repulsive"):
        return {"accepted": False, "reason": "Repulsive races cannot propose treaties."}

    bonus = 0
    if sender_emp and sender_emp.get("race", {}).get("traits", {}).get("flags", {}).get("charismatic"):
        bonus += 20

    # Personality impact
    personality = recipient_emp.get("personality", "balanced") if recipient_emp else "balanced"
    
    if personality == "aggressive":
        bonus -= 15
    elif personality == "researcher" and treaty_type == "research_pact":
        bonus += 15
    elif personality == "expansionist" and treaty_type == "non_aggression_pact":
        bonus -= 10 # Expansionists want to keep options open
    elif personality == "charismatic": # If personality itself is charismatic (special case)
        bonus += 10

    threshold = {"non_aggression_pact": 30, "trade_treaty": 25, "research_pact": 40, "alliance": 60, "tribute": 0}.get(treaty_type, 50)

    accept = (rel.get("value", 0) + bonus) >= threshold or recipient == "player"

    if recipient_emp and recipient_emp.get("race", {}).get("traits", {}).get("flags", {}).get("repulsive") and recipient != "player":
        accept = False

    treaty = {
        "id": f"treaty_{game_state.get('turn', 0)}_{random.randint(1000, 9999)}",
        "type": treaty_type,
        "parties": sorted([sender, recipient]),
        "terms": terms or {},
        "signed_at_turn": game_state.get("turn", 1),
        "expires_at_turn": (game_state.get("turn", 1) + (terms.get("duration", 0) if terms else 0)) if (terms and terms.get("duration")) else None,
        "active": accept,
    }

    if accept:
        game_state["diplomacy"]["treaties"].append(treaty)
        _adjust_relation(game_state, sender, recipient, +10)
        if treaty_type in ("non_aggression_pact", "alliance", "trade_treaty"):
            _set_state(game_state, sender, recipient, "friendly" if treaty_type == "alliance" else "neutral")
    else:
        _adjust_relation(game_state, sender, recipient, -5)

    return {"accepted": accept, "treaty": treaty if accept else None, "reason": "Auto-evaluated"}


def accept_treaty(game_state: dict, treaty_id: str) -> dict:
    initialize_diplomacy(game_state)
    treaty = next((t for t in game_state["diplomacy"]["treaties"] if t["id"] == treaty_id), None)
    if not treaty:
        return {"success": False, "reason": "Treaty not found"}
    treaty["active"] = True
    return {"success": True, "treaty": treaty}


def reject_treaty(game_state: dict, treaty_id: str) -> dict:
    initialize_diplomacy(game_state)
    treaty = next((t for t in game_state["diplomacy"]["treaties"] if t["id"] == treaty_id), None)
    if not treaty:
        return {"success": False, "reason": "Treaty not found"}
    treaty["active"] = False
    return {"success": True}


def declare_war(game_state: dict, sender: str, target: str) -> dict:
    initialize_diplomacy(game_state)
    _set_state(game_state, sender, target, "war")
    _adjust_relation(game_state, sender, target, -100)
    # Cancel all treaties between them
    for t in game_state["diplomacy"]["treaties"]:
        if sorted(t["parties"]) == sorted([sender, target]):
            t["active"] = False
    game_state["diplomacy"].setdefault("history", []).append({
        "turn": game_state.get("turn", 1),
        "type": "war_declared",
        "by": sender,
        "against": target,
    })
    return {"success": True, "state": "war"}


def offer_surrender(game_state: dict, sender: str, target: str) -> dict:
    """sender se rinde a target: target adquiere todas las colonias y flotas."""
    initialize_diplomacy(game_state)
    sender_emp = _find_empire(game_state, sender)
    target_emp = _find_empire(game_state, target)
    if not sender_emp or not target_emp:
        return {"success": False, "reason": "Empire not found"}

    target_emp.setdefault("colonies", []).extend(sender_emp.get("colonies", []))
    for c in target_emp["colonies"]:
        c["owner"] = target
    target_emp.setdefault("fleets", []).extend(sender_emp.get("fleets", []))
    for fl in target_emp["fleets"]:
        fl["owner"] = target

    sender_emp["colonies"] = []
    sender_emp["fleets"] = []
    _set_state(game_state, sender, target, "neutral")
    return {"success": True}


def gift(game_state: dict, sender: str, recipient: str, payload: dict) -> dict:
    initialize_diplomacy(game_state)
    sender_emp = _find_empire(game_state, sender)
    recipient_emp = _find_empire(game_state, recipient)
    if not sender_emp or not recipient_emp:
        return {"success": False, "reason": "Empire not found"}

    total_delta = 0
    tech_already_owned = False
    tech_gifted: Optional[str] = None

    if "bc" in payload:
        amount = max(0, int(payload.get("bc", 0)))
        if sender_emp["resources"].get("bc", 0) < amount:
            return {"success": False, "reason": "Not enough BC"}
        sender_emp["resources"]["bc"] -= amount
        recipient_emp["resources"]["bc"] = recipient_emp["resources"].get("bc", 0) + amount
        bc_delta = max(1, amount // 50)
        _adjust_relation(game_state, sender, recipient, +bc_delta)
        total_delta += bc_delta

    if "tech_id" in payload:
        tech_id = payload["tech_id"]
        # Sender must actually own the tech
        sender_techs = {
            item.get("tech_id")
            for item in sender_emp.get("technologies", {}).get("researched", [])
            if item.get("status") != "discarded"
        }
        if tech_id not in sender_techs:
            return {"success": False, "reason": "Sender does not own this technology"}

        tech_already_owned = any(
            item.get("tech_id") == tech_id
            for item in recipient_emp.get("technologies", {}).get("researched", [])
        )
        if not tech_already_owned:
            tech_data = TECHS.get(tech_id, {})
            field = payload.get("field") or tech_data.get("field", "")
            level = payload.get("level") or tech_data.get("level", 1)
            recipient_emp.setdefault("technologies", {}).setdefault("researched", []).append(
                {"tech_id": tech_id, "field": field, "level": level, "status": "researched"}
            )
            # Diplomacy reward scales with research cost: cheap basic tech
            # (~50 RP) gives +5, expensive late-game tech (~1500 RP) caps near +50.
            research_cost = int(tech_data.get("research_cost", 50) or 50)
            tech_delta = max(5, min(50, research_cost // 30))
            _adjust_relation(game_state, sender, recipient, +tech_delta)
            total_delta += tech_delta
            tech_gifted = tech_id

    return {
        "success": True,
        "delta": total_delta,
        "tech_gifted": tech_gifted,
        "tech_already_owned": tech_already_owned,
    }


def demand(game_state: dict, sender: str, recipient: str, payload: dict) -> dict:
    initialize_diplomacy(game_state)
    rel = game_state["diplomacy"]["relations"].get(_make_relation_key(sender, recipient), {"value": 30})
    accept = rel.get("value", 0) >= 50 or random.random() < 0.20
    if not accept:
        _adjust_relation(game_state, sender, recipient, -15)
        return {"accepted": False, "reason": "Demand rejected"}
    return gift(game_state, recipient, sender, payload)


def propose_tech_trade(game_state: dict, sender: str, recipient: str, offered_tech: str, requested_tech: str) -> dict:
    initialize_diplomacy(game_state)
    sender_emp = _find_empire(game_state, sender)
    recipient_emp = _find_empire(game_state, recipient)
    if not sender_emp or not recipient_emp:
        return {"success": False, "reason": "Empire not found"}

    sender_techs = {item.get("tech_id") for item in sender_emp.get("technologies", {}).get("researched", []) if item.get("status") != "discarded"}
    recipient_techs = {item.get("tech_id") for item in recipient_emp.get("technologies", {}).get("researched", []) if item.get("status") != "discarded"}

    if offered_tech not in sender_techs:
        return {"success": False, "reason": "Sender does not own offered tech"}
    if requested_tech not in recipient_techs:
        return {"success": False, "reason": "Recipient does not own requested tech"}

    # AI evaluation: compare tech levels
    offered_data = TECHS.get(offered_tech, {"level": 1})
    requested_data = TECHS.get(requested_tech, {"level": 1})
    
    # Base value: difference in levels. Positive is good for recipient.
    # recipient wants offered_level >= requested_level
    value_diff = offered_data.get("level", 1) - requested_data.get("level", 1)
    
    rel = game_state["diplomacy"]["relations"].get(_make_relation_key(sender, recipient), {"value": 30})
    rel_val = rel.get("value", 0)
    
    # Threshold for acceptance: requires better relations for unfair trades (negative value_diff)
    # If levels are equal (0), threshold is 25.
    # If offered is better (+1), threshold is 10.
    # If requested is better (-1), threshold is 40.
    threshold = 25 - (value_diff * 15)
    
    accept = rel_val >= threshold or recipient == "player"
    if not accept:
        return {"accepted": False, "reason": "Recipient declined the tech trade (bad deal or bad relations)"}

    # Grant techs
    sender_emp["technologies"]["researched"].append({
        "tech_id": requested_tech, 
        "field": requested_data.get("field", ""), 
        "level": requested_data.get("level", 1), 
        "status": "researched"
    })
    recipient_emp["technologies"]["researched"].append({
        "tech_id": offered_tech, 
        "field": offered_data.get("field", ""), 
        "level": offered_data.get("level", 1), 
        "status": "researched"
    })
    _adjust_relation(game_state, sender, recipient, +10)
    return {"accepted": True}


def ultimatum(game_state: dict, sender: str, recipient: str, payload: dict) -> dict:
    """Demanda algo con amenaza de guerra inmediata si se rechaza."""
    initialize_diplomacy(game_state)
    sender_emp = _find_empire(game_state, sender)
    recipient_emp = _find_empire(game_state, recipient)
    if not sender_emp or not recipient_emp:
        return {"success": False, "reason": "Empire not found"}

    # AI evaluation for ultimatum:
    # 1. Relative power (simplified: number of ships or total CP)
    # 2. Relationship
    # 3. Aggressiveness
    
    sender_power = sum(s.get("count", 0) for f in sender_emp.get("fleets", []) for s in f.get("ships", []))
    recipient_power = sum(s.get("count", 0) for f in recipient_emp.get("fleets", []) for s in f.get("ships", []))
    
    power_ratio = sender_power / max(1, recipient_power)
    rel = game_state["diplomacy"]["relations"].get(_make_relation_key(sender, recipient), {"value": 0})
    rel_val = rel.get("value", 0)
    
    # Acceptance chance: higher if sender is much stronger
    chance = (power_ratio * 20) + (rel_val / 2)
    
    accept = random.randint(1, 100) <= chance or recipient == "player"
    
    if accept:
        res = gift(game_state, recipient, sender, payload)
        _adjust_relation(game_state, sender, recipient, -20) # Relations worsen even if accepted
        return {"accepted": True, "details": res}
    else:
        # Rejected -> War!
        declare_war(game_state, sender, recipient)
        return {"accepted": False, "reason": "Ultimatum rejected. War declared!", "war": True}


def blackmail(game_state: dict, sender: str, recipient: str, leverage: dict) -> dict:
    """Si el sender posee leverage (info comprometedora), extorsiona BC o tech."""
    initialize_diplomacy(game_state)
    sender_emp = _find_empire(game_state, sender)
    recipient_emp = _find_empire(game_state, recipient)
    if not sender_emp or not recipient_emp:
        return {"success": False, "reason": "Empire not found"}

    leverage_strength = leverage.get("strength", 0)
    rel = game_state["diplomacy"]["relations"].get(_make_relation_key(sender, recipient), {"value": 30})
    chance = max(10, min(80, 40 + leverage_strength - max(0, rel.get("value", 0)) // 5))
    if random.randint(1, 100) > chance:
        _adjust_relation(game_state, sender, recipient, -25)
        return {"accepted": False, "reason": "Blackmail attempt failed"}

    bc = min(recipient_emp["resources"].get("bc", 0), 50 + leverage_strength * 10)
    recipient_emp["resources"]["bc"] -= bc
    sender_emp["resources"]["bc"] = sender_emp["resources"].get("bc", 0) + bc
    _adjust_relation(game_state, sender, recipient, -10)
    return {"accepted": True, "bc_extracted": bc}


# ---------- Per-turn maintenance ----------

def process_turn_diplomacy(game_state: dict) -> list:
    """Cada turno: ingresos por tratados comerciales, expiracion, decay leve de relaciones."""
    initialize_diplomacy(game_state)
    events = []
    turn = game_state.get("turn", 1)
    treaties = game_state["diplomacy"]["treaties"]

    for t in treaties:
        if not t.get("active"):
            continue
        # Trade treaty income
        if t["type"] == "trade_treaty":
            for owner_id in t["parties"]:
                emp = _find_empire(game_state, owner_id)
                if not emp:
                    continue
                pop = sum(c.get("population", {}).get("total", 0) if isinstance(c.get("population"), dict) else 0 for c in emp.get("colonies", []))
                income = max(2, pop // 3)
                emp["resources"]["bc"] = emp["resources"].get("bc", 0) + income
            events.append({"type": "trade_treaty_income", "treaty_id": t["id"]})
        # Research pact bonus
        if t["type"] == "research_pact":
            for owner_id in t["parties"]:
                emp = _find_empire(game_state, owner_id)
                cur = emp.get("technologies", {}).get("current_research") if emp else None
                if cur:
                    cur["progress"] = cur.get("progress", 0) + 5
        # Expiration
        if t.get("expires_at_turn") and turn >= t["expires_at_turn"]:
            t["active"] = False
            events.append({"type": "treaty_expired", "treaty_id": t["id"]})

    # Slight decay back toward neutral (0) every turn
    for key, rel in game_state["diplomacy"]["relations"].items():
        if rel.get("state") == "war":
            continue
        target = 0
        v = rel.get("value", 0)
        if v < target:
            rel["value"] = min(target, v + 1)
        elif v > target:
            rel["value"] = max(target, v - 1)

    return events


# Alias for turn_engine.py legacy import
def update_diplomacy_relations(game_state: dict) -> list:
    return process_turn_diplomacy(game_state)


# ---------- Galactic Council ----------

def check_galactic_council(game_state: dict) -> Optional[dict]:
    """Convoca el Senado cada 25 turnos cuando hay 3+ imperios y resuelve la votacion."""
    initialize_diplomacy(game_state)
    turn = game_state.get("turn", 1)
    if turn < 25 or turn % 25 != 0:
        return None

    contacted_empires = ["player", *[ai["id"] for ai in game_state.get("ai_players", []) if ai.get("colonies")]]
    if len(contacted_empires) < 3:
        return None

    # Compute votes by population
    votes = {}
    for owner_id in contacted_empires:
        emp = _find_empire(game_state, owner_id)
        if not emp:
            continue
        pop = sum(
            c.get("population", {}).get("total", 0) if isinstance(c.get("population"), dict) else 0
            for c in emp.get("colonies", [])
        )
        votes[owner_id] = max(1, int(pop))

    total_votes = sum(votes.values())
    if total_votes == 0:
        return None

    # Top 2 candidates
    sorted_emps = sorted(votes.items(), key=lambda kv: kv[1], reverse=True)
    candidates = [sorted_emps[0][0], sorted_emps[1][0]]

    # Each empire votes for the candidate with whom they have better relation (or abstain randomly)
    candidate_votes = {c: 0 for c in candidates}
    for owner_id in contacted_empires:
        if owner_id in candidates:
            candidate_votes[owner_id] += votes[owner_id]
            continue
        rel_a = game_state["diplomacy"]["relations"].get(_make_relation_key(owner_id, candidates[0]), {"value": 30}).get("value", 30)
        rel_b = game_state["diplomacy"]["relations"].get(_make_relation_key(owner_id, candidates[1]), {"value": 30}).get("value", 30)
        if abs(rel_a - rel_b) < 10 or max(rel_a, rel_b) < 20:
            continue  # abstain (counts as negative)
        winner_choice = candidates[0] if rel_a > rel_b else candidates[1]
        candidate_votes[winner_choice] += votes[owner_id]

    # 2/3 majority
    needed = total_votes * 2 / 3
    elected = None
    for c, v in candidate_votes.items():
        if v >= needed:
            elected = c
            break

    event = {
        "type": "galactic_council",
        "turn": turn,
        "candidates": candidates,
        "votes": candidate_votes,
        "total_votes": total_votes,
        "needed": needed,
        "winner": elected,
    }

    if elected and elected == "player":
        game_state["victory_condition"] = "Diplomatic"
    return event
