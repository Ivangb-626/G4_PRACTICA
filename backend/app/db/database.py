from pymongo import MongoClient
from app.config import MONGO_URI

client = MongoClient(MONGO_URI)
db = client.masterdehostias

users = db.users
games = db.games

# indexes ensure unique constraints
users.create_index('username', unique=True)
users.create_index('email', unique=True)
games.create_index('user_id')
games.create_index([('user_id', 1), ('last_saved', -1)])
