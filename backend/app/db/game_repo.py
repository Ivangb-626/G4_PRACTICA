from datetime import datetime
from bson import ObjectId
from app.db.database import games


def create_game(user_id: str, name: str, scenario_id: str, game_state: dict):
    now = datetime.utcnow().isoformat()
    doc = {
        'user_id': ObjectId(user_id),
        'name': name,
        'scenario_id': scenario_id,
        'created_at': now,
        'last_saved': now,
        'is_autosave': False,
        'game_state': game_state
    }
    result = games.insert_one(doc)
    return str(result.inserted_id)


def list_games(user_id: str):
    cursor = games.find({'user_id': ObjectId(user_id)}).sort('last_saved', -1)
    out = []
    for g in cursor:
        gs = g['game_state']
        out.append({
            'game_id': str(g['_id']),
            'name': g.get('name'),
            'scenario_id': g.get('scenario_id'),
            'turn': gs.get('turn'),
            'last_saved': g.get('last_saved'),
            'is_autosave': g.get('is_autosave', False),
            'player_race': gs.get('player', {}).get('race', {}).get('id'),
            'galaxy_size': gs.get('galaxy', {}).get('size')
        })
    return out


def get_game(user_id: str, game_id: str):
    try:
        g = games.find_one({'_id': ObjectId(game_id)})
    except Exception:
        return None
    if not g:
        return None
    if str(g['user_id']) != str(user_id):
        return 'forbidden'
    return g


def save_game(user_id: str, game_id: str, game_state: dict, name: str = None, autosave: bool = False):
    now = datetime.utcnow().isoformat()
    query = {'_id': ObjectId(game_id), 'user_id': ObjectId(user_id)}
    update = {'$set': {'game_state': game_state, 'last_saved': now, 'is_autosave': autosave}}
    if name:
        update['$set']['name'] = name
    res = games.update_one(query, update)
    return res.modified_count > 0


def delete_game(user_id: str, game_id: str):
    try:
        res = games.delete_one({'_id': ObjectId(game_id), 'user_id': ObjectId(user_id)})
        return res.deleted_count > 0
    except Exception:
        return False
