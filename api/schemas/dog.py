from datetime import date
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class AgeGroup(str, Enum):
    junior = "주니어"
    adult = "성견"
    senior = "시니어"


class Gender(str, Enum):
    male = "남아"
    female = "여아"
    neutered = "중성화"


class DogCreate(BaseModel):
    name: str
    birthdate: date
    age_group: AgeGroup
    weight: float
    breed_id: Optional[int]  # 품종 선택-기타일 경우 null
    gender: Gender
    medication: Optional[str] = None
    allergy_ids: List[int] = []
    disease_ids: List[int] = []


class DogResponse(BaseModel):
    id: int
    name: str
    birthdate: date
    age_group: AgeGroup
    weight: float
    gender: Gender
    medication: Optional[str]
    breed_name: Optional[str]
    allergy_names: List[str]
    disease_names: List[str]

    class Config:
        from_attributes = True


class OptionItem(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class AllergyOption(BaseModel):
    category: str
    items: List[OptionItem]


class DiseaseOption(BaseModel):
    category: str
    items: List[OptionItem]


class MbtiResultCreate(BaseModel):
    mbti_type: str


class MbtiResultResponse(BaseModel):
    mbti_type: str
    created_at: datetime

    class Config:
        from_attributes = True
