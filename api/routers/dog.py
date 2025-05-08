from typing import List

from core.security import get_current_user
from db.models import Dog, User
from db.session import get_db
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.schemas.dog import DogCreate, DogListResponse, DogResponse, DogUpdate
from api.services.dog_service import DogService

router = APIRouter()


@router.post("/", response_model=DogResponse)
def register_dog(
    dog: DogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_dog = DogService.create_dog(current_user.id, dog, db)
    return new_dog


@router.get("/", response_model=DogResponse)
def get_my_dog(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    dog = db.query(Dog).filter(Dog.user_id == current_user.id).first()
    if not dog:
        raise HTTPException(status_code=404, detail="등록된 반려견이 없습니다")
    return DogService.to_response(dog)


@router.put("/", response_model=DogResponse)
def update_my_dog(
    updated_dog: DogUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return DogService.update_dog(current_user.id, updated_dog, db)


@router.delete("/", status_code=204)
def delete_my_dog(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    DogService.delete_dog(current_user.id, db)
    return
