from datetime import datetime
from bson import ObjectId
from app.db.database import users


def create_user(username: str, email: str, password_hash: str) -> dict:
    now = datetime.utcnow().isoformat()
    user = {
        'username': username,
        'email': email,
        'password_hash': password_hash,
        'created_at': now,
        'last_login': now,
        'games_played': 0,
        'games_won': 0
    }
    result = users.insert_one(user)
    user['_id'] = str(result.inserted_id)
    return user


def get_by_username(username: str):
    return users.find_one({'username': username})


def get_by_email(email: str):
    return users.find_one({'email': email})


def get_by_id(user_id: str):
    try:
        return users.find_one({'_id': ObjectId(user_id)})
    except Exception:
        return None


def update_last_login(user_id: str):
    users.update_one({'_id': ObjectId(user_id)}, {'$set': {'last_login': datetime.utcnow().isoformat()}})
