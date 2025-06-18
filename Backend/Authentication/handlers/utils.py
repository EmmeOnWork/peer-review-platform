# handlers/utils.py
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone 
import os

JWT_EXP_DELTA_SECONDS = 3600  # 1 ora di durata

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def generate_jwt_token(user) -> str:
    key_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'private.pem')
    with open(key_path, 'r') as f:
        private_key = f.read()
    payload = {
        "user_id": user.serial_number,
        "role": user.role,
        "exp": datetime.now(timezone.utc) + timedelta(seconds=JWT_EXP_DELTA_SECONDS)
    }
    token = jwt.encode(payload, private_key, algorithm='RS256')
    return token

from .blacklist import is_token_blacklisted

def decode_token(token):
    if is_token_blacklisted(token):
        return None
    try:
        key_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'public.pem')
        with open(key_path, 'r') as f:
            public_key = f.read()
        payload = jwt.decode(token, public_key, algorithms=['RS256'])
        if payload and 'user_id' in payload:
            return payload
        return None
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None