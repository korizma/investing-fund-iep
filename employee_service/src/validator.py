import jwt
import os
from datetime import datetime, timedelta, timezone
from typing import Tuple

JWT_ALGO = "HS256"
JWT_EXP_TIME_MIN = 60
JWT_SECRET_KEY_LOCATION = "JWT_SECRET_KEY"


def get_jwt_secret():
    return os.environ[JWT_SECRET_KEY_LOCATION]

def validate_jwt(token: str) -> Tuple[bool, str]:
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGO])
    except jwt.ExpiredSignatureError:
        return False
    except jwt.InvalidTokenError:
        return False

    if payload['role'] != 'employee':
        return False

    return True

def extract_jwt(header: str) -> str | None:
    if header is None:
        return None

    # auth header is: "Authorization" : "Bearer <ACCESS_TOKEN>"
    parts = header.split()

    if len(parts) != 2 or parts[0] != "Bearer":
        return None

    token = parts[1]

    return token