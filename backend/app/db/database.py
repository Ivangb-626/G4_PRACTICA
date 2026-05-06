from pymongo import MongoClient, ASCENDING, DESCENDING
from app.config import MONGO_URI

client = MongoClient(MONGO_URI)
try:
    db = client.get_default_database()
except Exception:
    db = client.masterdehostias

users = db.users
games = db.games
hall_of_fame = db.hall_of_fame

# Indices as per AGENT-BACKEND.md mandates for 4X-scale performance
users.create_index('username', unique=True)
users.create_index('email', unique=True)

# Optimized indices for Game queries
games.create_index('user_id')
games.create_index([('user_id', ASCENDING), ('last_saved', DESCENDING)])
games.create_index('game_state.turn') # Optimization for turn-processing queries

# HoF index
hall_of_fame.create_index([('score', DESCENDING)])

# Static data cache dictionary
STATIC_CACHE = {}
