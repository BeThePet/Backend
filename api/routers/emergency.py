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


# 병원 조회 (경로 파라미터 방식)
@router.get("/hospitals/all", response_model=List[HospitalResponse])
def get_all_hospitals(db: Session = Depends(get_db)):
    """전체 병원 목록 조회"""
    return EmergencyService.get_all_hospitals(db)


@router.get("/hospitals/regular", response_model=List[HospitalResponse])
def get_regular_hospitals(db: Session = Depends(get_db)):
    """일반 병원 목록 조회"""
    return EmergencyService.get_hospitals_by_type(db, HospitalType.REGULAR)


@router.get("/hospitals/emergency", response_model=List[HospitalResponse])
def get_emergency_hospitals(db: Session = Depends(get_db)):
    """응급 병원 목록 조회"""
    return EmergencyService.get_hospitals_by_type(db, HospitalType.EMERGENCY)


@router.get("/hospitals/specialist", response_model=List[HospitalResponse])
def get_specialist_hospitals(db: Session = Depends(get_db)):
    """전문 병원 목록 조회"""
    return EmergencyService.get_hospitals_by_type(db, HospitalType.SPECIALIST)


@router.get("/hospitals/summary", response_model=List[EmergencyHospitalSummary])
def get_emergency_hospital_summary(db: Session = Depends(get_db)):
    return EmergencyService.get_emergency_hospital_summaries(db)


# 병원 CRUD
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


# 응급 가이드
@router.get("/guides", response_model=List[EmergencyGuideResponse])
def get_all_guides(db: Session = Depends(get_db)):
    return EmergencyService.get_all_emergency_guides(db)


@router.get("/guides/{guide_id}", response_model=EmergencyGuideResponse)
def get_guide(guide_id: str, db: Session = Depends(get_db)):
    try:
        return EmergencyService.get_emergency_guide_by_id(guide_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
