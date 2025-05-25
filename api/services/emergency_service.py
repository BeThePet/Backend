from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound

from db.models import Hospital, EmergencyGuide
from api.schemas.emergency import (
    HospitalCreate,
    HospitalUpdate,
    HospitalResponse,
    EmergencyGuideResponse,
)
from db.enums import HospitalType


class EmergencyService:

    @staticmethod
    def get_all_hospitals(db: Session, type_filter: Optional[HospitalType] = None) -> List[Hospital]:
        query = db.query(Hospital)
        if type_filter:
            query = query.filter(Hospital.type == type_filter)
        return query.all()

    @staticmethod
    def create_hospital(data: HospitalCreate, db: Session) -> Hospital:
        hospital = Hospital(**data.dict())
        db.add(hospital)
        db.commit()
        db.refresh(hospital)
        return hospital

    @staticmethod
    def update_hospital(hospital_id: int, data: HospitalUpdate, db: Session) -> Hospital:
        hospital = db.query(Hospital).filter(Hospital.id == hospital_id).first()
        if not hospital:
            raise ValueError("해당 병원을 찾을 수 없습니다.")
        for field, value in data.dict(exclude_unset=True).items():
            setattr(hospital, field, value)
        db.commit()
        db.refresh(hospital)
        return hospital

    @staticmethod
    def delete_hospital(hospital_id: int, db: Session) -> None:
        hospital = db.query(Hospital).filter(Hospital.id == hospital_id).first()
        if not hospital:
            raise ValueError("해당 병원을 찾을 수 없습니다.")
        db.delete(hospital)
        db.commit()

    @staticmethod
    def get_all_emergency_guides(db: Session) -> List[EmergencyGuide]:
        return db.query(EmergencyGuide).all()

    @staticmethod
    def get_emergency_guide_by_id(guide_id: str, db: Session) -> EmergencyGuide:
        guide = db.query(EmergencyGuide).filter(EmergencyGuide.id == guide_id).first()
        if not guide:
            raise ValueError("해당 가이드를 찾을 수 없습니다.")
        return guide