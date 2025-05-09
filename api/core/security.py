from core.token_manager import TokenManager
from db.models import User
from db.session import get_db
from fastapi import HTTPException, Request, status
from jose import ExpiredSignatureError, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import Depends

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=400, detail="Access token이 쿠키에 없습니다.")
    try:
        payload = TokenManager.decode_token(token)
        email = payload.get("sub")
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")
        return user
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Access token이 만료되었습니다.")
    except JWTError:
        raise HTTPException(status_code=401, detail="Access token이 유효하지 않습니다.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")
