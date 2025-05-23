from typing import List

from core.security import get_current_user
from db.models import Dog, User
from db.session import get_db
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.schemas.vaccine import (
    VaccinationCreate,
    VaccinationResponse,
    VaccineTypeResponse,
)
from api.services import vaccine_service

router = APIRouter()


def get_dog_or_404(current_user: User, db: Session):
    dog = db.query(Dog).filter(Dog.user_id == current_user.id).first()
    if not dog:
        raise HTTPException(status_code=404, detail="반려견 정보가 없습니다")
    return dog


@router.get("/types", response_model=List[VaccineTypeResponse])
def list_types(db: Session = Depends(get_db)):
    return vaccine_service.list_vaccine_types(db)


@router.post("/", response_model=VaccinationResponse)
def create_vaccine_record(
    payload: VaccinationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dog = get_dog_or_404(current_user, db)
    return vaccine_service.create_vaccination_record(dog.id, payload, db)


@router.get("/", response_model=List[VaccinationResponse])
def list_vaccine_records(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dog = get_dog_or_404(current_user, db)
    return vaccine_service.list_vaccination_records(dog.id, db)
