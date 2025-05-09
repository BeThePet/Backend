from datetime import datetime, timedelta
from jose import jwt, JWTError
from core.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS


class TokenManager:
    @staticmethod
    def create_access_token(data: dict):
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        data.update({"exp": expire})
        return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def create_refresh_token(data: dict):
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        data.update({"exp": expire})
        return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def decode_token(token: str):
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])