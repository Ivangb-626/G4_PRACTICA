from flask import Flask, request, jsonify, g
from flask_cors import CORS
import asyncio

from app.auth.middleware import token_required
from app.auth.password import hash_password, verify_password
from app.auth.jwt_handler import create_token
from app.db.user_repo import create_user, get_by_username, get_by_email, get_by_id, update_last_login
from app.db.game_repo import create_game, list_games, get_game, save_game, delete_game
from app.services.ai_service import AIService
from app.services.game_service import (
    generate_game_state,
    list_scenarios,
    move_fleet,
    colonize_planet,
    set_research,
    end_turn,
    apply_cheat,
    get_galaxy_view,
    get_tech_tree,
    get_colony_detail,
)
from app.services.diplomacy_service import propose_treaty, declare_war, initialize_diplomacy

app = Flask(__name__)
CORS(app)

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if len(username) < 3 or len(username) > 30 or not username.replace('-', '').isalnum():
        return jsonify({'error': 'Invalid username'}), 400
    if '@' not in email or '.' not in email:
        return jsonify({'error': 'Invalid email format'}), 400
    if len(password) < 8:
        return jsonify({'error': 'Password too short'}), 400
    if get_by_username(username):
        return jsonify({'error': 'Username already exists'}), 400
    if get_by_email(email):
        return jsonify({'error': 'Email already registered'}), 400

    password_hash = hash_password(password)
    user = create_user(username, email, password_hash)
    token = create_token(str(user['_id']))

    return jsonify({'user_id': str(user['_id']), 'username': username, 'token': token}), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username', '')
    password = data.get('password', '')

    user = get_by_username(username)
    if not user or not verify_password(password, user['password_hash']):
        return jsonify({'error': 'Invalid credentials'}), 401

    update_last_login(str(user['_id']))
    token = create_token(str(user['_id']))

    return jsonify({'user_id': str(user['_id']), 'username': user['username'], 'token': token})

@app.route('/api/auth/profile', methods=['GET'])
@token_required
def profile():
    user = get_by_id(g.user_id)
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    return jsonify({
        'user_id': str(user['_id']),
        'username': user['username'],
        'email': user['email'],
        'created_at': user['created_at'],
        'games_played': user.get('games_played', 0),
        'games_won': user.get('games_won', 0),
    })

@app.route('/api/games', methods=['GET'])
@token_required
def games_list():
    games = list_games(g.user_id)
    return jsonify({'games': games})

@app.route('/api/games', methods=['POST'])
@token_required
def create_game_route():
    data = request.get_json() or {}
    name = data.get('name', 'New Game')
    scenario_config = data.get('scenario_config', {})

    if scenario_config.get('galaxy_size') not in ['small', 'medium', 'large']:
        return jsonify({'error': 'Invalid galaxy size'}), 400
    if not (1 <= scenario_config.get('num_opponents', 0) <= 3):
        return jsonify({'error': 'Invalid number of opponents'}), 400
    if scenario_config.get('difficulty') not in ['easy', 'normal', 'hard']:
        return jsonify({'error': 'Invalid difficulty'}), 400
    if not scenario_config.get('player_race'):
        return jsonify({'error': 'Player race required'}), 400

    game_state = generate_game_state(name, scenario_config)
    game_id = create_game(g.user_id, name, scenario_config.get('scenario_id', 'default'), game_state)
    game_state['game_id'] = game_id

    return jsonify({'game_id': game_id, 'game_state': game_state}), 201

@app.route('/api/games/<game_id>', methods=['GET'])
@token_required
def load_game(game_id):
    entry = get_game(g.user_id, game_id)
    if entry == 'forbidden':
        return jsonify({'error': 'This game does not belong to you'}), 403
    if not entry:
        return jsonify({'error': 'Game not found'}), 404

    game_state = entry['game_state']
    game_state['game_id'] = game_id
    return jsonify({'game_id': game_id, 'game_state': game_state})

@app.route('/api/games/<game_id>/save', methods=['POST'])
@token_required
def save_game_route(game_id):
    entry = get_game(g.user_id, game_id)
    if entry == 'forbidden':
        return jsonify({'error': 'This game does not belong to you'}), 403
    if not entry:
        return jsonify({'error': 'Game not found'}), 404

    data = request.get_json() or {}
    name = data.get('name')

    success = save_game(g.user_id, game_id, entry['game_state'], name=name)
    if not success:
        return jsonify({'error': 'Failed to save game'}), 500

    return jsonify({'success': True, 'last_saved': entry['game_state'].get('last_saved')})

@app.route('/api/games/<game_id>', methods=['DELETE'])
@token_required
def delete_game_route(game_id):
    success = delete_game(g.user_id, game_id)
    return jsonify({'success': success})

