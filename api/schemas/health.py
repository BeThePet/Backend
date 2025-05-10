from datetime import date
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class HealthCheckItem(str, Enum):
    appetite = "식욕"
    vitality = "활력"
    hydration = "수분섭취"
    defecation = "배변상태"
    sleep = "수면"
    temperature = "체온"


class HealthDailyCreate(BaseModel):
    date: date
    item: HealthCheckItem
    is_normal: bool
    memo: Optional[str] = None


class HealthDailyResponse(BaseModel):
    id: int
    date: date
    item: HealthCheckItem
    is_normal: bool
    memo: Optional[str]

    class Config:
        from_attributes = True


class WalkRecordCreate(BaseModel):
    date: date
    distance_km: float
    duration_min: int


class WalkRecordResponse(BaseModel):
    id: int
    date: date
    distance_km: float
    duration_min: int

    class Config:
        from_attributes = True


class FoodRecordCreate(BaseModel):
    date: date
    time: str
    brand: Optional[str]
    amount_g: int


class FoodRecordResponse(BaseModel):
    id: int
    date: date
    time: str
    brand: Optional[str]
    amount_g: int

    class Config:
        from_attributes = True


class WaterRecordCreate(BaseModel):
    date: date
    amount_ml: int


class WaterRecordResponse(BaseModel):
    id: int
    date: date
    amount_ml: int

    class Config:
        from_attributes = True


class WeightRecordCreate(BaseModel):
    date: date
    weight_kg: float


class WeightRecordResponse(BaseModel):
    id: int
    date: date
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
