from datetime import date
from typing import Optional, List
from pydantic import BaseModel

class VaccinationCreate(BaseModel):
    vaccine_id: str
    date: date
    hospital: Optional[str] = None
    memo: Optional[str] = None

class VaccinationResponse(BaseModel):
    id: int
    vaccine_id: str
    date: date
    hospital: Optional[str]
    memo: Optional[str]

    class Config:
        from_attributes = True

class VaccineTypeResponse(BaseModel):
    id: str
    name: str
    category: str
    description: Optional[str]
    period: int
    

    class Config:
        from_attributes = True