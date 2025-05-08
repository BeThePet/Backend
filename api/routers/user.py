from core.security import get_current_user
from db.models import User
from db.session import get_db
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from api.schemas.user import UserCreate, UserLogin, UserResponse
from api.services.auth_service import AuthService

router = APIRouter()


@router.post("/signup", response_model=UserResponse)
def signup(user: UserCreate, response: Response, db: Session = Depends(get_db)):
    db_user = AuthService.signup(user, db)
    tokens = AuthService.issue_token_pair(db_user)
    AuthService.set_auth_cookies(
        response, tokens["access_token"], tokens["refresh_token"]
    )
    return UserResponse.from_orm(db_user)


@router.post("/login", response_model=UserResponse)
def login(user: UserLogin, response: Response, db: Session = Depends(get_db)):
    db_user = AuthService.authenticate_user(user.email, user.password, db)
    tokens = AuthService.issue_token_pair(db_user)
    AuthService.set_auth_cookies(
        response, tokens["access_token"], tokens["refresh_token"]
    )
    return UserResponse.from_orm(db_user)


@router.post("/logout")
def logout(response: Response):
    AuthService.clear_auth_cookies(response)
    return {"msg": "로그아웃 완료"}


@router.post("/refresh")
def refresh_token(request: Request, response: Response):
    try:
        new_token = AuthService.refresh_access_token(request, response)
        return {"access_token": new_token}
    except HTTPException as e:
        raise e


@router.get("/me", response_model=UserResponse)
def read_my_info(current_user: User = Depends(get_current_user)):
    return current_user
