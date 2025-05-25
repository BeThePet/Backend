from datetime import date
from typing import List, Optional

from db.enums import HospitalType, Specialty
from pydantic import BaseModel


class EmergencyGuideResponse(BaseModel):
    id: str
    title: str
    severity: str
    symptoms: List[str]
    first_aid: List[str]
    notes: Optional[str]

    class Config:
        from_attributes = True


class HospitalBase(BaseModel):
    name: str
    phone: str
    address: Optional[str] = None
    type: HospitalType
    is_emergency: Optional[bool] = False
    hours: Optional[str] = None
    notes: Optional[str] = None
    specialties: Optional[List[Specialty]] = []


class HospitalCreate(HospitalBase):
    pass


class HospitalUpdate(HospitalBase):
    pass


class HospitalResponse(HospitalBase):
    id: int

    class Config:
        from_attributes = True
