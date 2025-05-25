from typing import List, Optional

from db.enums import HospitalType
from db.session import get_db
from fastapi import APIRouter, Depends, HTTPException, Query
from services.emergency_service import EmergencyService
from sqlalchemy.orm import Session

from api.schemas.emergency import (
    EmergencyGuideResponse,
    EmergencyHospitalSummary,
    HospitalCreate,
    HospitalResponse,
    HospitalUpdate,
)

router = APIRouter()


@router.get("/hospitals", response_model=List[HospitalResponse])
def get_hospitals(
    type: Optional[HospitalType] = Query(None),
    db: Session = Depends(get_db),
):
    return EmergencyService.get_all_hospitals(db, type_filter=type)


@router.post("/hospitals", response_model=HospitalResponse)
def create_hospital(data: HospitalCreate, db: Session = Depends(get_db)):
    return EmergencyService.create_hospital(data, db)


@router.put("/hospitals/{hospital_id}", response_model=HospitalResponse)
def update_hospital(
    hospital_id: int, data: HospitalUpdate, db: Session = Depends(get_db)
):
    try:
        return EmergencyService.update_hospital(hospital_id, data, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/hospitals/{hospital_id}")
def delete_hospital(hospital_id: int, db: Session = Depends(get_db)):
    try:
        EmergencyService.delete_hospital(hospital_id, db)
        return {"message": "삭제되었습니다."}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/hospitals/summary", response_model=List[EmergencyHospitalSummary])
def get_emergency_hospital_summary(db: Session = Depends(get_db)):
    return EmergencyService.get_emergency_hospital_summaries(db)


@router.get("/guides", response_model=List[EmergencyGuideResponse])
def get_all_guides(db: Session = Depends(get_db)):
    return EmergencyService.get_all_emergency_guides(db)


@router.get("/guides/{guide_id}", response_model=EmergencyGuideResponse)
def get_guide(guide_id: str, db: Session = Depends(get_db)):
    try:
        return EmergencyService.get_emergency_guide_by_id(guide_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
