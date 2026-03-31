from functools import wraps
from flask import request, jsonify, g
from app.auth.jwt_handler import verify_token


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Unauthorized'}), 401
        token = auth_header.split(' ', 1)[1]
        try:
            data = verify_token(token)
            g.user_id = data.get('sub')
        except Exception as e:
            return jsonify({'error': 'Unauthorized', 'details': str(e)}), 401
        return f(*args, **kwargs)

    return decorated
