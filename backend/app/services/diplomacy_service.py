def initialize_diplomacy(game_state):
    """Initializes the diplomacy structures in the game state if missing."""
    if 'diplomacy' not in game_state:
        game_state['diplomacy'] = {
            'relations': {}, # "owner1_owner2": { "value": 50, "treaties": ["peace"] }
            'council_active': False
        }
    
    entities = ['player'] + [ai['id'] for ai in game_state.get('ai_players', [])]
    for i in range(len(entities)):
        for j in range(i + 1, len(entities)):
            pair_key = f"{entities[i]}:{entities[j]}"
            alt_key = f"{entities[j]}:{entities[i]}"
            if pair_key not in game_state['diplomacy']['relations'] and alt_key not in game_state['diplomacy']['relations']:
                game_state['diplomacy']['relations'][pair_key] = {
                    'value': 50, # 0 = war, 100 = alliance
                    'treaties': []
                }
    return game_state

def get_relation_key(relations, faction1, faction2):
    k1 = f"{faction1}:{faction2}"
    k2 = f"{faction2}:{faction1}"
    if k1 in relations: return k1
    if k2 in relations: return k2
    return None

def propose_treaty(game_state, proposer, target, treaty_type):
    initialize_diplomacy(game_state)
    relations = game_state['diplomacy']['relations']
    key = get_relation_key(relations, proposer, target)
    if not key:
        raise ValueError("Unknown relation")
    
    rel = relations[key]
    if treaty_type in rel['treaties']:
        return {"success": False, "reason": "Treaty already active"}
    
    # Simple acceptance logic based on relation value
    acceptance_chance = rel['value']
    if treaty_type == 'alliance':
        acceptance_chance -= 30
    elif treaty_type == 'trade':
        acceptance_chance += 10
    elif treaty_type == 'peace':
        acceptance_chance += 20
        
    import random
    if random.randint(0, 100) < acceptance_chance:
        rel['treaties'].append(treaty_type)
        rel['value'] = min(100, rel['value'] + 10)
        return {"success": True, "message": f"{target} accepted the {treaty_type} treaty!"}
    else:
        rel['value'] = max(0, rel['value'] - 5)
        return {"success": False, "message": f"{target} rejected the {treaty_type} treaty."}

def declare_war(game_state, declarer, target):
    initialize_diplomacy(game_state)
    relations = game_state['diplomacy']['relations']
    key = get_relation_key(relations, declarer, target)
    if not key:
        raise ValueError("Unknown relation")
    
    rel = relations[key]
    rel['treaties'] = [] # Cancel all treaties
    rel['value'] = 0
    return {"success": True, "message": f"{declarer} has declared war on {target}!"}

def check_galactic_council(game_state):
    """
    Called every few turns to determine if Galactic Council meets to elect a supreme leader.
    """
    t = game_state.get('turn', 0)
    initialize_diplomacy(game_state)
    if t > 0 and t % 25 == 0:
        game_state['diplomacy']['council_active'] = True
        return {"type": "council_convened", "message": "The Galactic Council has convened!"}
    return None
