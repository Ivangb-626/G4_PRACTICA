import jwt
from datetime import datetime, timedelta
from app.config import JWT_SECRET, JWT_ALGORITHM, JWT_EXP_HOURS


def create_token(user_id: str) -> str:
    payload = {
        'sub': str(user_id),
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXP_HOURS),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> dict:
    decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    return decoded
