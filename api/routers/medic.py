from typing import List

from core.security import get_current_user
from db.models import Dog, User
from db.session import get_db
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.schemas.medic import MedicationCreate, MedicationResponse
from api.services.medic_service import MedicationService

router = APIRouter


def get_dog_or_404(current_user: User, db: Session):
    dog = db.query(Dog).filter(Dog.user_id == current_user.id).first()
    if not dog:
        raise HTTPException(status_code=404, detail="반려견 정보가 없습니다")
    return dog


@router.post("/", response_model=MedicationResponse)
def create_medication(
    payload: MedicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dog = get_dog_or_404(current_user, db)
    return MedicationService.create_medication(dog.id, payload, db)


@router.get("/", response_model=List[MedicationResponse])
def list_medications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dog = get_dog_or_404(current_user, db)
    return MedicationService.list_medications(dog.id, db)


@router.delete("/{medication_id}", status_code=204)
def delete_medication(
    medication_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dog = get_dog_or_404(current_user, db)
    MedicationService.delete_medication(medication_id, dog.id, db)
