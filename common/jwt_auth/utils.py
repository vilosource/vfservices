import jwt
from django.conf import settings
from datetime import datetime, timedelta

def encode_jwt(payload: dict, expires_in: int = 3600) -> str:
    payload = payload.copy()
    payload['exp'] = datetime.utcnow() + timedelta(seconds=expires_in)
    return jwt.encode(payload, settings.JWT_SECRET, algorithm='HS256')

def decode_jwt(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
