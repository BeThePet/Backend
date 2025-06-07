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
    status: Optional[HealthStatus] = None  
    memo: Optional[str] = None
    # 수치형 데이터 지원 (수면, 체온 등)
    numeric_value: Optional[float] = None  # 수치값 (예: 7.5시간, 38.2°C)
    unit: Optional[str] = None  # 단위 (예: "시간", "°C")

    # 데이터 무결성 검증
    def __init__(self, **data):
        super().__init__(**data)
        # status와 numeric_value 중 최소 하나는 있어야 함
        if not self.status and not self.numeric_value:
            raise ValueError(
                "status 또는 numeric_value 중 하나는 반드시 제공해야 합니다"
            )

        # 수면/체온은 수치형 권장, 식욕/활력/배변상태는 상태형 권장
        if self.item in ["수면", "체온"] and not self.numeric_value:
            raise ValueError(
                f"{self.item}은 수치값(numeric_value)을 제공하는 것이 권장됩니다"
            )

        if self.item in ["식욕", "활력", "배변상태"] and not self.status:
            raise ValueError(f"{self.item}은 상태값(status)을 제공하는 것이 권장됩니다")


class HealthDailyResponse(BaseModel):
    id: int
    item: HealthCheckItem
    status: Optional[HealthStatus] = None  # nullable 지원
    memo: Optional[str]
    # 수치형 데이터 지원
    numeric_value: Optional[float] = None
    unit: Optional[str] = None

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
    avg_walk_distance: Optional[float]
    walk_count: int
    health_check_count: int
    total_water_ml: int
    total_food_g: int


class HealthInsightResponse(BaseModel):
    score: int  
    status: str  
    insights: List[str]  
    score_breakdown: List[str]  
    class Config:
        from_attributes = True


class ActivityStatsResponse(BaseModel):
    walk_count: int
    avg_walk_distance: float
    avg_walk_duration: float
    total_walk_distance: float
    total_walk_duration: int

    feed_count: int
    avg_feed_amount: float
    total_feed_amount: int

    water_count: int
    avg_water_amount: float
    total_water_amount: int

    health_check_count: int
    health_check_abnormal_count: int

    class Config:
        from_attributes = True


class HealthItemStatsResponse(BaseModel):
    item: str  
    count: int  
    status: str  
    normal_count: Optional[int] = None
    abnormal_count: Optional[int] = None
    abnormal_ratio: Optional[str] = None
    average_value: Optional[float] = None
    unit: Optional[str] = None
    explanation: str

    class Config:
        from_attributes = True


class ComprehensiveReportResponse(BaseModel):
    period: str  # "week", "month", "all"
    start_date: date
    end_date: date

    # 종합 건강 정보
    health_insight: HealthInsightResponse

    # 활동 통계
    activity_stats: ActivityStatsResponse

    # 건강 체크 상세 통계
    health_check_details: List[HealthItemStatsResponse]

    # 체중 정보
    current_weight: Optional[float]
    weight_change: Optional[float]
    weight_trend: str  # "up", "down", "stable"

    class Config:
        from_attributes = True
