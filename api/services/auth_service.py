from core.token_manager import TokenManager
from db.models import User
from fastapi import HTTPException, Request, Response
from passlib.context import CryptContext
from sqlalchemy.orm import Session

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    @staticmethod
    def authenticate_user(email: str, password: str, db: Session) -> User:
        user = db.query(User).filter(User.email == email).first()
        if not user or not pwd_context.verify(password, user.hashed_password):
            raise HTTPException(status_code=401, detail="잘못된 로그인 정보")
        return user

    @staticmethod
    def issue_token_pair(user: User) -> dict:
        return {
            "access_token": TokenManager.create_access_token(data={"sub": user.email}),
            "refresh_token": TokenManager.create_refresh_token(
                data={"sub": user.email}
            ),
        }

    @staticmethod
    def set_auth_cookies(response: Response, access_token: str, refresh_token: str):
        response.set_cookie(key="access_token", value=access_token, httponly=True)
        response.set_cookie(key="refresh_token", value=refresh_token, httponly=True)
        return response

    @staticmethod
    def create_user(email: str, password: str, nickname: str, db: Session) -> User:
        if db.query(User).filter(User.email == email).first():
            raise HTTPException(status_code=400, detail="이미 존재하는 이메일")
        if db.query(User).filter(User.nickname == nickname).first():
            raise HTTPException(status_code=400, detail="이미 존재하는 닉네임")

        hashed = pwd_context.hash(password)
        new_user = User(email=email, hashed_password=hashed, nickname=nickname)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    @staticmethod
    def signup(user_data, db: Session) -> User:
        return AuthService.create_user(
            email=user_data.email,
            password=user_data.password,
            nickname=user_data.nickname,
            db=db,
        )

    @staticmethod
    def clear_auth_cookies(response: Response):
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        return response

    @staticmethod
    def refresh_access_token(request: Request, response: Response):
        token = request.cookies.get("refresh_token")
        if not token:
            raise HTTPException(status_code=403, detail="Refresh token 없음")

        try:
            payload = TokenManager.decode_token(token)
            email = payload.get("sub")
            new_access_token = TokenManager.create_access_token(data={"sub": email})
            response.set_cookie(
                key="access_token", value=new_access_token, httponly=True
            )
            return new_access_token
        except:
            raise HTTPException(status_code=403, detail="유효하지 않은 refresh token")
