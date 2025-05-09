from core.security import get_current_user
from db.models import Dog, User
from db.session import get_db
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.schemas.dog import MbtiResultCreate, MbtiResultResponse
from api.services.mbti_service import MbtiService

router = APIRouter()


@router.post("/", status_code=204)
def save_mbti(
    payload: MbtiResultCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dog = db.query(Dog).filter(Dog.user_id == current_user.id).first()
    if not dog:
        raise HTTPException(status_code=404, detail="반려견 정보가 없습니다")
    MbtiService.save_mbti_result(dog.id, payload.mbti_type, db)
    return


@router.get("/", response_model=MbtiResultResponse)
def get_mbti(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dog = db.query(Dog).filter(Dog.user_id == current_user.id).first()
    if not dog:
        raise HTTPException(status_code=404, detail="반려견 정보가 없습니다")
    result = MbtiService.get_mbti_result(dog.id, db)
    if not result:
        raise HTTPException(status_code=404, detail="MBTI 정보가 없습니다")
    return result