@app.route('/api/games/<game_id>/colony/<colony_id>/manage', methods=['POST'])
@token_required
def manage_colony(game_id, colony_id):
    entry = get_game(g.user_id, game_id)
    if entry == 'forbidden':
        return jsonify({'error': 'This game does not belong to you'}), 403
    if not entry:
        return jsonify({'error': 'Game not found'}), 404

    game_state = entry['game_state']
    data = request.get_json() or {}
    colony = next((c for c in game_state['player']['colonies'] if c['id'] == colony_id), None)
    if not colony:
        return jsonify({'error': 'Colony not found'}), 404

    population = data.get('population', {})
    farmers = population.get('farmers', colony['population']['farmers'])
    workers = population.get('workers', colony['population']['workers'])
    scientists = population.get('scientists', colony['population']['scientists'])

    total = colony['population']['total']
    if farmers + workers + scientists != total:
        return jsonify({'error': 'Population assignment does not match total'}), 400

    colony['population']['farmers'] = farmers
    colony['population']['workers'] = workers
    colony['population']['scientists'] = scientists

    save_game(g.user_id, game_id, game_state)
    return jsonify({'colony': colony, 'validation_warnings': []})

@app.route('/api/games/<game_id>/research', methods=['POST'])
@token_required
def research_route(game_id):
    entry = get_game(g.user_id, game_id)
    if entry == 'forbidden':
        return jsonify({'error': 'This game does not belong to you'}), 403
    if not entry:
        return jsonify({'error': 'Game not found'}), 404

    data = request.get_json() or {}
    try:
        result = set_research(entry['game_state'], data.get('field'), data.get('level'), data.get('tech_id'))
        save_game(g.user_id, game_id, entry['game_state'])
        return jsonify(result)
    except ValueError as err:
        return jsonify({'error': str(err)}), 400

@app.route('/api/games/<game_id>/fleet/<fleet_id>/move', methods=['POST'])
@token_required
def fleet_move_route(game_id, fleet_id):
    entry = get_game(g.user_id, game_id)
    if entry == 'forbidden':
        return jsonify({'error': 'This game does not belong to you'}), 403
    if not entry:
        return jsonify({'error': 'Game not found'}), 404

    destination = request.get_json().get('destination')
    try:
        result = move_fleet(entry['game_state'], fleet_id, destination)
        save_game(g.user_id, game_id, entry['game_state'])
        return jsonify(result)
    except ValueError as err:
        return jsonify({'error': str(err)}), 400

@app.route('/api/games/<game_id>/colonize', methods=['POST'])
@token_required
def colonize_route(game_id):
    entry = get_game(g.user_id, game_id)
    if entry == 'forbidden':
        return jsonify({'error': 'This game does not belong to you'}), 403
    if not entry:
        return jsonify({'error': 'Game not found'}), 404

    data = request.get_json() or {}
    try:
        result = colonize_planet(entry['game_state'], data.get('fleet_id'), data.get('planet_index'))
        save_game(g.user_id, game_id, entry['game_state'])
        return jsonify(result)
    except (ValueError, TypeError) as err:
        return jsonify({'error': str(err)}), 400

@app.route('/api/games/<game_id>/endTurn', methods=['POST'])
@token_required
def end_turn_route(game_id):
    entry = get_game(g.user_id, game_id)
    if entry == 'forbidden':
        return jsonify({'error': 'This game does not belong to you'}), 403
    if not entry:
        return jsonify({'error': 'Game not found'}), 404

    result = end_turn(entry['game_state'])
    save_game(g.user_id, game_id, result['game_state'])
    return jsonify(result)

