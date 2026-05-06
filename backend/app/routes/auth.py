from flask import Blueprint, request, jsonify, g
from app.auth.jwt_handler import create_token
from app.auth.middleware import token_required
from app.models.user import UserModel
from app.validation import validate_username, validate_email, validate_password, ValidationError
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    try:
        validate_username(username)
        validate_email(email)
        validate_password(password)
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400

    if UserModel.get_by_username(username):
        return jsonify({"error": "Username already exists"}), 400
    if UserModel.get_by_email(email):
        return jsonify({"error": "Email already exists"}), 400

    user_id = UserModel.create_user(username, email, password)
    return jsonify({"message": "User created", "user_id": user_id}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = UserModel.get_by_username(username)
    from app.auth.password import verify_password
    if not user or not verify_password(password, user['password']):
        return jsonify({"error": "Invalid credentials"}), 401

    token = create_token(str(user['_id']))
    UserModel.update_last_login(str(user['_id']), datetime.utcnow().isoformat())
    
    return jsonify({
        "token": token,
        "username": user['username'],
        "user_id": str(user['_id'])
    }), 200

@auth_bp.route('/profile', methods=['GET'])
@token_required
def profile():
    user = UserModel.get_by_id(g.user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify({
        "username": user['username'],
        "email": user['email'],
        "last_login": user.get('last_login')
    }), 200
