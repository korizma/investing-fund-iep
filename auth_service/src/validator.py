import re
import jwt
import os
from .models import User
from datetime import datetime, timedelta, timezone
from typing import Tuple

EMAIL_PATTERN = re.compile(r"[a-zA-Z][a-zA-Z0-9._]*@([a-zA-Z][a-zA-Z0-9]*\.)+[a-zA-Z]+")

JWT_ALGO = "HS256"
JWT_EXP_TIME_MIN = 60
JWT_SECRET_KEY_LOCATION = "JWT_SECRET_KEY"

def validate_password(password : str) -> bool:
    if len(password) < 8:
        return False
    else:
        return True
    
def validate_email(email : str) -> bool:
    if EMAIL_PATTERN.fullmatch(email) is not None:
        return True
    else:
        return False

def get_jwt_secret():
    return os.environ[JWT_SECRET_KEY_LOCATION]

def create_jwt(user: User) -> str:
    payload = {
        "forename": user.forename,
        "surname": user.surname,
        "email": user.email,
        "role": user.role,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=JWT_EXP_TIME_MIN),
    }

    token: str = jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGO)

    return token

def validate_jwt(token: str) -> Tuple[bool, str]:
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGO])
    except jwt.ExpiredSignatureError:
        return False, ""
    except jwt.InvalidTokenError:
        return False, ""

    return True, payload["email"]