@app.route('/api/games/<game_id>/ai-turn', methods=['POST'])
@token_required
def ai_turn_route(game_id):
    entry = get_game(g.user_id, game_id)
    if entry == 'forbidden':
        return jsonify({'error': 'This game does not belong to you'}), 403
    if not entry:
        return jsonify({'error': 'Game not found'}), 404

    data = request.get_json() or {}
    ai_id = data.get('ai_id', 'ai_0')
    game_state = entry['game_state']
    ai_player = next((x for x in game_state.get('ai_players', []) if x.get('id') == ai_id), None)
    if not ai_player:
        return jsonify({'error': 'AI player not found'}), 404

    available_actions = {
        'can_colonize': [],
        'can_research': [],
        'available_buildings': {},
        'available_ships': {}
    }

    if ai_player.get('fleets'):
        for fleet in ai_player['fleets']:
            if fleet.get('destination') is None:
                system = next((s for s in game_state['galaxy']['star_systems'] if s['id'] == fleet['star_system_id']), None)
                if system:
                    for p in system.get('planets', []):
                        if p.get('colonized_by') is None and p.get('type') not in ['toxic', 'barren']:
                            available_actions['can_colonize'].append({'fleet_id': fleet['id'], 'system': system['id'], 'planetIndex': p['index']})
                            break

    researched_ids = {t.get('tech_id') for t in ai_player.get('technologies', {}).get('researched', [])}
    if ai_player.get('technologies', {}).get('current_research') is None:
        available_actions['can_research'] = ['fusion_beam']
    else:
        available_actions['can_research'] = []

    for c in ai_player.get('colonies', []):
        available_actions['available_ships'][c['id']] = ['frigate', 'colony_ship']
        available_actions['available_buildings'][c['id']] = ['research_lab', 'shipyard']

    # fallback: simple AI request
    ai_service = AIService()
    request_payload = {
        'game_state': {'turn': game_state.get('turn'), 'ai_player': ai_player, 'galaxy': game_state.get('galaxy'), 'known_enemies': []},
        'personality': ai_player.get('personality', 'balanced'),
        'difficulty': game_state.get('scenario_id', 'normal'),
        'available_actions': available_actions
    }

    ai_response = asyncio.run(ai_service.get_ai_turn(request_payload))
    return jsonify(ai_response)

@app.route('/api/games/<game_id>/cheat', methods=['POST'])
@token_required
def cheat_route(game_id):
    entry = get_game(g.user_id, game_id)
    if entry == 'forbidden':
        return jsonify({'error': 'This game does not belong to you'}), 403
    if not entry:
        return jsonify({'error': 'Game not found'}), 404

    data = request.get_json() or {}
    try:
        result = apply_cheat(entry['game_state'], data.get('cheat_code'), data.get('target'))
        save_game(g.user_id, game_id, entry['game_state'])
        return jsonify({'success': True, 'message': result['message'], 'game_state': result['game_state']})
    except ValueError as err:
        return jsonify({'error': str(err)}), 400

@app.route('/api/games/<game_id>/galaxy', methods=['GET'])
@token_required
def galaxy_route(game_id):
    entry = get_game(g.user_id, game_id)
    if entry == 'forbidden':
        return jsonify({'error': 'This game does not belong to you'}), 403
    if not entry:
        return jsonify({'error': 'Game not found'}), 404

    return jsonify(get_galaxy_view(entry['game_state']))

@app.route('/api/games/<game_id>/tech-tree', methods=['GET'])
@token_required
def tech_tree_route(game_id):
    entry = get_game(g.user_id, game_id)
    if entry == 'forbidden':
        return jsonify({'error': 'This game does not belong to you'}), 403
    if not entry:
        return jsonify({'error': 'Game not found'}), 404

    return jsonify(get_tech_tree(entry['game_state']))

@app.route('/api/games/<game_id>/colony/<colony_id>', methods=['GET'])
@token_required
def colony_detail_route(game_id, colony_id):
    entry = get_game(g.user_id, game_id)
    if entry == 'forbidden':
        return jsonify({'error': 'This game does not belong to you'}), 403
    if not entry:
        return jsonify({'error': 'Game not found'}), 404

    try:
        return jsonify(get_colony_detail(entry['game_state'], colony_id))
    except ValueError as err:
        return jsonify({'error': str(err)}), 404

@app.route('/api/games/<game_id>/diplomacy', methods=['GET'])
@token_required
def diplomacy_status_route(game_id):
    entry = get_game(g.user_id, game_id)
    if entry == 'forbidden':
        return jsonify({'error': 'This game does not belong to you'}), 403
    if not entry:
        return jsonify({'error': 'Game not found'}), 404
        
    game_state = entry['game_state']
    initialize_diplomacy(game_state)
    return jsonify(game_state['diplomacy'])

@app.route('/api/games/<game_id>/diplomacy/propose', methods=['POST'])
@token_required
def propose_treaty_route(game_id):
    entry = get_game(g.user_id, game_id)
    if entry == 'forbidden':
        return jsonify({'error': 'This game does not belong to you'}), 403
    if not entry:
        return jsonify({'error': 'Game not found'}), 404
        
    data = request.get_json() or {}
    target = data.get('target')
    treaty_type = data.get('treaty_type')
    
    try:
        result = propose_treaty(entry['game_state'], 'player', target, treaty_type)
        save_game(g.user_id, game_id, entry['game_state'])
        return jsonify(result)
    except ValueError as err:
        return jsonify({'error': str(err)}), 400

@app.route('/api/scenarios', methods=['GET'])
def scenarios_route():
    return jsonify({'scenarios': list_scenarios()})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
