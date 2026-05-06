from bson import ObjectId
from app.db.database import users
from app.auth.password import hash_password, verify_password

class UserModel:
    @staticmethod
    def create_user(username, email, password):
        hashed = hash_password(password)
        doc = {
            "username": username,
            "email": email,
            "password": hashed,
            "last_login": None
        }
        result = users.insert_one(doc)
        return str(result.inserted_id)

    @staticmethod
    def get_by_username(username):
        return users.find_one({"username": username})

    @staticmethod
    def get_by_email(email):
        return users.find_one({"email": email})

    @staticmethod
    def get_by_id(user_id):
        try:
            return users.find_one({"_id": ObjectId(user_id)})
        except:
            return None

    @staticmethod
    def update_last_login(user_id, timestamp):
        users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"last_login": timestamp}}
        )
