# api/routers/user.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def read_users():
    return {"message": "사용자 목록입니다"}