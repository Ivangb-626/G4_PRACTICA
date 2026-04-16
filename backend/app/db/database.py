from pymongo import MongoClient
from app.config import MONGO_URI

client = MongoClient(MONGO_URI)
# Use the DB from URI when present (e.g. mongodb://.../mydb).
# Fallback keeps compatibility with existing local setup.
try:
    db = client.get_default_database()
except Exception:
    db = None
if db is None:
    db = client.masterdehostias

users = db.users
games = db.games

# indexes ensure unique constraints
users.create_index('username', unique=True)
users.create_index('email', unique=True)
games.create_index('user_id')
games.create_index([('user_id', 1), ('last_saved', -1)])
