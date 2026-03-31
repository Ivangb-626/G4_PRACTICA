import random
import math
import json
from datetime import datetime
from app.data import races, ships, technologies
from app.services.combat_service import resolve_combat, resolve_ground_combat

# Load static values from json files
with open('backend/app/data/races.json', 'r', encoding='utf-8') as f:
    RACES = {r['id']: r for r in json.load(f)}
with open('backend/app/data/ships.json', 'r', encoding='utf-8') as f:
    SHIP_TYPES = {s['type']: s for s in json.load(f)}
with open('backend/app/data/technologies.json', 'r', encoding='utf-8') as f:
    TECHS = {t['id']: t for t in json.load(f)}

PLANET_TYPES = {
    'toxic': {'habitable': False, 'food_mod': -3},
    'barren': {'habitable': False, 'food_mod': -2},
    'desert': {'habitable': True, 'food_mod': -1},
    'tundra': {'habitable': True, 'food_mod': -1},
    'arid': {'habitable': True, 'food_mod': 0},
    'swamp': {'habitable': True, 'food_mod': 0},
    'ocean': {'habitable': True, 'food_mod': 1},
    'terran': {'habitable': True, 'food_mod': 1},
    'gaia': {'habitable': True, 'food_mod': 2}
}

PLANET_SIZES = {
    'tiny': {'max_pop': 8, 'build_slots': 3},
    'small': {'max_pop': 12, 'build_slots': 4},
    'medium': {'max_pop': 16, 'build_slots': 5},
    'large': {'max_pop': 22, 'build_slots': 7},
    'huge': {'max_pop': 28, 'build_slots': 8}
}

MINERAL_MOD = {
    'ultra_poor': 0.33,
    'poor': 0.66,
    'abundant': 1.0,
    'rich': 1.5,
    'ultra_rich': 2.0
}

STAR_TYPES = {
    'red': {'max_planets': 3, 'bias': ['toxic', 'barren', 'tundra']},
    'orange': {'max_planets': 4, 'bias': ['desert', 'tundra', 'arid']},
    'yellow': {'max_planets': 5, 'bias': list(PLANET_TYPES.keys())},
    'white': {'max_planets': 4, 'bias': ['barren', 'desert', 'terran']},
    'blue': {'max_planets': 3, 'bias': ['toxic', 'barren', 'ultra_rich']}
}

SCENARIOS = [
    {'id': 'default', 'name': 'Estándar', 'description': 'Partida de práctica', 'galaxy_sizes': ['small', 'medium', 'large'], 'max_opponents': 3, 'difficulty_options': ['easy', 'normal', 'hard']}
]


def random_star_type():
    return random.choice(list(STAR_TYPES.keys()))


def random_planet(star_type):
    type_candidates = STAR_TYPES[star_type]['bias']
    ptype = random.choice(type_candidates)
    if ptype == 'ultra_rich':
        ptype = 'gaia'
    size = random.choice(list(PLANET_SIZES.keys()))
    mineral = random.choice(list(MINERAL_MOD.keys()))
    gravity = random.choice(['low', 'normal', 'high'])
    return {
        'index': 0,
        'name': f'{ptype.title()}-{random.randint(100,999)}',
        'type': ptype,
        'size': size,
        'minerals': mineral,
        'gravity': gravity,
        'max_population': PLANET_SIZES[size]['max_pop'],
        'colonized_by': None,
        'special': None
    }


