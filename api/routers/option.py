from db.session import get_db
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.schemas.dog import (
    AllergyCategoryResponse,
    BreedResponse,
    DiseaseCategoryResponse,
)
from api.services.option_service import OptionService

router = APIRouter(prefix="/options", tags=["Option"])


@router.get("/breeds", response_model=list[BreedResponse])
def get_breeds(db: Session = Depends(get_db)):
    return OptionService.get_breeds(db)


@router.get("/allergies", response_model=list[AllergyCategoryResponse])
def get_allergies(db: Session = Depends(get_db)):
    return OptionService.get_allergy_categories(db)


@router.get("/diseases", response_model=list[DiseaseCategoryResponse])
def get_diseases(db: Session = Depends(get_db)):
    return OptionService.get_disease_categories(db)
