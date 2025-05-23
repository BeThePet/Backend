from datetime import date, time
from enum import Enum
from typing import List, Optional
from db.enums import HealthStatus

from pydantic import BaseModel


class HealthCheckItem(str, Enum):
    appetite = "식욕"
    vitality = "활력"
    defecation = "배변상태"
    sleep = "수면"
    temperature = "체온"


class HealthDailyCreate(BaseModel):
    item: HealthCheckItem
    status: HealthStatus
    memo: Optional[str] = None


class HealthDailyResponse(BaseModel):
    id: int
    item: HealthCheckItem
    status: HealthStatus
    memo: Optional[str]

    class Config:
        from_attributes = True


class WalkRecordCreate(BaseModel):
    distance_km: float
    duration_min: int


class WalkRecordResponse(BaseModel):
    id: int
    distance_km: float
    duration_min: int

    class Config:
        from_attributes = True


class FoodRecordCreate(BaseModel):
    time: str
    brand: Optional[str]
    amount_g: int


class FoodRecordResponse(BaseModel):
    id: int
    time: time
    brand: Optional[str]
    amount_g: int

    class Config:
        from_attributes = True


class WaterRecordCreate(BaseModel):
    amount_ml: int


class WaterRecordResponse(BaseModel):
    id: int
    amount_ml: int

    class Config:
        from_attributes = True


class WeightRecordCreate(BaseModel):
    weight_kg: float


class WeightRecordResponse(BaseModel):
    id: int
    weight_kg: float

    class Config:
        from_attributes = True


class WeeklyReportResponse(BaseModel):
    week_start: date
    week_end: date
    current_weight: Optional[float]
    avg_walk_duration: Optional[float]
    walk_count: int
    health_check_count: int
    total_water_ml: int
    total_food_g: int