def generate_galaxy(size: str, num_opponents: int, player_race_id: str):
    assert size in ['small', 'medium', 'large']
    counts = {'small': 20, 'medium': 30, 'large': 40}
    num_systems = counts[size]
    systems = []
    for i in range(num_systems):
        star_type = random_star_type()
        num_planets = random.randint(1, STAR_TYPES[star_type]['max_planets'])
        planets = []
        for j in range(num_planets):
            p = random_planet(star_type)
            p['index'] = j
            planets.append(p)
        systems.append({
            'id': f'sys_{i}',
            'name': f'Sistema {i}',
            'position': {'x': random.random() * 100, 'y': random.random() * 100},
            'star_type': star_type,
            'planets': planets,
            'connections': [],
            'explored_by': [],
            'guardian': {'active': False, 'fleet': None}
        })
    # connect graph simply by spanning tree and random extra edges
    for i in range(1, num_systems):
        connect_to = random.randint(0, i-1)
        systems[i]['connections'].append(systems[connect_to]['id'])
        systems[connect_to]['connections'].append(systems[i]['id'])
    # extra connections
    for _ in range(num_systems // 3):
        a, b = random.sample(range(num_systems), 2)
        if systems[b]['id'] not in systems[a]['connections']:
            systems[a]['connections'].append(systems[b]['id'])
            systems[b]['connections'].append(systems[a]['id'])
    # place Orion as sys_0 with gaia planet and guardian
    orion = systems[0]
    orion['name'] = 'Orion'
    orion['star_type'] = 'yellow'
    orion['planets'] = [{
        'index': 0,
        'name': 'Gaia',
        'type': 'gaia',
        'size': 'huge',
        'minerals': 'ultra_rich',
        'gravity': 'normal',
        'max_population': 28,
        'colonized_by': None,
        'special': 'gaia'
    }]
    orion['guardian'] = {'active': True, 'fleet': {'id': 'antaran_guardian', 'owner': 'antaranos', 'star_system_id': orion['id'], 'ships':[{'type':'cruiser','count':1},{'type':'destroyer','count':2}], 'destination':None, 'eta_turns':None, 'command_points_used':0}}
    return {
        'size': size,
        'num_systems': num_systems,
        'star_systems': systems,
        'fog_of_war': {'player': [], 'ai_0': [], 'ai_1': [], 'ai_2': []}
    }


def make_colony(star_system_id, planet_index, owner):
    return {
        'id': f'col_{star_system_id}_{planet_index}',
        'name': f'Colonia-{star_system_id}-{planet_index}',
        'star_system_id': star_system_id,
        'planet_index': planet_index,
        'owner': owner,
        'population': {'total': 1, 'max': 8, 'farmers': 1, 'workers': 0, 'scientists': 0},
        'buildings': [],
        'build_queue': [],
        'morale': 'stable',
        'food_output': 0,
        'food_consumption': 0,
        'industry_output': 0,
        'research_output': 0,
        'bc_output': 0,
        'ground_defense': 0,
        'orbital_defense': 0
    }


def initial_player_state(race_id, system_id):
    race = RACES[race_id]
    colon = make_colony(system_id, 0, 'player')
    return {
        'race': race,
        'resources': {'bc': 200, 'total_food_surplus': 0, 'total_production': 0, 'total_research': 0, 'command_points': 4, 'command_points_used': 0},
        'colonies': [colon],
        'fleets': [
            {'id': f'f_{system_id}_0', 'name': 'Flota inicial A', 'owner': 'player', 'star_system_id': system_id, 'ships':[{'type':'frigate','count':2},{'type':'colony_ship','count':1}], 'destination':None,'eta_turns':None,'command_points_used':2},
            {'id': f'f_{system_id}_1', 'name': 'Flota inicial B', 'owner': 'player', 'star_system_id': system_id, 'ships':[{'type':'frigate','count':2}], 'destination':None,'eta_turns':None,'command_points_used':2}
        ],
        'technologies': {'researched': [], 'current_research': None}
    }


def generate_game_state(name, scenario):
    size = scenario['galaxy_size']
    num_opponents = scenario['num_opponents']
    player_race = scenario['player_race']
    difficulty = scenario.get('difficulty', 'normal')
    galaxy = generate_galaxy(size, num_opponents, player_race)
    # assign starting positions: player sys_1, ai sys_2 etc
    player_sys = galaxy['star_systems'][1]['id']
    galaxy['star_systems'][1]['explored_by'].append('player')
    galaxy['fog_of_war']['player'] = [player_sys] + galaxy['star_systems'][1]['connections']
    galaxy['star_systems'][1]['planets'][0]['colonized_by'] = 'player'
    player_state = initial_player_state(player_race, player_sys)
    # AI players
    ai_states = []
    ai_ids = ['ai_0', 'ai_1', 'ai_2']
    available_races = [r for r in RACES if r != player_race]
    random.shuffle(available_races)
    for i in range(num_opponents):
        sys_index = 2 + i
        if sys_index >= len(galaxy['star_systems']):
            sys_index = i
        sys = galaxy['star_systems'][sys_index]
        sys['explored_by'].append(ai_ids[i])
        sys['planets'][0]['colonized_by'] = ai_ids[i]
        galaxy['fog_of_war'][ai_ids[i]] = [sys['id']] + sys['connections']
        ai_race_id = available_races[i % len(available_races)]
        ai_race = RACES[ai_race_id]
        colony = make_colony(sys['id'], 0, ai_ids[i])
        ai_state = {
            'id': ai_ids[i],
            'race': ai_race,
            'personality': random.choice(['aggressive','defensive','expansionist','researcher','balanced']),
            'diplomacy_stance': 'hostile',
            'resources': {'bc': 200, 'total_food_surplus': 0, 'total_production': 0, 'total_research': 0, 'command_points': 4, 'command_points_used': 0},
            'colonies': [colony],
            'fleets': [{'id': f'fleet_{ai_ids[i]}', 'name': f'AI Fleet {i}', 'owner': ai_ids[i], 'star_system_id': sys['id'], 'ships':[{'type':'frigate','count':2}], 'destination':None, 'eta_turns':None, 'command_points_used':2}],
            'technologies': {'researched': [], 'current_research': None}
        }
        ai_states.append(ai_state)
    return {
        'game_id': None,
        'name': name,
        'scenario_id': 'default',
        'turn': 1,
        'current_player': 'player',
        'created_at': datetime.utcnow().isoformat(),
        'last_saved': datetime.utcnow().isoformat(),
        'is_autosave': False,
        'cheats_used': [],
        'antaran_next_attack_turn': 15 + random.randint(0,5),
        'victory_condition': None,
        'player': player_state,
        'ai_players': ai_states,
        'galaxy': galaxy
    }


def get_game_safe(game_state, user='player'):
    return game_state


def find_fleet(game_state, fleet_id):
    for f in game_state['player']['fleets']:
        if f['id'] == fleet_id:
            return f
    return None


def find_system(game_state, system_id):
    return next((s for s in game_state['galaxy']['star_systems'] if s['id']==system_id), None)


def move_fleet(game_state, fleet_id, destination):
    fleet = find_fleet(game_state, fleet_id)
    if not fleet:
        raise ValueError('Fleet not found')
    if fleet['destination']:
        raise ValueError('Fleet already in transit')
    current = find_system(game_state, fleet['star_system_id'])
    if not current:
        raise ValueError('Current system missing')
    if destination not in current['connections']:
        raise ValueError('Destination not reachable')
    dest = find_system(game_state, destination)
    if not dest:
        raise ValueError('Destination not found')
    slowest = min(SHIP_TYPES[s['type']]['speed'] for s in fleet['ships'] if s['count']>0)
    eta = math.ceil(1 / slowest)  # always 1 for simplicity as distance=1
    fleet['destination'] = destination
    fleet['eta_turns'] = eta
    return {'fleet': fleet, 'path':[current['id'], destination]}


def colonize_planet(game_state, fleet_id, planet_index):
    fleet = find_fleet(game_state, fleet_id)
    if not fleet:
        raise ValueError('Fleet not found')
    colony_ship = next((s for s in fleet['ships'] if s['type']=='colony_ship' and s['count']>0), None)
    if not colony_ship:
        raise ValueError('No colony ship in fleet')
    system = find_system(game_state, fleet['star_system_id'])
    if not system:
        raise ValueError('System not found')
    if planet_index < 0 or planet_index >= len(system['planets']):
        raise ValueError('Invalid planet index')
    planet = system['planets'][planet_index]
    if planet['colonized_by'] is not None:
        raise ValueError('Planet already colonized')
    if planet['type'] in ['toxic','barren']:
        raise ValueError('Planet not colonizable by default')
    planet['colonized_by'] = 'player'
    colony_ship['count'] -= 1
    new_colony = make_colony(system['id'], planet_index, 'player')
    game_state['player']['colonies'].append(new_colony)
    return {'new_colony': new_colony, 'fleet': fleet}


def set_research(game_state, field, level, tech_id):
    tech = TECHS.get(tech_id)
    if not tech or tech['field'] != field or tech['level'] != level:
        raise ValueError('Technology not available')
    research = game_state['player']['technologies']
    if any(t['field']==field and t['level']==level for t in research['researched']):
        raise ValueError('Already researched')
    # require previous level
    if level > 1 and not any(t['field']==field and t['level']==level-1 for t in research['researched']):
        raise ValueError('Previous level not completed')
    research['current_research'] = {'field':field,'level':level,'tech_id':tech_id,'progress':0,'total_cost':tech['research_cost']}
    return {'current_research': research['current_research']}


def apply_research(game_state):
    research = game_state['player']['technologies']['current_research']
    if not research:
        return None
    total_research = 0
    for c in game_state['player']['colonies']:
        total_research += c.get('research_output',0)
    research['progress'] += total_research
    if research['progress']>=research['total_cost']:
        game_state['player']['technologies']['researched'].append({'field':research['field'],'level':research['level'],'tech_id':research['tech_id']})
        game_state['player']['technologies']['current_research']=None
        return {'event':'research_complete','tech_id':research['tech_id']}
    return None


def compute_colony_economy(game_state):
    total_bc = 0
    total_research = 0
    total_production = 0
    total_food_surplus = 0
    for colony in game_state['player']['colonies']:
        ptype = find_system(game_state,colony['star_system_id'])['planets'][colony['planet_index']]['type']
        food_mod = PLANET_TYPES[ptype]['food_mod']
        farmers = colony['population']['farmers']
        workers = colony['population']['workers']
        scientists = colony['population']['scientists']
        total = colony['population']['total']
        race = game_state['player']['race']
        food_per_farmer = 1 + food_mod + race['traits'].get('food_bonus', 0)
        food_prod = max(0, farmers * food_per_farmer)
        food_consume = total
        surplus = food_prod - food_consume
        colony['food_output'] = food_prod
        colony['food_consumption'] = food_consume
        colony['food_surplus'] = surplus
        if surplus < 0:
            colony['population']['total'] = max(1, colony['population']['total'] - 1)
        else:
            growth_rate = 0.5 * (1 + race['traits'].get('population_growth_bonus',0)/100) * (1 - total / colony['population']['max'])
            colony['population']['total'] = min(colony['population']['max'], colony['population']['total'] + max(0, growth_rate))
        base_prod = workers * 2
        mineral_mod = MINERAL_MOD[find_system(game_state,colony['star_system_id'])['planets'][colony['planet_index']]['minerals']]
        race_industry_bonus = race['traits'].get('industry_bonus',0) * workers
        production = (base_prod + race_industry_bonus) * mineral_mod
        colony['industry_output'] = production
        research = scientists * 2 + race['traits'].get('research_bonus',0)
        colony['research_output'] = research
        bc = race['traits'].get('trade_bonus',0) * colony['population']['total']
        colony['bc_output'] = bc
        total_bc += bc
        total_research += research
        total_production += production
        total_food_surplus += surplus
    game_state['player']['resources']['total_bc'] = total_bc
    game_state['player']['resources']['total_research'] = total_research
    game_state['player']['resources']['total_production'] = total_production
    game_state['player']['resources']['total_food_surplus'] = total_food_surplus
    return game_state


def process_fleet_movements(game_state):
    events=[]
    for fleet in game_state['player']['fleets']:
        if fleet['eta_turns'] is not None:
            fleet['eta_turns'] -= 1
            if fleet['eta_turns'] <=0:
                fleet['star_system_id']=fleet['destination']
                if fleet['destination'] not in game_state['galaxy']['fog_of_war']['player']:
                    game_state['galaxy']['fog_of_war']['player'].append(fleet['destination'])
                fleet['destination']=None
                fleet['eta_turns']=None
                events.append({'type':'fleet_arrival','fleet_id':fleet['id'],'system':fleet['star_system_id']})
    
    # Process AI fleets too
    for ai in game_state.get('ai_players', []):
        for fleet in ai.get('fleets', []):
            if fleet.get('eta_turns') is not None:
                fleet['eta_turns'] -= 1
                if fleet['eta_turns'] <= 0:
                    fleet['star_system_id']=fleet['destination']
                    if fleet['destination'] not in game_state['galaxy']['fog_of_war'][ai['id']]:
                        game_state['galaxy']['fog_of_war'][ai['id']].append(fleet['destination'])
                    fleet['destination']=None
                    fleet['eta_turns']=None
                    events.append({'type':'fleet_arrival','fleet_id':fleet['id'],'system':fleet['star_system_id']})
                    
    return events


def resolve_space_combats(game_state):
    events = []
    # Collect all fleets by system
    system_fleets = {}
    
    all_players_fleets = [('player', f) for f in game_state['player']['fleets']]
    for ai in game_state.get('ai_players', []):
        all_players_fleets.extend([(ai['id'], f) for f in ai.get('fleets', [])])
        
    # Also add guardian fleet if active
    for sys in game_state['galaxy']['star_systems']:
        if sys.get('guardian', {}).get('active') and sys['guardian'].get('fleet'):
            all_players_fleets.append(('antaranos', sys['guardian']['fleet']))

    for owner, fleet in all_players_fleets:
        if fleet.get('eta_turns') is None and fleet.get('star_system_id'):
            sys_id = fleet['star_system_id']
            system_fleets.setdefault(sys_id, []).append((owner, fleet))
            
    for sys_id, fleets in system_fleets.items():
        owners_present = {owner for owner, _ in fleets}
        if len(owners_present) > 1:
            # Combat! For simplicity, let's just match the first two different owners
            owners_list = list(owners_present)
            att_owner = owners_list[0]
            def_owner = owners_list[1]
            
            att_fleets = [f for o, f in fleets if o == att_owner]
            def_fleets = [f for o, f in fleets if o == def_owner]
            
            # Combine fleets for combat resolution
            att_combined = {'ships': []}
            for f in att_fleets: att_combined['ships'].extend(f['ships'])
            def_combined = {'ships': []}
            for f in def_fleets: def_combined['ships'].extend(f['ships'])
            
            combat_result = resolve_combat(att_combined, def_combined)
            
            # Update fleets based on survivors
            # In a full implementation, we'd distribute survivors. For now, replace first fleet and empty the rest.
            if att_fleets:
                att_fleets[0]['ships'] = combat_result['attacker_remaining']
                for f in att_fleets[1:]: f['ships'] = []
            if def_fleets:
                def_fleets[0]['ships'] = combat_result['defender_remaining']
                for f in def_fleets[1:]: f['ships'] = []
                
            events.append({
                'type': 'combat_resolved', 
                'system_id': sys_id, 
                'winner': combat_result['winner'],
                'attacker': att_owner,
                'defender': def_owner
            })
            
    # Cleanup empty fleets
    game_state['player']['fleets'] = [f for f in game_state['player']['fleets'] if f['ships']]
    for ai in game_state.get('ai_players', []):
        ai['fleets'] = [f for f in ai.get('fleets', []) if f['ships']]
        
    for sys in game_state['galaxy']['star_systems']:
        if sys.get('guardian', {}).get('active') and sys['guardian'].get('fleet'):
            if not sys['guardian']['fleet']['ships']:
                sys['guardian']['active'] = False
                sys['guardian']['fleet'] = None
                
    return events


def check_victory(game_state):
    player_colonies=len(game_state['player']['colonies'])
    player_fleets=len([f for f in game_state['player']['fleets'] if f])
    ai_colonies=sum(len(ai['colonies']) for ai in game_state['ai_players'])
    ai_fleets=sum(len(ai['fleets']) for ai in game_state['ai_players'])
    if ai_colonies==0 and ai_fleets==0:
        game_state['victory_condition']='Conquista'
        return 'victory'
    if player_colonies==0 and player_fleets==0:
        game_state['victory_condition']='Derrota'
        return 'defeat'
    return None


def end_turn(game_state):
    events=[]
    compute_colony_economy(game_state)
    res = apply_research(game_state)
    if res:
        events.append(res)
    events += process_fleet_movements(game_state)
    combat_events = resolve_space_combats(game_state)
    events += combat_events
    
    # Executing AI turn heuristically internally, for seamless backend advancement (Optionally, could call ai_service here)
    from app.services.ai_service import AIService
    import asyncio
    
    ai_service = AIService()
    for ai_player in game_state.get('ai_players', []):
        # Build available_actions (simplified)
        available_actions = {'can_colonize': [], 'can_research': [], 'available_buildings': {}, 'available_ships': {}}
        for fleet in ai_player.get('fleets', []):
            if not fleet.get('destination'):
                available_actions['can_colonize'].append({'fleet_id': fleet['id'], 'system': fleet['star_system_id'], 'planetIndex': 0})
        
        request_payload = {
            'game_state': {'turn': game_state.get('turn'), 'ai_player': ai_player},
            'personality': ai_player.get('personality', 'balanced'),
            'difficulty': game_state.get('difficulty', 'normal'),
            'available_actions': available_actions
        }
        # In a real app we might await this asynchronously or use a background task.
        # Since end_turn is synchronous here, we use asyncio.run to fetch AI actions if ai_service relies on LLM.
        # For performance, could use simple heuristics instead if no LLM configured.
        
    # simple antaranos event
    t=game_state['turn']
    ant = game_state.get('antaran_next_attack_turn')
    if ant is not None and t>=ant:
        game_state['antaran_next_attack_turn']=t+10
        events.append({'type':'antaran_attack','target':'random'})
    victory=check_victory(game_state)
    if victory:
        events.append({'type':victory})
    game_state['turn'] +=1
    game_state['last_saved']=datetime.utcnow().isoformat()
    return {'game_state':game_state, 'events':events, 'turn':game_state['turn']}


def apply_cheat(game_state, cheat_code, target=None):
    cheat_code = cheat_code.lower()
    if cheat_code in game_state['cheats_used']:
        pass
    game_state['cheats_used'].append(cheat_code)
    if cheat_code=='recursos_infinitos':
        game_state['player']['resources']['bc']=99999
        for c in game_state['player']['colonies']:
            c['food_output']=999
        return {'message':'Recursos infinitos aplicados','game_state':game_state}
    if cheat_code=='revelar_galaxia':
        game_state['galaxy']['fog_of_war']['player']=[s['id'] for s in game_state['galaxy']['star_systems']]
        return {'message':'Galaxia revelada','game_state':game_state}
    if cheat_code=='tecnologia_total':
        for t in TECHS.values():
            if not any(r['tech_id']==t['id'] for r in game_state['player']['technologies']['researched']):
                game_state['player']['technologies']['researched'].append({'field':t['field'],'level':t['level'],'tech_id':t['id']})
        return {'message':'Todas las tecnologías investigadas','game_state':game_state}
    if cheat_code=='flota_invencible':
        if not target or target.get('type')!='star_system' or not target.get('id'):
            raise ValueError('Target required')
        star = find_system(game_state,target['id'])
        if not star: raise ValueError('Star system not found')
        star_fleet={'id':'cheat_invincible','owner':'player','star_system_id':star['id'],'ships':[{'type':'battleship','count':10}],'destination':None,'eta_turns':None,'command_points_used':80}
        game_state['player']['fleets'].append(star_fleet)
        return {'message':'Flota invencible creada','game_state':game_state}
    if cheat_code=='victoria_inmediata':
        game_state['victory_condition']='Conquista'
        return {'message':'Victoria inmediata','game_state':game_state}
    if cheat_code=='derrota_inmediata':
        game_state['victory_condition']='Derrota'
        return {'message':'Derrota inmediata','game_state':game_state}
    if cheat_code=='colonizar_todo':
        if not target or target.get('type')!='star_system' or not target.get('id'):
            raise ValueError('Target required')
        star=find_system(game_state,target['id'])
        if not star: raise ValueError('Star system not found')
        for planet in star['planets']:
            if planet['colonized_by'] is None:
                planet['colonized_by']='player'
                game_state['player']['colonies'].append(make_colony(star['id'],planet['index'],'player'))
        return {'message':'Sistema colonizado completamente','game_state':game_state}
    if cheat_code=='poblacion_maxima':
        if not target or target.get('type')!='colony' or not target.get('id'):
            raise ValueError('Target required')
        colony = next((c for c in game_state['player']['colonies'] if c['id']==target['id']),None)
        if not colony: raise ValueError('Colony not found')
        colony['population']['total']=colony['population']['max']
        return {'message':'Población máxima','game_state':game_state}
    if cheat_code=='naves_gratis':
        game_state['player']['resources']['free_ship']=True
        return {'message':'Naves gratis este turno','game_state':game_state}
    if cheat_code=='guardian_eliminado':
        orion = next((s for s in game_state['galaxy']['star_systems'] if s['name']=='Orion'),None)
        if orion: orion['guardian']['active']=False
        return {'message':'Guardián eliminado','game_state':game_state}
    if cheat_code=='antaranos_desactivados':
        game_state['antaran_next_attack_turn']=None
        return {'message':'Antaranos desactivados','game_state':game_state}
    raise ValueError('Invalid cheat code')


def list_scenarios():
    return SCENARIOS


def get_galaxy_view(game_state):
    visible = set(game_state['galaxy']['fog_of_war']['player'])
    out=[]
    for sys in game_state['galaxy']['star_systems']:
        seen = sys['id'] in visible
        out.append({
            'id': sys['id'],
            'name': sys['name'],
            'position': sys['position'],
            'star_type': sys['star_type'],
            'explored': seen,
            'planets': sys['planets'] if seen else [],
            'connections': sys['connections'],
            'has_player_colony': any(c['star_system_id']==sys['id'] for c in game_state['player']['colonies']),
            'has_player_fleet': any(f['star_system_id']==sys['id'] and f['destination'] is None for f in game_state['player']['fleets']),
            'has_enemy_fleet': seen and any(f['star_system_id']==sys['id'] and f['owner']!='player' for a in game_state['ai_players'] for f in a['fleets'])
        })
    return {'star_systems': out}


def get_colony_detail(game_state, colony_id):
    colony = next((c for c in game_state['player']['colonies'] if c['id']==colony_id),None)
    if not colony:
        raise ValueError('Colony not found')
    available_buildings = []
    available_ships = []
    return {'colony': colony, 'available_buildings': available_buildings, 'available_ships': available_ships}


def get_tech_tree(game_state):
    fields = {}
    for t in TECHS.values():
        fields.setdefault(t['field'], []).append(t)
    output = []
    researched = {r['tech_id'] for r in game_state['player']['technologies']['researched']}
    current = game_state['player']['technologies']['current_research']
    for field, techs in fields.items():
        levels = {}
        for t in techs:
            status = 'researched' if t['id'] in researched else 'available'
            if current and current['tech_id']==t['id']:
                status = 'current'
            levels.setdefault(t['level'], []).append({
                'tech_id':t['id'],'name':t['name'],'description':'','research_cost':t['research_cost'],'status':status,'unlocks':t['unlocks']
            })
        output.append({'field':field,'levels':[{'level':l,'options':levels[l]} for l in sorted(levels)]})
    return {'fields': output, 'current_research': current}
