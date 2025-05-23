from datetime import date, time
from typing import Optional
from pydantic import BaseModel


class MedicationCreate(BaseModel):
    name: str
    time: time
    weekdays: str
    dosage: str
    start_date: date
    end_date: Optional[date] = None
    memo: Optional[str] = None
    alarm_enabled: bool = False

class MedicationResponse(BaseModel):
    id: int
    name: str
    time: time
    weekdays: str
    dosage: str
    start_date: date
    end_date: Optional[date]
    memo: Optional[str]
    alarm_enabled: bool

    class Config:
        from_attributes = True