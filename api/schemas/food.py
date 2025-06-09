from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# === 사료 제품 관련 스키마 (조회용) ===
class FoodProductResponse(BaseModel):
    id: int
    csv_index: Optional[int] = None  # CSV 매핑용 인덱스
    product_name: Optional[str] = None
    url: Optional[str] = None
    brand: Optional[str] = None
    price: Optional[float] = None
    ingredients: Optional[str] = None
    calorie_content: Optional[str] = None

    # 영양소 성분
    protein_pct: Optional[float] = None
    fat_pct: Optional[float] = None
    fiber_pct: Optional[float] = None
    moisture_pct: Optional[float] = None
    calcium_pct: Optional[float] = None
    phosphorus_pct: Optional[float] = None
    sodium_pct: Optional[float] = None
    omega_6_pct: Optional[float] = None
    omega_3_pct: Optional[float] = None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# === 추천 결과 관련 스키마 ===
class FoodRecommendationResponse(BaseModel):
    recommendation_id: int
    request_conditions: Dict[str, Any]
    recommendations: List[Dict[str, Any]]  # DataFrame.to_dict('records') 결과
    algorithm_version: str
    confidence_score: float

    model_config = ConfigDict(from_attributes=True)


# === 사료 피드백 관련 스키마 (평점만 - 최대한 단순화) ===
class FoodFeedbackCreate(BaseModel):
    dog_id: int = Field(..., description="반려견 ID")
    food_product_id: int = Field(..., description="사료 제품 ID")
    rating: float = Field(..., ge=1.0, le=5.0, description="평점 (1.0-5.0, 0.5 단위)")


class FoodFeedbackResponse(BaseModel):
    id: int
    user_id: int
    dog_id: int
    food_product_id: int
    rating: float
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
